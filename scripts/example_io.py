"""Input and output helpers for the pinned soluble 1IEP tutorial."""

import argparse
import math
import re
from pathlib import Path


def order_example_receptor(source, destination):
    lines = source.read_text().splitlines()
    atoms = [line for line in lines if line.startswith("ATOM  ")]
    if not atoms or sum(line.startswith("TER") for line in lines) != 1 or any(
        line.startswith(("HETATM", "MODEL", "CONECT")) for line in lines
    ):
        raise ValueError("Unexpected PDB layout for the pinned, single-chain receptor.")
    serials = [int(line[6:11]) for line in atoms]
    if len(set(serials)) != len(serials):
        raise ValueError("Duplicate atom serial in the example receptor.")
    ordered = sorted(atoms, key=lambda line: int(line[6:11]))
    first_atom = next(i for i, line in enumerate(lines) if line.startswith("ATOM  "))
    last_atom = max(i for i, line in enumerate(lines) if line.startswith("ATOM  "))
    if any(not line.startswith("ATOM  ") for line in lines[first_atom:last_atom + 1]):
        raise ValueError("Unexpected non-ATOM record within the pinned receptor.")
    destination.write_text("\n".join(lines[:first_atom] + ordered + lines[last_atom + 1:]) + "\n")


def read_sdf(path):
    from rdkit import Chem

    records = list(Chem.SDMolSupplier(str(path), removeHs=False))
    if not records or any(mol is None for mol in records):
        raise ValueError(f"Empty or invalid SDF: {path}")
    return records


def identity(mol):
    from rdkit import Chem

    stripped = Chem.RemoveHs(mol)
    return Chem.MolToSmiles(stripped, isomericSmiles=True), Chem.GetFormalCharge(stripped)


def select_pose(original, poses, destination):
    from rdkit import Chem

    reference, *extras = read_sdf(original)
    if extras or Chem.GetFormalCharge(reference) != 1:
        raise ValueError("The example expects one ligand record with formal charge +1.")
    docked = read_sdf(poses)
    pose = docked[0]
    if not pose.GetConformer().Is3D() or not all(
        math.isfinite(x) for xyz in pose.GetConformer().GetPositions() for x in xyz
    ):
        raise ValueError("The selected docking pose has invalid coordinates.")
    if identity(reference) != identity(pose):
        raise ValueError("The selected SDF has a different chemical identity.")
    with Chem.SDWriter(str(destination)) as writer:
        writer.write(pose)
    print(f"Selected SDF record 1 of {len(docked)}; identity and formal charge +1 match.")


def check_mol2(reference, roundtrip, tolerance=0.02):
    from rdkit import Chem
    from rdkit.Chem import rdMolAlign

    ref = Chem.RemoveHs(read_sdf(reference)[0])
    converted = Chem.RemoveHs(read_sdf(roundtrip)[0])
    if identity(ref) != identity(converted):
        raise ValueError("MOL2 changed the chemical graph, stereochemistry, or charge.")
    rmsd = rdMolAlign.CalcRMS(ref, converted, maxMatches=100000)
    if not math.isfinite(rmsd) or rmsd > tolerance:
        raise ValueError(f"MOL2 moved the pose: fixed-frame RMSD {rmsd:.4f} Å.")
    print(f"MOL2 fixed-frame heavy-atom RMSD: {rmsd:.4f} Å.")


def read_gro(path):
    lines = path.read_text().splitlines()
    count = int(lines[1])
    if count < 1 or len(lines) != count + 3:
        raise ValueError(f"Expected a nonempty one-frame GRO file: {path}")
    return lines[2:-1], lines[-1]


def header(line):
    match = re.match(r"^\s*\[\s*([a-zA-Z_]+)\s*\]", line)
    return match[1].lower() if match else None


def extract_sections(text):
    lines = text.splitlines(keepends=True)
    positions = [(i, header(line)) for i, line in enumerate(lines) if header(line)]
    return lines, positions


def mol2_xyz(filename):
    section = None
    xyz = []
    for line in filename.read_text().splitlines():
        if line.startswith("@<TRIPOS>"):
            section = line[9:]
        elif section == "ATOM" and line.strip():
            cols = line.split()
            xyz.append(tuple(float(x) / 10 for x in cols[2:5]))
    if not xyz:
        raise ValueError("The input MOL2 has no atoms.")
    return xyz


def write_index(filename, groups):
    with filename.open("x") as handle:
        for name, ids in groups.items():
            if not ids:
                raise ValueError(f"Empty index group: {name}")
            handle.write(f"[ {name} ]\n")
            for start in range(0, len(ids), 15):
                handle.write(" ".join(map(str, ids[start:start + 15])) + "\n")


def atomtypes_with_elements(type_lines, rows, pdb_atoms):
    from rdkit import Chem

    periodic = Chem.GetPeriodicTable()
    numbers = {}
    for fields, pdb in zip(rows, pdb_atoms, strict=True):
        element = pdb[76:78].strip().title()
        if not element:
            raise ValueError("ACPYPE PDB is missing a verified atom element.")
        atom_type = fields[1]
        number = periodic.GetAtomicNumber(element)
        if numbers.setdefault(atom_type, number) != number:
            raise ValueError(f"Inconsistent element assignment for {atom_type}.")
    output = ["[ atomtypes ]\n", "; name bond_type atomic_number mass charge ptype sigma epsilon\n"]
    seen = set()
    for line in type_lines[1:]:
        data, sep, comment = line.partition(";")
        columns = data.split()
        if not columns:
            continue
        name = columns[0]
        if name not in numbers or name in seen:
            raise ValueError(f"Unexpected or duplicated ACPYPE atom type: {name}.")
        seen.add(name)
        number = str(numbers[name])
        if len(columns) == 7:
            columns.insert(2, number)
        elif len(columns) != 8 or columns[2] != number:
            raise ValueError(f"Unexpected ACPYPE columns or atomic number for {name}.")
        output.append(" ".join(columns) + (" ; " + comment.strip() if sep else "") + "\n")
    if seen != numbers.keys():
        raise ValueError("An ACPYPE atom type is missing its nonbonded parameters.")
    return "".join(output) + "\n"


def assemble(work):
    protein, box = read_gro(work / "protein.gro")
    ligand, _ = read_gro(work / "LIG.acpype" / "LIG_GMX.gro")
    raw = (work / "LIG.acpype" / "LIG_GMX.itp").read_text()
    lines, positions = extract_sections(raw)
    indices = {name: i for i, name in positions}
    if "defaults" in indices or "system" in indices:
        raise ValueError("Expected a ligand ITP, not a standalone topology.")
    atomtypes = indices["atomtypes"]
    molecule = indices["moleculetype"]
    atoms = indices["atoms"]
    atom_end = next(i for i, _ in positions if i > atoms)
    rows = [line.split(";", 1)[0].split() for line in lines[atoms + 1:atom_end]]
    rows = [row for row in rows if row]
    if not (atomtypes < molecule < atoms):
        raise ValueError("Unexpected ordering of ACPYPE sections.")
    if len(rows) != len(ligand):
        raise ValueError("ACPYPE ligand coordinate and ITP counts differ.")
    if [line[10:15].strip() for line in ligand] != [row[4] for row in rows]:
        raise ValueError("ACPYPE ligand coordinate and ITP atom names differ.")
    charge = math.fsum(float(row[6]) for row in rows)
    if not math.isfinite(charge) or abs(charge - 1) > 0.01:
        raise ValueError("ACPYPE ligand charge is inconsistent with the verified +1 ligand.")

    # ACPYPE may rename repeated MOL2 atom names. Verify its numbered PDB
    # against the coordinates submitted for parameterization and its ITP/GRO.
    submitted = mol2_xyz(work / "lig_pose.mol2")
    if len(submitted) != len(ligand):
        raise ValueError("MOL2 and ACPYPE atom counts differ.")
    ac_pdb = [
        line for line in (work / "LIG.acpype" / "LIG_NEW.pdb").read_text().splitlines()
        if line.startswith(("ATOM  ", "HETATM"))
    ]
    if [line[12:16].strip() for line in ac_pdb] != [row[4] for row in rows]:
        raise ValueError("ACPYPE PDB and ITP atom names or order differ.")
    for i, (xyz, pdb, gro, fields) in enumerate(zip(submitted, ac_pdb, ligand, rows), 1):
        pdb_xyz = [float(pdb[start:start + 8]) / 10 for start in (30, 38, 46)]
        gro_xyz = [float(gro[start:start + 8]) for start in (20, 28, 36)]
        errors = [math.dist(xyz, pdb_xyz), math.dist(xyz, gro_xyz)]
        if int(fields[0]) != i or not all(math.isfinite(e) and e <= 0.002 for e in errors):
            raise ValueError(f"ACPYPE coordinate or atom-order mismatch at atom {i}.")
    heavy = [i for i, row in enumerate(rows, 1) if float(row[7]) > 2.5]
    (work / "ligand_atomtypes.itp").write_text(
        atomtypes_with_elements(lines[atomtypes:molecule], rows, ac_pdb)
    )
    restrained = "".join(lines[molecule:]).replace('#ifdef POSRES\n', '#ifdef ACPYPE_UNUSED_POSRES\n')
    (work / "ligand.itp").write_text(
        restrained + '\n#ifdef POSRES_LIG\n#include "posre_ligand.itp"\n#endif\n'
    )
    (work / "posre_ligand.itp").write_text(
        "[ position_restraints ]\n" + "".join(f"{i} 1 1000 1000 1000\n" for i in heavy)
    )

    moltype = next(
        row[0] for line in lines[molecule + 1:atoms]
        if (row := line.split(";", 1)[0].split()) and not line.startswith("#")
    )
    topology = (work / "protein.top").read_text()
    topology, n = re.subn(
        r'(^#include "[^"]+/forcefield\.itp"\s*$)',
        r'\1\n#include "ligand_atomtypes.itp"',
        topology, count=1, flags=re.M,
    )
    if n != 1:
        raise ValueError("Missing protein force-field include.")
    topology, n = re.subn(
        r'(?im)^(\s*\[\s*system\s*\])',
        r'\n#include "ligand.itp"\n\1',
        topology, count=1,
    )
    if n != 1 or not re.search(r"(?im)^\s*\[\s*molecules\s*\]", topology):
        raise ValueError("Missing [ system ] or [ molecules ].")
    (work / "topol.top").write_text(topology.rstrip() + f"\n{moltype}  1\n")
    (work / "complex.gro").write_text(
        "1IEP protein–ligand complex\n" + str(len(protein) + len(ligand)) + "\n"
        + "\n".join(protein + ligand) + "\n" + box + "\n"
    )
    write_index(work / "analysis.ndx", {
        "System": list(range(1, len(protein) + len(ligand) + 1)),
        "Protein": list(range(1, len(protein) + 1)),
        "Ligand": list(range(len(protein) + 1, len(protein) + len(ligand) + 1)),
        "Backbone": [i for i, row in enumerate(protein, 1) if row[10:15].strip() in {"N", "CA", "C"}],
        "Ligand_heavy": [len(protein) + i for i in heavy],
        "Complex": list(range(1, len(protein) + len(ligand) + 1)),
    })
    print(f"Assembled {len(protein)} protein atoms and {len(ligand)} ligand atoms.")


def index_solvated(work):
    coordinates, _ = read_gro(work / "solv_ions.gro")
    text = (work / "analysis.ndx").read_text()
    text = re.sub(r'(?s)^\[ System \].*?(?=\[ Protein \])', '', text)
    target = work / "analysis_full.ndx"
    write_index(target, {"System": list(range(1, len(coordinates) + 1))})
    with target.open("a") as handle:
        handle.write(text)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    pose_parser = sub.add_parser("pose")
    for arg in ("original", "poses", "destination"):
        pose_parser.add_argument(arg, type=Path)
    mol2_parser = sub.add_parser("mol2")
    mol2_parser.add_argument("reference", type=Path)
    mol2_parser.add_argument("roundtrip", type=Path)
    order_parser = sub.add_parser("order-example")
    order_parser.add_argument("source", type=Path)
    order_parser.add_argument("destination", type=Path)
    for command in ("assemble", "index"):
        sub.add_parser(command).add_argument("work", type=Path)
    options = parser.parse_args()
    if options.action == "pose":
        select_pose(options.original, options.poses, options.destination)
    elif options.action == "mol2":
        check_mol2(options.reference, options.roundtrip)
    elif options.action == "order-example":
        order_example_receptor(options.source, options.destination)
    elif options.action == "assemble":
        assemble(options.work)
    else:
        index_solvated(options.work)
