# Force fields and system preparation

**English** · [简体中文](SYSTEM_SETUP.zh-CN.md)

Languages synchronized 2026-11-28. [Verified workflow commit](https://github.com/LuciferBioLab/docking-gromacs-tutorial/commit/d139618900e79f0dc186d3bb64fbe5be4cc25914).

[Repository home](../README.md#contents)

<a name="topology"></a>

## 06. Force-field selection and ligand parameterization

- **Input** Validated ligand and force-field selection
- **Outputs** ligand GRO/ITP
- **If a step fails** review parameter and charge failures

| Route | Protein force field | Ligand force field and charges | Water and nonbonded settings |
| --- | --- | --- | --- |
| A · AMBER | AMBER99SB-ILDN | GAFF2 and AM1-BCC via AmberTools and ACPYPE | TIP3P and ions from the AMBER port, PME, example 1.0 nm cutoff |
| B · CHARMM | CHARMM36m in the MacKerell Lab GROMACS port | Version-matched CGenFF types, charges, and bonded parameters | CHARMM TIP3P and matching ions, PME, LJ force switch over 1.0–1.2 nm for the cutoff port |

Route A provides the baseline for the soluble protein–ligand systems covered here. Select route B when a CHARMM36m protocol is justified and suitable CGenFF parameters are available. To compare the force-field families, start from the same ligand microstate and pose, apply each family's solvent, ion, and nonbonded settings, and equilibrate each system independently. [Amber manuals](https://ambermd.org/Manuals.php) · [GROMACS force-field notes](https://manual.gromacs.org/2026.3/user-guide/force-fields.html) · [MacKerell force-field ports](https://mackerell.umaryland.edu/charmm_ff.shtml)

### Route A · GAFF2 + AM1-BCC ligand

Use Open Babel for format conversion while preserving the existing 3D geometry. The example's `-n 0` assumes a verified neutral ligand. Set `-n -1`, `-n 1`, or another integer according to the selected chemical state's net charge. [AmberTools](https://ambermd.org/AmberTools.php) · [ACPYPE quick start](https://acpype.readthedocs.io/en/latest/)

**Environment:** `ligandtools`. **Expected files or evidence:** terminal output or the paths named below. For planning, use the per-stage budget in the quickstart.

```bash
conda activate ligandtools
obabel lig_pose.sdf -O lig_pose.mol2
obabel lig_pose.mol2 -O lig_pose_roundtrip.sdf
obabel lig_pose.sdf -ocan
obabel lig_pose_roundtrip.sdf -ocan
obrms lig_pose.sdf lig_pose_roundtrip.sdf
```

Compare molecular connectivity, net charge, and stereochemistry across the SDF round trip. Check that heavy-atom RMSD in the original coordinate frame is within the precision of the file format. Here, use `obrms` for geometry only. Use ACPYPE after the chemistry and geometry checks pass.

**Environment:** `docking-gromacs`. **Expected files or evidence:** terminal output or the paths named below. For planning, use the per-stage budget in the quickstart.

```bash
acpype -i lig_pose.mol2 -b LIG -a gaff2 -c bcc -n 0

ls -lh LIG.acpype
cp LIG.acpype/LIG_GMX.gro ligand.gro
cp LIG.acpype/LIG_GMX.itp ligand.itp
```

ACPYPE invokes AmberTools for parameterization. `antechamber` assigns GAFF2 atom types, `sqm` participates in AM1-BCC charge calculation, `parmchk2` identifies and supplies missing parameter terms, and `tleap` builds the Amber topology. ACPYPE exports GROMACS-compatible coordinates and topology.<sup>[11](REFERENCES.md#ref-11),[12](REFERENCES.md#ref-12),[13](REFERENCES.md#ref-13),[14](REFERENCES.md#ref-14)</sup> [Amber manuals](https://ambermd.org/Manuals.php) · [ACPYPE source](https://github.com/alanwilter/acpype)

Use the filenames produced by your ACPYPE version. Inspect the Antechamber, SQM, and parmchk2 logs, then review atom types and parameter terms. Verify the partial-charge sum, atom order, names, and masses in `[ atoms ]`. Compare the mapped heavy atoms in `ligand.gro` and the docking SDF after accounting for Å-to-nm conversion and file precision. Resolve discrepancies before assembly.

### Route B · CGenFF ligand

**Choose one compatible parameter set.** Treat route B as a separate replicate directory. Use the CHARMM36m protein definitions from the selected GROMACS port, the CGenFF stream for the verified ligand microstate, and the CHARMM-modified TIP3P water and ion parameters from that port. Keep the source SDF, original docking output, MOL2 submitted to CGenFF, and the returned stream. For the cutoff port, use the cutoff-specific MDP settings in step 08. Follow the release-specific protocol for a CHARMM36 LJ-PME port. [MacKerell Lab CHARMM force-field releases](https://mackerell.umaryland.edu/charmm_ff.shtml)

1. In the CHARMM replicate directory, prepare a single-ligand MOL2 with the reviewed bond orders, stereochemistry, net charge, explicit hydrogens, and docked heavy-atom coordinates. Compare it with the source SDF.<sup>[15](REFERENCES.md#ref-15),[16](REFERENCES.md#ref-16)</sup>

**Environment:** `docktools`. **Expected files or evidence:** terminal output or the paths named below. For planning, use the per-stage budget in the quickstart.

```bash
conda activate docktools
obabel lig_pose.sdf -O lig_pose.mol2 --title LIG
obabel lig_pose.sdf -ocan
obabel lig_pose.mol2 -ocan
```

2. Submit the MOL2 to the [CGenFF Service](https://cgenff.silcsbio.com/) and save the CHARMM stream containing the ligand topology and additional parameters as `lig_pose.str`. Record the **CGenFF parameter version**, `RESI` name, integer charge, and penalties. Replace `LIG` in the example with the actual `RESI` name. High penalties flag analogies for review. The SilcsBio guide typically recommends further optimization for values above 50. [CGenFF stream format and penalties](https://docs.silcsbio.com/2026/cgenff/usage.html)

**Environment:** `Bash`. **Expected files or evidence:** terminal output or the paths named below. For planning, use the per-stage budget in the quickstart.

```bash
grep -iE 'cgenff version|force field|^[[:space:]]*RESI[[:space:]]|penalty' lig_pose.str | head -30
```

3. Download the GROMACS port that matches the stream **parameter version** from the MacKerell lab. This example uses the February 2026 cutoff port with CGenFF 5.0. Keep the same directory name throughout the workflow. For a CGenFF 4.6 stream, download the matching 4.6 port and update the commands to use that directory. [MacKerell lab force-field downloads](https://mackerell.umaryland.edu/charmm_ff.shtml)

**Environment:** `Bash`. **Expected files or evidence:** terminal output or the paths named below. For planning, use the per-stage budget in the quickstart.

```bash
curl --fail --location  'https://mackerell.umaryland.edu/download.php?filename=CHARMM_ff_params_files%2Fcharmm36-feb2026_cgenff-5.0.ff.tgz'  -o charmm36-feb2026_cgenff-5.0.ff.tgz
tar -tzf charmm36-feb2026_cgenff-5.0.ff.tgz | head -20
tar -xzf charmm36-feb2026_cgenff-5.0.ff.tgz
test -f charmm36-feb2026_cgenff-5.0.ff/forcefield.itp
sha256sum charmm36-feb2026_cgenff-5.0.ff.tgz
```

4. Install the Lemkul Lab converter once. Record its commit and the force-field archive hash. The commands call the lab's upstream converter. [Lemkul Lab converter](https://github.com/Lemkul-Lab/cgenff_charmm2gmx)

**Environment:** `cgenff-tools`. **Expected files or evidence:** terminal output or the paths named below. For planning, use the per-stage budget in the quickstart.

```bash
conda create -n cgenff-tools --override-channels -c conda-forge python=3.13 networkx numpy
mkdir -p "$HOME/tools"
git clone https://github.com/Lemkul-Lab/cgenff_charmm2gmx.git "$HOME/tools/cgenff_charmm2gmx"
git -C "$HOME/tools/cgenff_charmm2gmx" rev-parse HEAD > cgenff_converter_commit.txt
conda activate cgenff-tools
python "$HOME/tools/cgenff_charmm2gmx/cgenff_charmm2gmx.py"  LIG lig_pose.mol2 lig_pose.str charmm36-feb2026_cgenff-5.0.ff
ls -lh lig.itp lig.prm lig_ini.pdb
```

5. Use either GROMACS build to convert the ligand coordinates to GRO, then check atom order, charges, and masses in `lig.itp`. Keep `lig.prm` as the global parameter include. Check the original coordinates in `lig_ini.pdb` and `ligand.gro`. The converter's standalone TOP is useful for review. The final system TOP owns `[ defaults ]`, `[ system ]`, and `[ molecules ]`.

**Environment:** `gmx-cpu`. **Expected files or evidence:** `ligand.gro`. For planning, use the per-stage budget in the quickstart.

```bash
conda activate gmx-cpu
gmx editconf -f lig_ini.pdb -o ligand.gro
cp lig.itp ligand.itp
head -n 2 ligand.gro
```

#### Route B acceptance before complex assembly

Record the converter commit, GROMACS force-field archive hash, CGenFF parameter version, ligand `RESI` identifier, verified integer charge, and the disposition of high-penalty terms. Use the same MOL2 for submission and conversion. If the MOL2 is edited, compare its atom names and order with the stream before running the converter. CGenFF penalties indicate uncertainty in analogy-based assignments. Evaluate the affected terms and follow the CGenFF optimization guidance when warranted. [CGenFF Usage and Penalties](https://docs.silcsbio.com/2026/cgenff/usage.html)

| Check | Acceptance criterion |
| --- | --- |
| Chemistry and coordinates | Compare the submitted MOL2 with the verified SDF for bond orders, stereochemistry, and formal charge. Use the reviewed atom mapping to check heavy-atom coordinates in `lig_ini.pdb` and `ligand.gro` without alignment. Account for Å and nm and for coordinate precision. |
| Local topology | Verify that the atom names and order in `ligand.gro` match the `[ atoms ]` records in `ligand.itp`. Confirm that the total of the assigned partial charges agrees with the verified integer ligand charge. Review any virtual-site mapping separately. |
| System topology | Include `lig.prm` after the CHARMM force-field include and before the first `[ moleculetype ]`. Include `ligand.itp` and record the exact ligand molecule type in `[ molecules ]`. Review the expanded topology from `grompp -pp` before equilibration. [Complex assembly](#complex-assembly) |
| Simulation settings | Archive the water and ion includes selected by the port. For the cutoff example, verify the 1.0–1.2 nm LJ force-switch settings in the processed MDP. [Run parameters](#simulation) |

The check below verifies the atom order and charge sum for the single-ligand GRO and ITP. Replace `0` with the independently verified integer charge if the ligand is charged. The charge tolerance shown is an example for this file check.

**Environment:** `docking-gromacs`. **Expected files or evidence:** terminal output or the paths named below. For planning, use the per-stage budget in the quickstart.

```bash
python - 0 <<'PYTHON'
from math import fsum, isfinite
from pathlib import Path
import re
import sys

expected_charge = int(sys.argv[1])
gro = Path("ligand.gro").read_text().splitlines()
count = int(gro[1].strip())
if count < 1 or len(gro) != count + 3:
    raise SystemExit("Expected a nonempty single-frame ligand GRO file.")
observed_names = [line[10:15].strip() for line in gro[2 : 2 + count]]

section = None
atom_names = []
charges = []
for line in Path("ligand.itp").read_text().splitlines():
    row = line.partition(";")[0].strip()
    heading = re.fullmatch(r"\[\s*(\w+)\s*\]", row)
    if heading:
        section = heading[1].lower()
        continue
    if section != "atoms" or not row:
        continue
    if row.startswith("#"):
        raise SystemExit("Inspect the preprocessed topology for conditional atom rows.")
    fields = row.split()
    if len(fields) < 7 or int(fields[0]) != len(atom_names) + 1:
        raise SystemExit("Check [ atoms ] numbering and record fields.")
    atom_names.append(fields[4])
    charges.append(float(fields[6]))

if not charges or not all(map(isfinite, charges)):
    raise SystemExit("Missing or nonfinite partial charges.")
if observed_names != atom_names:
    raise SystemExit("GRO and ITP atom count, names, or order differ.")
charge_sum = fsum(charges)
if abs(charge_sum - expected_charge) > 0.01:
    raise SystemExit(f"Charge sum {charge_sum:.6f} differs from {expected_charge:+d}.")
print(f"Matched {count} atoms; total partial charge {charge_sum:.6f} e.")
PYTHON
```

**Ligand checks for both routes.** Sum the partial charges in `[ atoms ]` and compare the result with the verified integer net charge. Check the heavy-atom mapping, coordinate units, and atom order between the GRO file and topology. If virtual sites are present, verify their definitions and positions in the coordinate ordering.

**Environment:** `Bash`. **Expected files or evidence:** terminal output or the paths named below. For planning, use the per-stage budget in the quickstart.

```bash
awk '/^[[:space:]]*\[[[:space:]]*atoms[[:space:]]*\]/{in_atoms=1;next}
     /^[[:space:]]*\[/{in_atoms=0}
     in_atoms && $1 ~ /^[0-9]+$/ {total+=$7; atoms++}
     END{if (!atoms) exit 1; printf "Atoms: %d; charge sum: %.6f\n", atoms,total}' ligand.itp
```

<a name="complex-assembly"></a>

## 07. Protein topology, position restraints, and complex assembly

- **Input** Protein and ligand coordinate/topology files
- **Outputs** assembled complex
- **If a step fails** check molecule counts and ordering on a mismatch

Prepare the protein topology in the selected force-field replicate directory. Activate either GROMACS build. The preprocessing commands for both force-field families are available in the CPU and CUDA builds.<sup>[17](REFERENCES.md#ref-17)</sup>

**CPU build**

**Environment:** `gmx-cpu`. **Expected files or evidence:** terminal output or the paths named below. For planning, use the per-stage budget in the quickstart.

```bash
conda activate gmx-cpu
gmx --version
```

**CUDA build**

**Environment:** `docking-gromacs`. **Expected files or evidence:** terminal output or the paths named below. For planning, use the per-stage budget in the quickstart.

```bash
source "$HOME/opt/gromacs-2026.3-cuda/bin/GMXRC"
gmx --version
```

**Route A**

**Environment:** `docking-gromacs`. **Expected files or evidence:** `protein.gro`, `topol.top`. For planning, use the per-stage budget in the quickstart.

```bash
gmx pdb2gmx -f protein.pdb -o protein.gro -p topol.top -i posre.itp  -ff amber99sb-ildn -water tip3p -ignh
cp topol.top topol_protein.top
```

**Route B**

**Environment:** `docking-gromacs`. **Expected files or evidence:** `protein.gro`, `topol.top`. For planning, use the per-stage budget in the quickstart.

```bash
gmx pdb2gmx -f protein.pdb -o protein.gro -p topol.top -i posre.itp  -ff charmm36-feb2026_cgenff-5.0 -water tip3p -ignh
cp topol.top topol_protein.top
```

Verify termini, histidine protonation states, disulfide bonds, chain connectivity, and the TIP3P include selected by the force field. Consult the force-field documentation and `pdb2gmx -h` to select explicit histidine states. Follow the AMBER naming convention for nonstandard termini. [pdb2gmx reference](https://manual.gromacs.org/current/onlinehelp/gmx-pdb2gmx.html)

`pdb2gmx -ignh` rebuilds hydrogens according to the chosen residue states. Review the generated chain topologies and restraint files and verify the protein's absolute heavy-atom coordinates. Resolve missing heavy atoms during structure preparation.

**Topology editing for route A.** Move `[ atomtypes ]` and any other required global type definitions from `ligand.itp` to `ligand_atomtypes.itp`. Verify that the ligand and protein force fields agree on `[ defaults ]`, combination rules, and 1–4 scaling. Resolve naming conflicts and keep a single global defaults block. Preserve the generated protein, solvent, and ion entries. The snippet shows where to insert the ligand includes.

```ini
#include "amber99sb-ildn.ff/forcefield.itp"
#include "ligand_atomtypes.itp"
; Existing protein molecule definitions and protein restraint includes
#include "ligand.itp"
; Existing water and ion includes

[ system ]
Protein-ligand complex

[ molecules ]
; Existing protein molecule names and counts, in their original order
LIG  1
```

**Topology editing for route B.** Place the converter's `lig.prm` after the CHARMM force-field include and before the first `[ moleculetype ]`. Preserve the generated protein, water, ion, and restraint includes. Use these insertion points.

```ini
#include "charmm36-feb2026_cgenff-5.0.ff/forcefield.itp"
#include "lig.prm"
; Existing protein molecule definitions and protein restraint includes
#include "ligand.itp"
; Existing CHARMM TIP3P and ion includes

[ system ]
Protein-ligand complex

[ molecules ]
; Existing protein molecule names and counts, in their original order
LIG  1
```

For both routes, ensure that the order in `[ molecules ]` matches the protein, ligand, solvent, and ions in the coordinates. [GROMACS topology formats](https://manual.gromacs.org/2026.3/reference-manual/topologies/topology-file-formats.html)

Use the name in `[ moleculetype ]` from `ligand.itp` in place of `LIG`. Generate a ligand-local index and heavy-atom restraints from `ligand.gro`. A mass selection from GRO coordinates can rely on atom names. Compare the selected atoms against their ITP masses before choosing `Ligand_heavy_local` in `gmx genrestr`.

**Environment:** `docking-gromacs`. **Expected files or evidence:** `ligand.gro`, `ligand_heavy_local.ndx`, `posre_ligand.itp`. For planning, use the per-stage budget in the quickstart.

```bash
gmx select -s ligand.gro -select '"Ligand_heavy_local" mass > 2.5' -on ligand_heavy_local.ndx
gmx genrestr -f ligand.gro -n ligand_heavy_local.ndx -o posre_ligand.itp -fc 1000 1000 1000
```

Add this conditional block at the end of the ligand's molecule definition in `ligand.itp`. If ACPYPE already added a ligand restraint block, review it and use a single restraint definition. The restraint indices are local to the ligand molecule.

```ini
#ifdef POSRES_LIG
#include "posre_ligand.itp"
#endif
```

The commands preserve the original coordinate rows in protein-first, ligand-second order. Use single-frame GRO files. Line 2 gives the atom count, and the total line count is the atom count plus three. Check the merged order against `[ molecules ]`.

**Environment:** `Bash`. **Expected files or evidence:** terminal output or the paths named below. For planning, use the per-stage budget in the quickstart.

```bash
head -n 2 protein.gro ligand.gro
wc -l protein.gro ligand.gro

protein_atoms=$(sed -n '2p' protein.gro | tr -d '[:space:]')
ligand_atoms=$(sed -n '2p' ligand.gro | tr -d '[:space:]')
solute_atoms=$((protein_atoms + ligand_atoms))

printf 'Protein-ligand complex\n%5d\n' "$solute_atoms" > complex_raw.gro
sed -n "3,$((protein_atoms + 2))p" protein.gro >> complex_raw.gro
sed -n "3,$((ligand_atoms + 2))p" ligand.gro >> complex_raw.gro
tail -n 1 protein.gro >> complex_raw.gro
wc -l complex_raw.gro
```

**Check.** Overlay the assembled complex with the original binding pose. Check atom order, atom counts, and net charge against the topology. The box setup translates the assembled complex as a whole.

<a name="simulation"></a>

## 08. GROMACS run parameters (MDP)

- **Input** Matching parameter ecosystem and simulation goals
- **Outputs** per-stage MDPs
- **If a step fails** resolve unknown or incompatible keys

The example uses 300 K, 1 bar, 0.15 M added NaCl, particle mesh Ewald (PME), and a 2 fs integration step. Save the AMBER baseline in the files below. For CHARMM, apply the nonbonded settings at the end of the section. Select and document the production duration and number of independent replicates for your research question. [Versioned MDP options](https://manual.gromacs.org/2026.3/user-guide/mdp-options.html)

**Temperature and pressure coupling.** The V-rescale thermostat and C-rescale barostat are described in separate methods papers. Use the MDP reference corresponding to your GROMACS version.<sup>[18](REFERENCES.md#ref-18),[19](REFERENCES.md#ref-19)</sup> [V-rescale](https://doi.org/10.1063/1.2408420) · [C-rescale](https://doi.org/10.1063/5.0020514) · [GROMACS MDP reference](https://manual.gromacs.org/2026.3/user-guide/mdp-options.html)

### `ions.mdp` · Ion-placement preprocessing

Use this file to generate the TPR input for `genion`.

```ini
integrator      = steep
nsteps          = 500
emtol           = 1000
emstep          = 0.01
cutoff-scheme   = Verlet
coulombtype     = Cut-off
rcoulomb        = 1.0
vdwtype         = Cut-off
rvdw            = 1.0
pbc             = xyz
constraints     = none
```

### `em.mdp` · Energy minimization

```ini
integrator      = steep
nsteps          = 50000
emtol           = 1000
emstep          = 0.01
cutoff-scheme   = Verlet
coulombtype     = PME
rcoulomb        = 1.0
vdwtype         = Cut-off
rvdw            = 1.0
DispCorr        = EnerPres
pbc             = xyz
constraints     = none
nstenergy       = 100
nstlog          = 100
```

### `nvt.mdp` · Temperature equilibration

```ini
define                  = -DPOSRES -DPOSRES_LIG
integrator              = md
dt                      = 0.002
nsteps                  = 50000
continuation            = no
constraints             = h-bonds
constraint-algorithm    = lincs
cutoff-scheme           = Verlet
nstlist                 = 20
coulombtype             = PME
rcoulomb                = 1.0
vdwtype                 = Cut-off
rvdw                    = 1.0
DispCorr                = EnerPres
pme-order               = 4
fourierspacing          = 0.12
pbc                     = xyz
tcoupl                  = V-rescale
tc-grps                 = Complex Water_and_ions
tau-t                   = 1.0 1.0
ref-t                   = 300 300
pcoupl                  = no
gen-vel                 = yes
gen-temp                = 300
gen-seed                = 202601
nstxout                 = 0
nstvout                 = 0
nstfout                 = 0
nstenergy               = 500
nstlog                  = 500
nstxout-compressed      = 500
```

### `npt.mdp` · Pressure equilibration

Copy `nvt.mdp`, replace the existing keys below, and add the new pressure-coupling keys. Remove `gen-temp` and `gen-seed`. Keep `define`.

**Environment:** `Bash`. **Expected files or evidence:** terminal output or the paths named below. For planning, use the per-stage budget in the quickstart.

```bash
cp nvt.mdp npt.mdp
```

```ini
nsteps                  = 500000
continuation            = yes
gen-vel                 = no
pcoupl                  = C-rescale
pcoupltype              = isotropic
tau-p                   = 5.0
ref-p                   = 1.0
compressibility         = 4.5e-5
refcoord-scaling        = com
```

### `smoke.mdp`, `pilot.mdp`, and `md.mdp` · Smoke tests, pilots, and production

Use `npt.mdp` as a template for `md.mdp` and for the optional `smoke.mdp` and `pilot.mdp` inputs. Remove `define` and `refcoord-scaling` for these unrestrained stages. Retain constraints on bonds involving hydrogen (`constraints = h-bonds`). Apply the stage-specific settings below and keep one entry per key.

**Environment:** `Bash`. **Expected files or evidence:** terminal output or the paths named below. For planning, use the per-stage budget in the quickstart.

```bash
cp npt.mdp md.mdp

# Optional smoke test and pilot
cp npt.mdp smoke.mdp
cp npt.mdp pilot.mdp
```

| File | `nsteps` | Duration | `nstenergy`, `nstlog`, `nstxout-compressed` |
| --- | ---: | ---: | ---: |
| `nvt.mdp` | 50,000 | 100 ps | 500 |
| `npt.mdp` | 500,000 | 1 ns | 500 |
| `smoke.mdp` | 10,000 | 20 ps | 500 |
| `pilot.mdp` | 500,000 | 1 ns | 500 |
| `md.mdp` | 50,000,000 | 100 ns | 5,000 |

Enter integer values without group separators, for example `50000000`. The 100 ns production duration is illustrative. At a 2 fs integration step, saving every 5,000 steps gives 10 ps between frames. Select an output interval appropriate for the analysis.

**Coordinate-output interval.** The coordinate-output interval is `dt × nstxout-compressed`. With a 2 fs step, values of `5000` and `15000` give intervals of 10 and 30 ps. Choose the interval based on the analysis timescale, storage budget, and measured trajectory size. Energy, log, and coordinate output frequencies can be set independently.

The analysis examples use an XTC containing the full system. To follow them, set `compressed-x-grps = System` in the production MDP and verify that the group includes every atom. For a solute-only trajectory, export a matching structure or topology with identical atom order and adapt the analysis commands. [GROMACS output control](https://manual.gromacs.org/documentation/current/user-guide/mdp-options.html)

### CHARMM36m + CGenFF cutoff MDP settings

For route B's cutoff port, create separate copies of all seven MDP files. Apply the following keys to `ions.mdp`, `em.mdp`, `nvt.mdp`, `npt.mdp`, `smoke.mdp`, `pilot.mdp`, and `md.mdp`. Replace matching keys and add missing ones. Keep each stage's integrator, coupling, step count, and restraint settings. Keep `coulombtype = Cut-off` in `ions.mdp` for ion-placement TPR preparation. Retain `coulombtype = PME` in the six run stages. [GROMACS recommended CHARMM settings](https://manual.gromacs.org/2026.3/user-guide/force-fields.html)

```ini
rcoulomb       = 1.2
vdwtype        = Cut-off
vdw-modifier   = Force-switch
rvdw-switch    = 1.0
rvdw           = 1.2
DispCorr       = no
```

Cross-check the MDP against the chosen port. An LJ-PME port requires its own settings. [MacKerell port notes](https://mackerell.umaryland.edu/charmm_ff.shtml)

## Parameter checklist for the two force-field routes

| Setting | Route A | Route B, cutoff port |
| --- | --- | --- |
| Protein / ligand | AMBER99SB-ILDN / GAFF2 + AM1-BCC | CHARMM36m / matching CGenFF stream |
| Water and ions | AMBER port TIP3P and matching ions | CHARMM-modified TIP3P and matching ions |
| Teaching setpoints | 300 K, 1 bar, 0.15 M added NaCl | 300 K, 1 bar, 0.15 M added NaCl |
| Solvated dynamics step | 2 fs with appropriate H-bond constraints | 2 fs with appropriate H-bond constraints |
| PME cutoff and LJ | 1.0 nm electrostatics and LJ cutoff, dispersion correction per baseline | 1.2 nm electrostatics, LJ force-switch 1.0–1.2 nm, no analytical dispersion correction |
| Example production output | Every 5,000 steps, 10 ps | Every 5,000 steps, 10 ps |

| File | Route B changes to nonbonded settings | Stage-specific fields to review |
| --- | --- | --- |
| ions.mdp | Six cutoff keys above; retain Coulomb Cut-off | Ion-placement preprocessor and box |
| em.mdp | Six cutoff keys above; retain PME | Maximum force target |
| nvt.mdp | Six cutoff keys above; retain PME | Restraints, temperature groups and velocity seed |
| npt.mdp | Six cutoff keys above; retain PME | Restraints, pressure, volume and continuation |
| smoke.mdp | Six cutoff keys above; retain PME | Short diagnostic, full output |
| pilot.mdp | Six cutoff keys above; retain PME | Unrestrained stability and resource measurement |
| md.mdp | Six cutoff keys above; retain PME | Sampling length, output stride and checkpoint |

An LJ-PME port changes both the dispersion calculation and its expected parameter protocol. Use the matching port and instructions and verify the processed MDP. See [research validation design](RESEARCH.md#alternative-parameters).
