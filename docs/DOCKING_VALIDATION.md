# Multi-stage docking and validation

**English** · [简体中文](DOCKING_VALIDATION.zh-CN.md)

[Repository home](../README.md#contents)

[Main tutorial](../README.md#contents) · [Reference redocking](ENVIRONMENT.md#benchmark) · [Troubleshooting](TROUBLESHOOTING.md#troubleshooting-contents)

This guide covers noncovalent docking with an unknown pocket, a multichain receptor, or multiple ligand starting conformers. The workflow proceeds through receptor repair, conformer generation, overlapping-box screening, local refinement, pose validation, and interaction review. The commands use generic filenames and illustrative settings. Qualify the settings with a public co-crystal control and record them with the workflow version.<sup>[1](#ref-1)</sup>

1. [Triage by failure stage](#validation-triage)
2. [Receptor repair and templates](#receptor-repair)
3. [Ligand conformers and identity](#conformer-preparation)
4. [Tiled search and run validation](#tiled-search)
5. [Local search and reproducibility](#pose-validation)
6. [Subunit symmetry and interaction review](#interaction-review)
7. [Archiving, tools, and references](#validation-references)

<a name="validation-triage"></a>

## 1. Triage by failure stage

| Symptom | Likely cause | Corrective action and verification |
| --- | --- | --- |
| Import fails in one shell | The shell resolves a different Python interpreter | Resolve the interpreter and check versions in the shell that runs the task. |
| Template or valence error | An observed residue lacks side-chain atoms, rebuilt atoms overlap, or a retained component lacks template atoms. | Diagnose the exact residue and rerun parameterization. [Receptor repair and templates](#receptor-repair) |
| Warning reaches the native error stream | A native tool writes its warning to stderr, whose handling varies by PowerShell version. | Redirect inside WSL, then check the exit status and fresh outputs. |
| Multiple geometries for a ligand with no rotatable bonds | Ring puckering can vary, and independent input files can represent one conformer family. | Verify identity and align low-energy conformers for deduplication. [Ligand conformer preparation](#conformer-preparation) |
| Duplicate or truncated results on resume | File presence was used as the completion criterion. | Validate the manifest, pose blocks, and hashes. [Tiled search and job validation](#tiled-search) |
| A strong local score accompanies pocket migration | The local search box also admits a neighboring pocket. | Check position and contacts jointly and retain migrated poses for review. [Local search and pose validation](#pose-validation) |
| Repeated subunit poses or ambiguous contact labels | Symmetry can duplicate sites, and proximity and chemical interactions use distinct criteria. | Check receptor-based symmetry and verify donor–acceptor geometry separately. [Interaction review](#interaction-review) |

Run this preflight in the same shell as the analysis. Change the package list to match the active stage.

**Environment:** `docking-gromacs`. **Expected files or evidence:** terminal output or the paths named below. For planning, use the per-stage budget in the quickstart.

```bash
python -c 'import sys; print(sys.executable)'
python -c 'from importlib.metadata import version; print({p: version(p) for p in ("pdbfixer", "openmm")})'
```

<a name="receptor-repair"></a>

## 2. Receptor repair and templates

**Define the receptor composition.** Document the source model, assembly, interfaces, and gaps near the target region. Record the identity, completeness, disposition, and rationale for each hetero component. Archive the coordinates of the reference ligand before stripping it for redocking. Essential cofactors and nonstandard chemistry require a system-specific model. An experimental surrogate construct is a separate receptor model with its own scope. [Complex-system preparation](TROUBLESHOOTING.md#complex-systems)

**Separate missing atoms from missing segments.** Resolve alternate locations coherently per residue. Retain shared atoms with blank altloc identifiers and record the occupancy-based selection rule. The PDBFixer example repairs missing atoms within observed residues. If an unresolved segment borders the pocket or interface, review alternative structures or an independently justified modeling procedure. Compare source and repaired files with residue and atom identifiers, and verify chain breaks, termini, and disulfides.<sup>[2](#ref-2)</sup> [PDBFixer manual](https://github.com/openmm/pdbfixer/blob/master/Manual.html)

Save as `repair_atoms.py`. The input is a chain-selected, altloc-resolved protein PDB. Reintroduce independently reviewed retained components using verified identifiers, connectivity, and the same coordinate frame.

```python
from openmm.app import PDBFile
from pdbfixer import PDBFixer

model = PDBFixer(filename="protein_input.pdb")
model.findMissingResidues()
print("Unresolved residue blocks:", len(model.missingResidues))
model.missingResidues.clear()

model.findMissingAtoms()
print("Missing atoms in observed residues:", sum(map(len, model.missingAtoms.values())))
model.missingTerminals.clear()
model.addMissingAtoms()

with open("protein_repaired.pdb", "x") as handle:
    PDBFile.writeFile(model.topology, model.positions, handle, keepIds=True)

check = PDBFixer(filename="protein_repaired.pdb")
check.findMissingResidues()
check.missingResidues.clear()
check.findMissingAtoms()
if check.missingAtoms:
    for residue, atoms in check.missingAtoms.items():
        print(residue.chain.id, residue.id, residue.name, [atom.name for atom in atoms])
    raise SystemExit("Internal atom repair is incomplete.")
```

**Diagnose persistent template failures.** Locate the chain and residue in stderr and inspect its heavy-atom inventory, connectivity, and modifications. For clashes involving rebuilt side chains, use the open-source PyMOL wizard to sample rotamers of the same residue type. Check neighboring atoms, transfer only the permitted coordinates by atom name, and verify original atoms and backbone positions. If only newly added atoms are moved, verify side-chain geometry after the coordinate transfer. Document removal of an incomplete nonessential component. For essential components, validate a complete model or template and check the final PDBQT inventory. [Meeko receptor preparation](https://meeko.readthedocs.io/en/develop/rec_cli_options.html) · [PyMOL rotamer implementation](https://github.com/schrodinger/pymol-open-source/blob/master/modules/pymol/wizard/mutagenesis.py)

Run in a fresh working directory in Linux or WSL. Use the reviewed receptor coordinates and archive the preparation JSON, processed PDB, PDBQT, and both logs.

**Environment:** `Bash`. **Expected files or evidence:** `receptor.pdbqt`, `receptor.pdb`. For planning, use the per-stage budget in the quickstart.

```bash
if mk_prepare_receptor.py --read_pdb receptor_qc.pdb -o receptor -p -j --write_pdb receptor.pdb  > prep.stdout.log 2> prep.stderr.log; then
    test -s receptor.pdbqt && test -s receptor.json && test -s receptor.pdb
else
    status=$?
    tail -n 30 prep.stderr.log >&2
    exit "$status"
fi
```

When launching from PowerShell, redirect inside WSL. Confirm the WSL working directory and the active environment first. Review warnings on templates and retained components after checking the exit code and artifacts. [Microsoft PowerShell native-command guidance](https://learn.microsoft.com/en-us/powershell/scripting/learn/shell/running-commands)

**Environment:** `PowerShell`. **Expected files or evidence:** terminal output or the paths named below. For planning, use the per-stage budget in the quickstart.

```powershell
wsl.exe -- pwd
wsl.exe -- bash -lc 'exec mk_prepare_receptor.py --read_pdb receptor_qc.pdb -o receptor -p -j --write_pdb receptor.pdb > prep.stdout.log 2> prep.stderr.log'
$status = $LASTEXITCODE
if ($status -ne 0) { throw "Receptor preparation exited with code $status. Read prep.stderr.log." }
foreach ($file in 'receptor.pdbqt', 'receptor.json', 'receptor.pdb') {
    if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { throw "Missing $file" }
    if ((Get-Item -LiteralPath $file).Length -eq 0) { throw "Empty $file" }
}
```

<a name="conformer-preparation"></a>

## 3. Ligand conformers and identity

First review salts, tautomers, protonation, formal charge, and stereochemistry. MolScrub can enumerate microstates. Generate conformers within each selected microstate. Cyclic ligands can have multiple geometries with few rotatable bonds. Resolve undefined stereochemistry and review unsupported MMFF chemistry before proceeding.<sup>[3](#ref-3),[4](#ref-4)</sup> [MolScrub](https://github.com/forlilab/molscrub) · [RDKit conformer-generation guide](https://www.rdkit.org/docs/RDKit_Book.html#conformer-generation)

Save as `sample_conformers.py` and use a single, chemically defined SDF record. Filter by MMFF energy within the same microstate and deduplicate with aligned heavy-atom RMSD. For production use multiple embedding seeds and archive convergence and family membership.<sup>[5](#ref-5)</sup>

```python
from math import isfinite
from pathlib import Path
from rdkit import Chem
from rdkit.Chem import AllChem, rdMolAlign

records = list(Chem.SDMolSupplier("ligand.sdf"))
if len(records) != 1 or records[0] is None:
    raise SystemExit("Expected one readable, chemically defined SDF record.")
ligand = Chem.AddHs(records[0])
ligand.RemoveAllConformers()
if not AllChem.MMFFHasAllMoleculeParams(ligand):
    raise SystemExit("Missing MMFF parameters. Choose a validated alternative.")

embed = AllChem.ETKDGv3()
embed.randomSeed = 41
embed.useSmallRingTorsions = True
embed.enforceChirality = True
embed.pruneRmsThresh = -1.0
ids = list(AllChem.EmbedMultipleConfs(ligand, numConfs=24, params=embed))
if not ids:
    raise SystemExit("Conformer embedding failed.")

optimized = AllChem.MMFFOptimizeMoleculeConfs(ligand, mmffVariant="MMFF94s", maxIters=1000)
ranked = sorted(
    (energy, cid)
    for cid, (status, energy) in zip(ids, optimized)
    if status == 0 and isfinite(energy)
)
if not ranked:
    raise SystemExit("No conformer reached MMFF convergence.")

heavy = Chem.RemoveHs(ligand)
selected = []
for energy, cid in ranked:
    if energy - ranked[0][0] > 4.0:
        break
    if all(
        rdMolAlign.GetBestRMS(Chem.Mol(heavy), heavy, prbId=cid, refId=ref, maxMatches=100000) >= 0.35
        for ref in selected
    ):
        selected.append(cid)

folder = Path("conformers")
folder.mkdir()
for index, cid in enumerate(selected, 1):
    with Chem.SDWriter(str(folder / f"conformer_{index:02d}.sdf")) as out:
        out.write(ligand, confId=cid)
print(f"Converged {len(ranked)}/{len(ids)}; retained {len(selected)} conformer families")
```

Meeko takes a 3D ligand structure. Preserve the chemical mapping metadata, and validate the molecular graph, stereochemistry, formal charge, and mapped heavy-atom coordinates after export. Record PDBQT partial-charge checks separately from SDF formal charge. Pool equivalent conformers even when they came from different inputs or embedding seeds.<sup>[6](#ref-6)</sup> [Meeko ligand and pose transfer](DOCKING.md#pose-handoff) · [Meeko export documentation](https://meeko.readthedocs.io/en/develop/export_usage.html)

**Environment:** `Bash`. **Expected files or evidence:** `ligand.pdbqt`. For planning, use the per-stage budget in the quickstart.

```bash
mk_prepare_ligand.py -i conformers/conformer_01.sdf -o ligand.pdbqt
```

<a name="tiled-search"></a>

## 4. Tiled search and run validation

### 4.1 Construct and verify overlapping boxes

Split the target heavy-atom bounds into overlapping boxes. The scoring receptor may retain documented partner chains for interface context. Report box-generation atoms and scoring components separately. The script verifies coverage of selected modeled atoms after empty boxes are dropped. Use a public control and repeated searches to assess sampling.<sup>[7](#ref-7),[8](#ref-8)</sup> [Vina search-space guidance](https://autodock-vina.readthedocs.io/en/latest/faq.html)

Save as `build_boxes.py`. Use PDB `ATOM` records with valid element fields and the same coordinate frame as the scoring receptor.

```python
from itertools import product
from math import ceil
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree

edge, stride, padding = 28.0, 18.0, 3.0  # Angstrom, illustrative
points = []
for line in Path("target_atoms.pdb").read_text().splitlines():
    if line.startswith("ATOM  "):
        element = line[76:78].strip().upper()
        if not element:
            raise SystemExit("Missing element field in target_atoms.pdb.")
        if element not in {"H", "D"}:
            points.append([float(line[i:i + 8]) for i in (30, 38, 46)])
xyz = np.asarray(points)
if xyz.size == 0 or not np.isfinite(xyz).all():
    raise SystemExit("No valid finite heavy-atom coordinates.")

lower, upper = xyz.min(axis=0) - padding, xyz.max(axis=0) + padding
axes = []
for lo, hi in zip(lower, upper):
    span = hi - lo
    count = max(1, ceil((span - edge) / stride) + 1)
    centers = [(lo + hi) / 2] if count == 1 else np.linspace(lo + edge / 2, hi - edge / 2, count)
    axes.append(centers)

candidates = np.round(np.asarray(list(product(*axes))), 4)
within = cKDTree(xyz).query_ball_point(candidates, r=edge / 2, p=np.inf, return_length=True)
centers = candidates[within > 0]
if len(centers) == 0:
    raise SystemExit("No nonempty box.")
distance, _ = cKDTree(centers).query(xyz, p=np.inf)
if np.any(distance > edge / 2):
    raise SystemExit("Uncovered modeled atoms. Review grid spacing and rounding.")

folder = Path("boxes")
folder.mkdir()
for index, center in enumerate(centers, 1):
    with (folder / f"box_{index:04d}.txt").open("x") as out:
        for axis, value in zip("xyz", center):
            out.write(f"center_{axis} = {value:.4f}\nsize_{axis} = {edge:.4f}\n")
print(f"Covered {len(xyz)} modeled heavy atoms with {len(centers)} boxes")
```

### 4.2 Validate outputs and provenance before resuming

Key each task by receptor, ligand input, box, scoring function, engine version, arguments, and seed. Record input hashes, exit status, and validated pose count. Promote temporary output only after validation. Reuse earlier outputs after matching their input and configuration fingerprints. `num_modes` sets an upper limit on returned poses. [Vina manual](https://vina.scripps.edu/manual/)

Save as `validate_poses.py`. This check expects Vina ligand-only PDBQT from rigid-receptor jobs and the expected heavy-atom count. Flexible-receptor or other PDBQT variants need an appropriate parser.

```python
from math import isfinite
from pathlib import Path
import sys

expected = int(sys.argv[2])
if expected < 1:
    raise SystemExit("Expected a positive heavy-atom count.")

models = set()
active = False
for line in Path(sys.argv[1]).read_text().splitlines():
    if line.startswith("MODEL"):
        fields = line.split()
        if active or len(fields) != 2 or fields[1] in models:
            raise SystemExit("Nested, malformed or duplicate MODEL record.")
        model = fields[1]
        active, score, heavy = True, None, 0
    elif line.startswith("ENDMDL"):
        if not active or score is None or heavy != expected:
            raise SystemExit("Unmatched ENDMDL, missing score or unexpected heavy-atom count.")
        models.add(model)
        active = False
    elif line.startswith("REMARK VINA RESULT:"):
        if not active or score is not None:
            raise SystemExit("Unexpected or duplicate Vina score.")
        score = float(line.split()[3])
        if not isfinite(score):
            raise SystemExit("Nonfinite Vina score.")
    elif line.startswith(("ATOM  ", "HETATM")):
        atom_type = line[77:].strip().upper()
        if not active or not atom_type:
            raise SystemExit("Atom outside MODEL or missing AutoDock type.")
        coords = [float(line[i:i + 8]) for i in (30, 38, 46)]
        if not all(map(isfinite, coords)):
            raise SystemExit("Nonfinite pose coordinates.")
        heavy += atom_type not in {"H", "HD", "HS", "D"}

if active or not models:
    raise SystemExit("Output contains no complete set of poses.")
print(f"Validated {len(models)} complete poses")
```

The example runs one screening task. Use independent task directories and explicit inputs for each box, starting conformer, and seed. Verify the ligand chemistry and atom mapping before passing the result to refinement.

**Environment:** `docking-gromacs`. **Expected files or evidence:** `poses.partial.pdbqt`. For planning, use the per-stage budget in the quickstart.

```bash
set -eu
expected_heavy=$(python -c 'from rdkit import Chem; m=Chem.SDMolSupplier("conformers/conformer_01.sdf")[0]; print(m.GetNumHeavyAtoms())')
cp boxes/box_0001.txt box.txt
vina --version > engine-version.txt
sha256sum receptor.pdbqt ligand.pdbqt box.txt conformers/conformer_01.sdf > inputs.sha256
command=(vina --receptor receptor.pdbqt --ligand ligand.pdbqt --config box.txt
    --scoring vina --exhaustiveness 16 --num_modes 12 --energy_range 4
    --seed 41 --cpu 2 --out poses.partial.pdbqt)
printf '%q ' "${command[@]}" > invocation.txt
printf '\n' >> invocation.txt
"${command[@]}" > vina.stdout.log 2> vina.stderr.log
python validate_poses.py poses.partial.pdbqt "$expected_heavy"
mv poses.partial.pdbqt poses.pdbqt
sha256sum poses.pdbqt > poses.sha256
```

<a name="pose-validation"></a>

## 5. Local search and reproducibility

**Define pockets before comparing scores.** Review all valid screening poses with target contacts. Deduplicate across overlapping boxes using geometric centers and residue-contact sets. Include chain, residue number, insertion code, and residue name in each key. A reproducible option is to sort by score and stable job identifiers, choose fixed anchors, and assign subsequent poses only when they satisfy both proximity and contact-overlap criteria. Shortlist pockets per starting conformer, then combine the shortlists.

**Size the local box from all reference heavy atoms.** Use the midpoint of the coordinate bounds and add a margin on both sides of the largest span. Review reference poses that lie near the box faces or span distinct sites. Repeat the local searches with recorded seeds under a shared box and scoring protocol. Report screening and refinement scores with their respective summary definitions.

**Validate refinement poses independently.** After SDF recovery and chemical/atom-map verification, audit position, residue contacts, severe overlap, and box geometry. The function below illustrates per-pose classification. Build `refs` from the reference centers and residue-contact sets for the same pocket. Use the full scoring receptor to test severe overlap.

```python
import numpy as np
from scipy.spatial import cKDTree

def local_box(reference_xyz, margin=5.0):
    points = np.vstack(reference_xyz)
    lower, upper = points.min(axis=0), points.max(axis=0)
    center = (upper + lower) / 2
    edge = max(22.0, float(np.ceil((upper - lower).max() + 2 * margin)))
    if edge > 30.0:
        raise ValueError("Review the pocket and reference poses before enlarging the box.")
    return center, edge

def jaccard(left, right):
    union = left | right
    return len(left & right) / len(union) if union else 0.0

def review_pose(pose, protein_heavy, residue_keys, target_residues, receptor_heavy, refs, box):
    center, edge = box
    hits = cKDTree(protein_heavy).query_ball_point(pose, r=4.0)
    contacts = {residue_keys[i] for indices in hits for i in indices}
    centroid = pose.mean(axis=0)
    if not refs:
        raise ValueError("At least one pocket reference is required.")
    comparisons = [(float(np.linalg.norm(centroid - c)), jaccard(contacts, r)) for c, r in refs]
    nearest = float(cKDTree(receptor_heavy).query(pose)[0].min())
    margin = float((edge / 2 - np.abs(pose - center)).min())

    flags = []
    if not contacts & target_residues:
        flags.append("NO_TARGET_CONTACT")
    if not any(distance <= 4.5 and overlap >= 0.30 for distance, overlap in comparisons):
        flags.append("POCKET_MIGRATION")
    if nearest < 1.6:
        flags.append("SEVERE_CLASH")
    if margin < -0.01:
        flags.append("OUTSIDE_BOX")
    return {"flags": flags, "min_distance_A": nearest, "box_margin_A": margin, "references": comparisons}
```

Archive migrated poses for separate review. A pose can trigger multiple flags, so report the number of affected poses and the count per reason. The box tolerance handles numerical precision, and the short-distance threshold screens for obvious overlaps.

### 5.1 Cluster in the receptor frame and summarize seeds

Use `GetBestRMS` for aligned, free-conformer deduplication. For docked poses in a common receptor frame, `CalcRMS` accounts for ligand atom symmetry without fitting away placement or orientation. Declare the within-pocket clustering threshold before inspection. A complete-link constraint requires a new member to be within the threshold of every current cluster member. Count at most one pose per seed and starting conformer in each cluster. Report seed hits, median score, score range, and maximum pairwise RMSD. A medoid is an observed pose with the smallest sum of distances to the other seed representatives. [RDKit alignment API](https://www.rdkit.org/docs/source/rdkit.Chem.rdMolAlign.html)

```python
from rdkit import Chem
from rdkit.Chem import rdMolAlign

def fixed_frame_rmsd(probe, reference):
    left, right = Chem.RemoveHs(probe), Chem.RemoveHs(reference)
    if Chem.MolToSmiles(left, isomericSmiles=True) != Chem.MolToSmiles(right, isomericSmiles=True):
        raise ValueError("The selected poses represent different chemical graphs or stereoisomers.")
    return rdMolAlign.CalcRMS(left, right, maxMatches=100000)
```

For a co-crystal control, report the top-ranked pose, the closest sampled pose to the experimental ligand, and the rank of that closest pose. This distinguishes failure to sample the reference geometry from failure to rank it first. Report seed reproducibility alongside the experimental control and model scope. [Public redocking benchmark](ENVIRONMENT.md#benchmark)

<a name="interaction-review"></a>

## 6. Subunit symmetry and interaction review

**Compare symmetry-related poses using a receptor-derived transformation.** Match homologous Cα atoms in equivalent structural regions. Apply one proper Kabsch rotation and translation to both the moving receptor and its ligand. For interface poses, verify the participating partner chains under the same mapping. Report matched atoms, receptor alignment RMSD, transformed ligand RMSD, and contact equivalence.<sup>[9](#ref-9)</sup> [Kabsch 1976](https://doi.org/10.1107/S0567739476001873)

Pass the matched receptor coordinates in the same order. The ligand coordinates move with the receptor. Use the atom mapping or symmetry-corrected RMSD from Section 5 for the transformed ligand.

```python
import numpy as np

def transfer_receptor_frame(moving_ca, fixed_ca, ligand_xyz):
    if moving_ca.shape != fixed_ca.shape or len(moving_ca) < 3:
        raise ValueError("Matching C-alpha coordinate sets are required.")
    moving_origin = moving_ca.mean(axis=0)
    fixed_origin = fixed_ca.mean(axis=0)
    left, right = moving_ca - moving_origin, fixed_ca - fixed_origin
    if min(np.linalg.matrix_rank(left), np.linalg.matrix_rank(right)) < 2:
        raise ValueError("The matched C-alpha atoms must be non-collinear.")
    u, _, vt = np.linalg.svd(left.T @ right)
    if np.linalg.det(u @ vt) < 0:
        u[:, -1] *= -1
    rotation = u @ vt
    receptor_rmsd = float(np.sqrt(np.mean(np.sum((left @ rotation - right) ** 2, axis=1))))
    transformed_ligand = (ligand_xyz - moving_origin) @ rotation + fixed_origin
    return receptor_rmsd, transformed_ligand
```

**Build the complex from the actual scoring model.** Recover the chosen pose to SDF and verify mapped heavy-atom coordinates against its source mode. Compare the scoring PDBQT and complex PDB by atom identity, coordinates, and component inventory. A one-way nearest-neighbor check serves as a geometric preflight. Retain verified connectivity and assign an unambiguous ligand residue identifier in the complex.

**Environment:** `docking-gromacs`. **Expected files or evidence:** `selected_pose.sdf`. For planning, use the per-stage budget in the quickstart.

```bash
# selected_pose.pdbqt is one audited MODEL/ENDMDL block with its Meeko mapping.
mk_export.py selected_pose.pdbqt -s selected_pose.sdf
# complex.pdb contains the matching receptor and the audited pose.
plip -f complex.pdb -o interactions -x -t --maxthreads 1
```

**Select the intended ligand in PLIP reports.** A report may contain independent sites for cofactors or lipids. Select the XML site by residue name, chain, and residue number, then cross-check atom indices against identities and coordinates. Review donor/acceptor identity, protonation, D···A and H···A distances, and the D–H···A angle for each putative hydrogen bond. Flag questionable assignments. Distinguish proximity, putative hydrogen bonds, and ring-centroid distances in figures. Archive the PyMOL session and the measurement table.<sup>[10](#ref-10),[11](#ref-11)</sup> [PLIP CLI and source](https://github.com/pharmai/plip) · [Publication figures](ANALYSIS.md#publication-figures)

<a name="validation-references"></a>

## 7. Archiving, tools, and references

| Stage | Minimum record |
| --- | --- |
| Input and preparation | Source versions, chain and component inventory, microstate, repair changes, preparation logs, and versions |
| Screening and refinement | Box centers and dimensions in Å, coverage report, arguments and seeds, file hashes, status, and pose count |
| Pose validation and interpretation | Source pose ID, chemistry map, rejection reasons, reference pocket, seed support, selected pose, raw XML, and review table |

### Tools

| Tool | Role | Documentation and source |
| --- | --- | --- |
| AutoDock Vina | Screening and local docking | [Manual](https://autodock-vina.readthedocs.io/) · [GitHub](https://github.com/ccsb-scripps/AutoDock-Vina) |
| PDBFixer / OpenMM | Repair observed residues and write coordinates | [PDBFixer manual](https://github.com/openmm/pdbfixer/blob/master/Manual.html) · [OpenMM](https://github.com/openmm/openmm) |
| PyMOL Open Source | Rotamer inspection and molecular views | [PyMOL](https://pymol.org/) · [Open-source repository](https://github.com/schrodinger/pymol-open-source) |
| MolScrub / RDKit | Microstates, conformers, and RMSD | [MolScrub](https://github.com/forlilab/molscrub) · [RDKit](https://github.com/rdkit/rdkit) · [RDKit documentation](https://www.rdkit.org/docs/) |
| Meeko | Preparation and pose export | [Documentation](https://meeko.readthedocs.io/) · [GitHub](https://github.com/forlilab/Meeko) |
| NumPy / SciPy | Coordinate arrays and spatial queries | [NumPy](https://numpy.org/doc/stable/) · [SciPy cKDTree](https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.cKDTree.html) |
| PLIP | Interaction annotation and review | [Open-source repository and CLI](https://github.com/pharmai/plip) |

### References

1. <a name="ref-1"></a> Martis EAF, Téletchéa S. Ten quick tips to perform meaningful and reproducible molecular docking calculations. *PLoS Comput Biol.* 2025. [DOI](https://doi.org/10.1371/journal.pcbi.1013030)
2. <a name="ref-2"></a> Eastman P, et al. OpenMM 7: Rapid development of high performance algorithms for molecular dynamics. *PLoS Comput Biol.* 2017. [DOI](https://doi.org/10.1371/journal.pcbi.1005659)
3. <a name="ref-3"></a> Riniker S, Landrum GA. Better Informed Distance Geometry: Using What We Know To Improve Conformation Generation. *J Chem Inf Model.* 2015. [DOI](https://doi.org/10.1021/acs.jcim.5b00654)
4. <a name="ref-4"></a> Wang S, Witek J, Landrum GA, Riniker S. Improving Conformer Generation for Small Rings and Macrocycles Based on Distance Geometry and Experimental Torsional-Angle Preferences. *J Chem Inf Model.* 2020. [DOI](https://doi.org/10.1021/acs.jcim.0c00025)
5. <a name="ref-5"></a> Halgren TA. MMFF VI. MMFF94s option for energy minimization studies. *J Comput Chem.* 1999. [PubMed](https://pubmed.ncbi.nlm.nih.gov/34376030/)
6. <a name="ref-6"></a> Santos-Martins D, et al. Meeko: Molecule Parametrization and Software Interoperability for Docking and Beyond. *J Chem Inf Model.* 2025. [DOI](https://doi.org/10.1021/acs.jcim.5c02271)
7. <a name="ref-7"></a> Trott O, Olson AJ. AutoDock Vina: improving the speed and accuracy of docking with a new scoring function, efficient optimization, and multithreading. *J Comput Chem.* 2010. [DOI](https://doi.org/10.1002/jcc.21334)
8. <a name="ref-8"></a> Eberhardt J, Santos-Martins D, Tillack AF, Forli S. AutoDock Vina 1.2.0: New Docking Methods, Expanded Force Field, and Python Bindings. *J Chem Inf Model.* 2021. [DOI](https://doi.org/10.1021/acs.jcim.1c00203)
9. <a name="ref-9"></a> Kabsch W. A solution for the best rotation to relate two sets of vectors. *Acta Crystallogr A.* 1976. [DOI](https://doi.org/10.1107/S0567739476001873)
10. <a name="ref-10"></a> Salentin S, et al. PLIP: fully automated protein–ligand interaction profiler. *Nucleic Acids Res.* 2015. [DOI](https://doi.org/10.1093/nar/gkv315)
11. <a name="ref-11"></a> Schake P, et al. PLIP 2025: introducing protein–protein interactions to the protein–ligand interaction profiler. *Nucleic Acids Res.* 2025. [DOI](https://doi.org/10.1093/nar/gkaf361)

We acknowledge the upstream developers and data maintainers. For broader software and force-field citations and scope, see the [main tutorial references](REFERENCES.md#references).
