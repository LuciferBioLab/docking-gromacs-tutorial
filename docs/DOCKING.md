# Preparation, docking, and pose transfer

**English** · [简体中文](DOCKING.zh-CN.md)

[Repository home](../README.md#contents)

<a name="docking"></a>

## 03. Receptor and ligand preparation

- **Input** Reviewed protein PDB and ligand SDF
- **Outputs** receptor/ligand PDBQT
- **If a step fails** stop at structural or protonation ambiguity

Use these commands for a new Linux project. If you already staged inputs, run only the last line from the corresponding project directory. [Local inputs](#local-inputs)

**Environment:** `Bash`. **Expected files or evidence:** terminal output or the paths named below. For planning, use the per-stage budget in the quickstart.

```bash
mkdir -p "$HOME/docking-md-workshop"
cd "$HOME/docking-md-workshop"
mkdir -p input ligands/pdbqt dock qc md
```

<a name="local-inputs"></a>

### Start from local PDB and SDF files

Open PowerShell in a new project directory and set the absolute paths to the source PDB and SDF files. The example stages the two selected files under the tutorial's standard names. Use PowerShell for staging and WSL or Linux for Bash instructions. On Linux, copy the selected files directly to `input/` under the same names. [Microsoft WSL filesystem guidance](https://learn.microsoft.com/en-us/windows/wsl/filesystems)

<details>
<summary>PowerShell staging example</summary>

**Environment:** `PowerShell`. **Expected files or evidence:** terminal output or the paths named below. For planning, use the per-stage budget in the quickstart.

```powershell
$Protein = 'C:\path\to\protein.pdb'
$Ligand  = 'C:\path\to\ligand.sdf'

if (!(Test-Path -LiteralPath $Protein -PathType Leaf) -or
    !(Test-Path -LiteralPath $Ligand -PathType Leaf)) {
    throw 'Check the two input file paths.'
}

$InputDir = Join-Path (Get-Location).Path 'input'
$ProteinCopy = Join-Path $InputDir 'protein_raw.pdb'
$LigandCopy = Join-Path $InputDir 'ligand_raw.sdf'
if ((Test-Path -LiteralPath $ProteinCopy) -or (Test-Path -LiteralPath $LigandCopy)) {
    throw 'The input directory already has a staged file. Use a fresh project directory.'
}

New-Item -ItemType Directory -Force -Path $InputDir -ErrorAction Stop | Out-Null
Copy-Item -LiteralPath $Protein -Destination $ProteinCopy -ErrorAction Stop
Copy-Item -LiteralPath $Ligand -Destination $LigandCopy -ErrorAction Stop
wsl pwd
```

Use `wsl pwd` to identify the WSL path corresponding to the current directory and verify the two copies there. Recheck paths if you move the project to the Linux filesystem.

</details>

| Source input | Requirements for the next step |
| --- | --- |
| `input/protein_raw.pdb` | Review assembly, chains, pocket, nonstandard components, and missing regions. Prepare `protein.pdb` for MD and `receptorH.pdb` for docking. |
| `input/ligand_raw.sdf` (2D SDF) | Verify bond orders, stereochemistry, and microstate, then generate a 3D conformer with explicit hydrogens for Meeko. |
| `input/ligand_raw.sdf` (3D SDF) | Review coordinates, explicit hydrogens, chemistry, and record number. A validated single record can be used directly for ligand preparation. |

[Ligand input requirements](https://meeko.readthedocs.io/en/develop/lig_prep_basic.html) · [Complex structure review](TROUBLESHOOTING.md#complex-systems)

| Input | Preparation |
| --- | --- |
| `input/protein.pdb` | Prepare the protein for MD. Review the biological assembly, chains, alternate conformations, missing residues and heavy atoms, disulfides, termini, and histidine states. Retain the original structure, PDB ID and curation rationale. |
| `input/receptorH.pdb` | Provide a Meeko-compatible receptor in the same coordinate frame using reviewed protonation assumptions. Evaluate each water, ion, or cofactor for its role in the pocket. |
| `input/ligand_raw.sdf` | Obtain a molecule record with defined bond orders, stereochemistry, and identity. Record the CID or other source, pH assumption, and integer net charge of each candidate. |
| `dock/box.txt` | Define and visually check the search box using the co-crystal ligand or other pocket evidence. Use Å for the center coordinates and all three edge lengths. Keep a separate configuration for each receptor or pocket. |

Structure databases and setup docs · [RCSB PDB](https://www.rcsb.org/) · [PubChem](https://pubchem.ncbi.nlm.nih.gov/) · [Meeko receptor options](https://meeko.readthedocs.io/en/develop/rec_cli_options.html) · [Molscrub CLI](https://molscrub.readthedocs.io/en/latest/cli.html)

**Receptor files for docking and MD.** Review chain identity, alternate locations, missing atoms or residues, and any essential solvent molecules or cofactors in the source structure. Open-source PyMOL can be used to curate `input/protein.pdb`. Review the hydrogen and protonation model in `input/receptorH.pdb` before generating receptor PDBQT with Meeko. AutoDockTools can assist with legacy preparation and AutoGrid parameter files (GPF). Use the prepared protein PDB for MD topology generation with `pdb2gmx`. [Meeko receptor preparation](https://meeko.readthedocs.io/en/develop/rec_cli_options.html) · [Scripps AutoDock Suite](https://ccsb.scripps.edu/autodocksuite/)

The example selects record 1 from the Molscrub output. Substitute the record number established during chemical review. You may supply a vetted single-record 3D SDF with explicit hydrogens as `ligands/state001.sdf`. Assign a distinct identifier to each ligand microstate.

**Environment:** `docktools`. **Expected files or evidence:** terminal output or the paths named below. For planning, use the per-stage budget in the quickstart.

```bash
conda activate docktools
scrub.py input/ligand_raw.sdf -o ligands/candidates.sdf --ph 7.4
obabel ligands/candidates.sdf -ocan
obabel ligands/candidates.sdf -f 1 -l 1 -O ligands/state001.sdf
```

**Review the candidate with RDKit.** From the `docktools` environment, load the selected SDF in Python and verify stereochemistry, integer net charge, explicit hydrogen count, and the 3D conformer flag. Resolve any parsing or chemical-identity discrepancy before calling Meeko. [RDKit Python guide](https://www.rdkit.org/docs/GettingStartedInPython.html)

**Environment:** `docking-gromacs`. **Expected files or evidence:** terminal output or the paths named below. For planning, use the per-stage budget in the quickstart.

```bash
python
```

```python
from rdkit import Chem

candidate = Chem.SDMolSupplier("ligands/state001.sdf", removeHs=False)[0]
Chem.MolToSmiles(Chem.RemoveHs(candidate), isomericSmiles=True)
Chem.GetFormalCharge(candidate)
sum(atom.GetAtomicNum() == 1 for atom in candidate.GetAtoms())
candidate.GetConformer().Is3D()
exit()
```

**Environment:** `Bash`. **Expected files or evidence:** terminal output or the paths named below. For planning, use the per-stage budget in the quickstart.

```bash
mk_prepare_receptor.py --read_pdb input/receptorH.pdb -o dock/receptor -p
mk_prepare_ligand.py -i ligands/state001.sdf -o ligands/pdbqt/state001.pdbqt
sha256sum input/* > qc/input_sha256.txt
```

Write the six fields to `dock/box.txt` and substitute the actual center and edge lengths. Convert legacy AutoGrid interval counts to Å using the grid spacing. If the binding site is unknown, use a separate exploratory box and evaluate sampling and pocket plausibility.

```ini
center_x = 15.190
center_y = 53.903
center_z = 16.917
size_x = 20.0
size_y = 20.0
size_z = 20.0
```

**Check.** Verify the SDF record count, explicit hydrogens, stereochemistry, bond orders, and net charge. Check that the ligand PDBQT retains the Meeko mapping metadata and that the receptor, reference ligand, and search box use the same coordinate frame. [Meeko documentation](https://meeko.readthedocs.io/) · [Open Babel CLI](https://openbabel.org/docs/Command-line_tools/babel.html)

**Structure and chemistry references.** Use wwPDB validation reports to review deposited experimental structures and the Chemical Component Dictionary to check ligand identifiers. [wwPDB validation reports](https://www.wwpdb.org/validation/validation-reports) · [Chemical Component Dictionary](https://www.wwpdb.org/data/ccd)

**Focused screening, blind docking, and follow-up.** Use a focused box when structural evidence identifies the binding site. Validate the protocol by redocking when a co-crystal pose is available. For exploratory docking, use a separate file such as `dock/box_blind.txt` and record the coverage, seeds, and search settings. Inspect pose clusters for structurally plausible pockets, then use separate focused boxes and output directories for follow-up. In a legacy GPF, `npts 60 60 60` with `spacing 0.375` defines three 22.5 Å edges. Resolve `gridcenter auto` to verified coordinates before writing the Vina configuration. [Vina FAQ](https://autodock-vina.readthedocs.io/en/latest/faq.html)

<a name="batch-docking"></a>

## 04. Batch docking on CPU and CUDA

- **Input** PDBQT, box and manifest
- **Outputs** scored poses and job logs
- **If a step fails** inspect failed entries before resuming

The CPU and CUDA workflows use the same receptor PDBQT, ligand PDBQT files, and search box from step 03. Use a separate output directory for each screen. Prepare ligands individually or pass a reviewed multi-record SDF to Meeko with `--multimol_outdir`. Track the mapping between ligand IDs and source SDF records, including duplicate IDs and failed preparations.<sup>[7](REFERENCES.md#ref-7)</sup> [Meeko ligand CLI](https://meeko.readthedocs.io/en/develop/lig_cli_options.html)

### A. CPU · AutoDock Vina

Run a single curated ligand and inspect its output and log before launching the batch.

**Environment:** `docktools`. **Expected files or evidence:** terminal output or the paths named below. For planning, use the per-stage budget in the quickstart.

```bash
conda activate docktools
mkdir dock/cpu_single_202601
vina --receptor dock/receptor.pdbqt --ligand ligands/pdbqt/state001.pdbqt  --config dock/box.txt --scoring vina --cpu 4 --exhaustiveness 32  --num_modes 20 --seed 202601 --out dock/cpu_single_202601/state001_out.pdbqt  > dock/cpu_single_202601/vina.log 2>&1
tail -20 dock/cpu_single_202601/vina.log
grep -E '^MODEL|^REMARK VINA RESULT' dock/cpu_single_202601/state001_out.pdbqt
```

**Environment:** `docking-gromacs`. **Expected files or evidence:** terminal output or the paths named below. For planning, use the per-stage budget in the quickstart.

```bash
mkdir dock/cpu_batch_202601
time vina --receptor dock/receptor.pdbqt --batch ligands/pdbqt/*.pdbqt  --config dock/box.txt --scoring vina --cpu 4 --exhaustiveness 32  --num_modes 20 --seed 202601 --dir dock/cpu_batch_202601  > dock/cpu_batch_202601/vina.log 2>&1
find ligands/pdbqt -maxdepth 1 -type f -name '*.pdbqt' | wc -l
find dock/cpu_batch_202601 -maxdepth 1 -type f -name '*.pdbqt' | wc -l
```

`--batch` processes ligands sequentially against one receptor. `--cpu 4` sets the thread count for a Vina process. Split large libraries into separate jobs to parallelize within your CPU allocation. Use a separately defined box for each receptor. [Vina native batch mode](https://autodock-vina.readthedocs.io/en/latest/docking_in_batch.html)

#### Native Windows Vina and WSL2 handoff

For WSL preparation followed by native Windows Vina, copy the docking files to your Windows profile. Replace `YOUR_WINDOWS_USER` and run these commands from the WSL project root. Keep the original SDF and the MD-ready protein PDB in the WSL project. Use the Windows drive for the handoff. [Microsoft WSL filesystems](https://learn.microsoft.com/windows/wsl/filesystems)

**Environment:** `Bash`. **Expected files or evidence:** terminal output or the paths named below. For planning, use the per-stage budget in the quickstart.

```bash
win_user='YOUR_WINDOWS_USER'
win_job="/mnt/c/Users/$win_user/MD_exchange/target01"
mkdir -p "/mnt/c/Users/$win_user/MD_exchange"
mkdir "$win_job" &&
  mkdir -p "$win_job/dock" "$win_job/ligands/pdbqt" &&
  cp dock/receptor.pdbqt dock/box.txt "$win_job/dock/" &&
  cp ligands/pdbqt/*.pdbqt "$win_job/ligands/pdbqt/"
```

Enter the exchange directory in Windows PowerShell. The example expects the upstream executable there as `vina.exe`. Set `$Vina` to its full path if it is installed elsewhere. [Official Windows batch instructions](https://autodock-vina.readthedocs.io/en/latest/docking_in_batch.html)

**Environment:** `PowerShell`. **Expected files or evidence:** terminal output or the paths named below. For planning, use the per-stage budget in the quickstart.

```powershell
Set-Location (Join-Path $env:USERPROFILE 'MD_exchange\target01')
$Vina = '.\vina.exe'
& $Vina --version
$Ligands = @(Get-ChildItem '.\ligands\pdbqt' -Filter '*.pdbqt' -File |
    Sort-Object Name | Select-Object -ExpandProperty FullName)
if ($Ligands.Count -eq 0) { throw 'No ligand PDBQT files found' }
New-Item -ItemType Directory -Path '.\dock\cpu_batch_win_202601' -ErrorAction Stop
& $Vina --receptor .\dock\receptor.pdbqt --batch $Ligands --config .\dock\box.txt `
    --scoring vina --cpu 4 --exhaustiveness 32 --num_modes 20 --seed 202601 `
    --dir .\dock\cpu_batch_win_202601 > .\dock\cpu_batch_win_202601\vina.log 2>&1
if ($LASTEXITCODE -ne 0) { throw 'See the Vina log' }
(Get-ChildItem '.\dock\cpu_batch_win_202601' -Filter '*.pdbqt' -File).Count
```

Return to the same WSL Bash session and project root. Copy the entire batch output and inspect the log and poses. In a new terminal, set `win_job` again first. In step 05, set `pose_file` to the candidate file you copied back. Run subsequent setup and trajectory work on the WSL filesystem.

**Environment:** `Bash`. **Expected files or evidence:** terminal output or the paths named below. For planning, use the per-stage budget in the quickstart.

```bash
test -d "$win_job/dock/cpu_batch_win_202601" &&
  test ! -e dock/cpu_batch_win_202601 &&
  cp -a "$win_job/dock/cpu_batch_win_202601" dock/
find dock/cpu_batch_win_202601 -maxdepth 1 -type f -name '*.pdbqt' -print
tail -20 dock/cpu_batch_win_202601/vina.log
```

### B. NVIDIA GPU · Uni-Dock CUDA

Run from the Linux or WSL2 project root. Verify a single ligand with `--gpu_batch` first. During a longer run, monitor GPU activity with `nvidia-smi -l 1` in a second terminal. [Uni-Dock CLI](https://github.com/dptech-corp/Uni-Dock/tree/main/unidock)

**Environment:** `dockgpu`. **Expected files or evidence:** terminal output or the paths named below. For planning, use the per-stage budget in the quickstart.

```bash
conda activate dockgpu
mkdir dock/gpu_single_202601
unidock --receptor dock/receptor.pdbqt --gpu_batch ligands/pdbqt/state001.pdbqt  --config dock/box.txt --scoring vina --search_mode balance  --num_modes 20 --seed 202601 --dir dock/gpu_single_202601  > dock/gpu_single_202601/unidock.log 2>&1
tail -25 dock/gpu_single_202601/unidock.log
find dock/gpu_single_202601 -maxdepth 1 -type f -name '*.pdbqt' -print
```

Pass a manifest to `--ligand_index` with one relative path per line and unique filenames without spaces. Measure device memory use, throughput, and output completeness on a representative subset before scaling.

**Environment:** `Bash`. **Expected files or evidence:** terminal output or the paths named below. For planning, use the per-stage budget in the quickstart.

```bash
mkdir dock/gpu_batch_202601
find ligands/pdbqt -maxdepth 1 -type f -name '*.pdbqt' | LC_ALL=C sort  > dock/gpu_batch_202601/ligands.txt
test -s dock/gpu_batch_202601/ligands.txt
```

Run after confirming the manifest is nonempty. If VRAM is limited, split it with `split -l 32 dock/gpu_batch_202601/ligands.txt dock/gpu_chunk_`. Give every run its own manifest path, log, and output directory.

**Environment:** `dockgpu`. **Expected files or evidence:** terminal output or the paths named below. For planning, use the per-stage budget in the quickstart.

```bash
time unidock --receptor dock/receptor.pdbqt  --ligand_index dock/gpu_batch_202601/ligands.txt  --config dock/box.txt --scoring vina --search_mode balance  --num_modes 20 --seed 202601 --dir dock/gpu_batch_202601  > dock/gpu_batch_202601/unidock.log 2>&1
wc -l dock/gpu_batch_202601/ligands.txt
find dock/gpu_batch_202601 -maxdepth 1 -type f -name '*.pdbqt' | wc -l
tail -25 dock/gpu_batch_202601/unidock.log
```

`fast`, `balance`, and `detail` control Uni-Dock's search effort. For follow-up docking, change the seed or search effort and use a new output directory. Verify that files contain poses and scores. Reconcile outputs against manifest IDs, inspect logs for CUDA or parsing errors, and record incomplete jobs. [Uni-Dock modes and batch manifest](https://github.com/dptech-corp/Uni-Dock/blob/main/unidock/README.md)

### Benchmarking the docking engines

Use identical receptor, search box, and ligand inputs. Document engine versions, scoring functions, search settings, seeds, device, thread count, elapsed wall time, successful ligand count, and peak VRAM where applicable. Report throughput as successful ligands per unit of wall time. Compare native-pose recovery, key contacts, ranking, and repeatability across seeds. Retain separate score tables for the two engines.<sup>[8](REFERENCES.md#ref-8)</sup>

**Other GPU engines.** Vina-GPU 2.1 provides OpenCL docking on the upstream-supported Windows or Linux setups. Its repository includes a sample and documents `--ligand_directory` and `--output_directory` for batch runs. Its NVIDIA build instructions reference CUDA Toolkit paths, while its search kernels use OpenCL. Scripps AutoDock-GPU supports CUDA/OpenCL and uses the AutoDock4 protocol with affinity maps.<sup>[9](REFERENCES.md#ref-9),[10](REFERENCES.md#ref-10)</sup> [Vina-GPU 2.1](https://github.com/DeltaGroupNJUPT/Vina-GPU-2.1) · [Scripps AutoDock-GPU](https://github.com/forlilab/AutoDock-GPU)

### Follow-up docking and pose selection

Redock shortlisted candidates with the same microstate, receptor frame, and focused search box. For the CPU example, repeat step 04A with seeds `202602` and `202603` and distinct logs and output directories. For Uni-Dock, set `--seed` for each repeat in `balance` mode, then assess increased sampling with `detail`. Group poses using a documented heavy-atom criterion and inspect pocket placement, steric clashes, and reference contacts. Record the selected pose and any failed runs.

| Record | Fields |
| --- | --- |
| Inputs | Receptor chain, box config, ligand source, SDF record ID, net charge |
| Docking | Engine, version, search effort, seed, output plus MODEL or SDF record, score |
| Selection | Redocking reference, pose group, key contacts, rejection reasons, selected pose |

<a name="pose-handoff"></a>

## 05. Docked-pose transfer to molecular dynamics

- **Input** Selected docking model and original chemistry
- **Outputs** validated SDF/MOL2
- **If a step fails** redock if the mapping is ambiguous

Both workflows produce `lig_pose.sdf`. The source SDF defines the molecular graph, formal charge, protonation state, and stereochemistry. The selected docking pose supplies the heavy-atom coordinates in the original receptor frame. Choose the recovery method from the available metadata and source structure. Docking hardware is an independent choice.

**Pose-transfer references.** See the Meeko paper for PDBQT interoperability and the Open Babel manual for subsequent format conversion.<sup>[1](REFERENCES.md#ref-1),[6](REFERENCES.md#ref-6)</sup> [Meeko paper](https://doi.org/10.1021/acs.jcim.5c02271) · [Open Babel CLI](https://openbabel.org/docs/Command-line_tools/babel.html) · [Open Babel paper](https://doi.org/10.1186/1758-2946-3-33)

| Route | When to use it | How to recover |
| --- | --- | --- |
| **A · Meeko-preserved mapping** | New jobs, or outputs retaining Meeko's SMILES and atom indices. | Prepare and check the state, dock mapped PDBQT, export SDF with `mk_export.py`, then verify with RDKit. |
| **[B · Legacy ADT with SDF template](#legacy-adt-handoff)** | A legacy ADT pose and the original SDF for the same chemical state are available. | Select the PDBQT MODEL, verify the atom map, then use RDKit to transfer coordinates, add hydrogens, check the pose and write SDF. |

Archive the original ligand SDF and docking output in separate work directories for each force field, pose, and replicate. The example uses `ff_family=amber` and a pose from the CPU run. Set `ff_family=charmm` for CHARMM, or set `pose_file` to the selected PDBQT from step 04B for a CUDA-generated pose.

**Environment:** `docktools`. **Expected files or evidence:** terminal output or the paths named below. For planning, use the per-stage budget in the quickstart.

```bash
conda activate docktools
ff_family=amber
pose_file=dock/cpu_single_202601/state001_out.pdbqt
run_dir="md/${ff_family}_state001_pose01_rep01"

test -s "$pose_file" &&
  mkdir "$run_dir" &&
  cp input/protein.pdb "$run_dir/protein.pdb" &&
  cp ligands/state001.sdf "$run_dir/state_original.sdf" &&
  cp "$pose_file" "$run_dir/selected_run.pdbqt" &&
cd "$run_dir"
```

### A. Pose recovery from Meeko metadata

Archive the original SDF and Meeko-prepared ligand PDBQT. In the docking output, verify `REMARK SMILES` and `REMARK SMILES IDX`, and check `REMARK H PARENT` where present. [Meeko export documentation](https://meeko.readthedocs.io/en/develop/export_usage.html)

**Environment:** `Bash`. **Expected files or evidence:** terminal output or the paths named below. For planning, use the per-stage budget in the quickstart.

```bash
awk '/^REMARK SMILES / && $3 != "IDX" {print; found=1; exit}
     END {if (!found) exit 1}' selected_run.pdbqt
grep -m 1 '^REMARK SMILES IDX ' selected_run.pdbqt
grep -m 1 '^REMARK H PARENT ' selected_run.pdbqt || true
```

Export once the mapping checks pass. For legacy ADT output without Meeko metadata, follow route B. For any new docking run, record its engine, search settings, and pose-selection rationale separately.

**Environment:** `docking-gromacs`. **Expected files or evidence:** `docked_poses.sdf`. For planning, use the per-stage budget in the quickstart.

```bash
mk_export.py selected_run.pdbqt -s docked_poses.sdf
grep -E '^MODEL|^REMARK VINA RESULT' selected_run.pdbqt
obabel docked_poses.sdf -ocan
```

**Optional native SDF from Uni-Dock.** If a Uni-Dock PDBQT output lacks Meeko metadata, use Uni-Dock Tools to prepare GPU input from the original SDF and redock against the same receptor and box to produce SDF poses with a molecular graph. This optional fallback produces poses from a new docking job. Start from the step 05 replicate directory. The first command returns to the project root. Keep the `run_dir` variable set above. [Uni-Dock Tools instructions](https://github.com/dptech-corp/Uni-Dock/blob/main/unidock_tools/README.md)

**Environment:** `dockgpu`. **Expected files or evidence:** terminal output or the paths named below. For planning, use the per-stage budget in the quickstart.

```bash
cd ../..
conda install -n dockgpu --override-channels -c conda-forge python=3.11 pip
conda activate dockgpu
python -m pip install 'git+https://github.com/dptech-corp/Uni-Dock.git@1.2.0#subdirectory=unidock_tools'
mkdir -p dock/gpu_sdfprep_202601 dock/gpu_sdf_202601
unidocktools ligandprep -l ligands/state001.sdf -sd dock/gpu_sdfprep_202601
find dock/gpu_sdfprep_202601 -maxdepth 1 -type f -name '*.sdf' -print
```

Check that the prepared ligand has the intended microstate. Before copying the results, verify that there is one SDF file for this ligand. A single file may contain multiple pose records.

**Environment:** `dockgpu`. **Expected files or evidence:** terminal output or the paths named below. For planning, use the per-stage budget in the quickstart.

```bash
unidock --receptor dock/receptor.pdbqt --gpu_batch dock/gpu_sdfprep_202601/*.sdf  --config dock/box.txt --scoring vina --search_mode balance --keep_nonpolar_H  --num_modes 20 --seed 202601 --dir dock/gpu_sdf_202601  > dock/gpu_sdf_202601/unidock.log 2>&1
find dock/gpu_sdf_202601 -maxdepth 1 -type f -name '*_out.sdf' -print
```

**Environment:** `docktools`. **Expected files or evidence:** terminal output or the paths named below. For planning, use the per-stage budget in the quickstart.

```bash
cp dock/gpu_sdf_202601/*_out.sdf "$run_dir/docked_poses.sdf"
cd "$run_dir"
conda activate docktools
obabel docked_poses.sdf -ocan
```

Before extracting a pose, verify its provenance and score. If it came from a PDBQT export, confirm the correspondence between its SDF record and PDBQT `MODEL`. The example selects record 1.

**Environment:** `docking-gromacs`. **Expected files or evidence:** terminal output or the paths named below. For planning, use the per-stage budget in the quickstart.

```bash
obabel docked_poses.sdf -f 1 -l 1 -O lig_pose.sdf
obabel state_original.sdf -ocan
obabel lig_pose.sdf -ocan
```

<a name="legacy-adt-handoff"></a>

### B. Template-based recovery of legacy ADT poses

Save the original SDF for the same microstate as `state_original.sdf` and the legacy Vina output as `selected_run.pdbqt`. Establish a one-to-one atom map from the preparation records, original ADT input, and atom identities. Verify heavy-atom elements, connectivity, and identifiers together. If the original chemical template, atom mapping, or stereochemistry remains uncertain, prepare a new input and redock with route A.

This example uses MODEL 1. Change it to the verified model. The columns are PDBQT serial, coordinates (Å), and AutoDock atom type. For an AutoDock4 `.dlg`, extract the selected pose first. If a single pose has no MODEL record, confirm its contents and extract that structure explicitly.

**Environment:** `Bash`. **Expected files or evidence:** terminal output or the paths named below. For planning, use the per-stage budget in the quickstart.

```bash
grep -E '^MODEL|^REMARK VINA RESULT' selected_run.pdbqt
model=1
awk -v model="$model" '
  $1 == "MODEL" { selected = ($2 == model); next }
  $1 == "ENDMDL" { selected = 0; next }
  selected && /^(ATOM  |HETATM)/ && $NF !~ /^(H|HD|HS)$/ {
    printf "%d\t%.3f\t%.3f\t%.3f\t%s\n",
      substr($0, 7, 5), substr($0, 31, 8), substr($0, 39, 8), substr($0, 47, 8), $NF
  }
' selected_run.pdbqt > pose_heavy.tsv
test -s pose_heavy.tsv && cat pose_heavy.tsv
```

Save the verified mapping as `atom_map.tsv` with two columns and no header. Column 1 is the **one-based** heavy-atom index after RDKit removes ordinary hydrogens from the source SDF. Column 2 is the atom serial in the selected PDBQT MODEL. Use these commands to inspect the template indices and elements.

**Environment:** `docktools`. **Expected files or evidence:** terminal output or the paths named below. For planning, use the per-stage budget in the quickstart.

```bash
conda activate docktools
python - <<'RDKIT'
from rdkit import Chem

template, = Chem.SDMolSupplier("state_original.sdf", removeHs=True)
for atom in template.GetAtoms():
    print(atom.GetIdx() + 1, atom.GetSymbol())
RDKIT
```

Run the following commands after reviewing the atom map. For the organic ligands covered here, RDKit retains the template's molecular graph, inserts the docked heavy-atom coordinates, and adds hydrogens. Resolve any disagreement between the template and stereochemistry assigned from the recovered 3D coordinates before continuing. [RDKit stereochemistry API](https://www.rdkit.org/docs/source/rdkit.Chem.rdmolops.html#rdkit.Chem.rdmolops.AssignStereochemistryFrom3D)

**Environment:** `docking-gromacs`. **Expected files or evidence:** terminal output or the paths named below. For planning, use the per-stage budget in the quickstart.

```bash
python - <<'RDKIT'
from math import dist
from pathlib import Path
from rdkit import Chem

template, = Chem.SDMolSupplier("state_original.sdf", removeHs=True)
assert template is not None and all(a.GetAtomicNum() > 1 for a in template.GetAtoms())
mapped_rows = [line.split() for line in Path("atom_map.tsv").read_text().splitlines() if line.strip()]
pose_rows = [line.split() for line in Path("pose_heavy.tsv").read_text().splitlines() if line.strip()]
mapping = {int(idx) - 1: int(serial) for idx, serial in mapped_rows}
coords = {int(serial): (float(x), float(y), float(z)) for serial, x, y, z, _ in pose_rows}
assert len(mapped_rows) == len(mapping) == template.GetNumAtoms()
assert len(pose_rows) == len(coords) == len(mapping)
assert set(mapping) == set(range(template.GetNumAtoms()))
assert len(set(mapping.values())) == len(mapping) and set(mapping.values()) == set(coords)

pose = Chem.Mol(template)
conf = pose.GetConformer()
assert conf.Is3D()
for idx, serial in mapping.items():
    conf.SetAtomPosition(idx, coords[serial])

pose = Chem.AddHs(pose, addCoords=True)
perceived = Chem.Mol(pose)
Chem.AssignStereochemistryFrom3D(perceived, replaceExistingTags=True)
assert Chem.MolToSmiles(Chem.RemoveHs(perceived)) == Chem.MolToSmiles(template)
assert Chem.GetFormalCharge(pose) == Chem.GetFormalCharge(template)

with Chem.SDWriter("lig_pose.sdf") as writer:
    writer.write(pose)
saved, = Chem.SDMolSupplier("lig_pose.sdf", removeHs=False)
saved_conf = saved.GetConformer()
errors = []
for idx, serial in mapping.items():
    p = saved_conf.GetAtomPosition(idx)
    errors.append(dist((p.x, p.y, p.z), coords[serial]))
assert max(errors) <= 0.02, max(errors)
print(f"Maximum mapped heavy-atom position difference: {max(errors):.4f} Å")
RDKIT
```

`0.02 Å` is the file-transfer tolerance used here. Archive the source SDF, ADT input, model number, and atom map. Use `lig_pose.sdf` after the checks pass.

### Pose and chemical-identity validation

In `docktools`, load the source and recovered SDF records in Python. Compare their canonical isomeric SMILES and formal charges. RDKit removes ordinary explicit hydrogens in memory for this comparison. The SDF used for parameterization retains explicit hydrogens and in-place coordinates. Resolve parsing or identity discrepancies before proceeding.

**Environment:** `docking-gromacs`. **Expected files or evidence:** terminal output or the paths named below. For planning, use the per-stage budget in the quickstart.

```bash
python
```

```python
from rdkit import Chem

source = Chem.SDMolSupplier("state_original.sdf")[0]
pose = Chem.SDMolSupplier("lig_pose.sdf")[0]
Chem.MolToSmiles(source, isomericSmiles=True) == Chem.MolToSmiles(pose, isomericSmiles=True)
Chem.GetFormalCharge(source) == Chem.GetFormalCharge(pose)
exit()
```

**Check.** Check the recovered molecular graph, bond orders, stereochemistry, and integer net charge against the source SDF. Compare mapped heavy-atom coordinates in the original receptor frame for the selected `MODEL`. Regenerate candidates with route A if the pose or chemical identity cannot be established. Proceed to ligand parameterization in step 06 once these checks pass. [Meeko export in the Vina tutorial](https://autodock-vina.readthedocs.io/en/latest/docking_basic.html#exporting-results-to-sdf)

[Back to contents](../README.md#contents)

## Choose a pose handoff and a search profile

| Observation | Route | Acceptance |
| --- | --- | --- |
| Selected PDBQT model has complete Meeko SMILES and atom-index metadata | A: mapped Meeko SDF export | Verify graph, stereochemistry, formal charge and fixed-frame coordinates |
| Meeko metadata absent or inconsistent | B: original SDF plus a unique reviewed atom map | Verify the same four properties and preserve the mapping table |
| Mapping ambiguous or chemistry fails review | Reprepare and redock from the original microstate | Apply route A to the newly generated pose |

Use Uni-Dock `fast` for broad triage, `balance` for follow-up ranking, and `detail` for a small reviewed set, where the installed 1.2.0 binary supports those modes. Record the installed help output, seed and search mode and calibrate against a known pose before screening. Use [batch manifest and restart parameters](../examples/README.md) and the [box template](../config/box.template.txt) for persistent per-job files. A blind box should cover the intended receptor region and be reviewed in PyMOL; define all dimensions in Å.
