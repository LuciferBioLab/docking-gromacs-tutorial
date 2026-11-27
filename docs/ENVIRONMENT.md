# Environment and reference redocking

**English** · [简体中文](ENVIRONMENT.zh-CN.md)

Languages synchronized 2026-11-28. [Verified workflow commit](https://github.com/LuciferBioLab/docking-gromacs-tutorial/commit/d139618900e79f0dc186d3bb64fbe5be4cc25914).

[Repository home](../README.md#contents)

<a name="setup"></a>

## 01. Environment setup and installation

- **Input** Linux/WSL2 system
- **Outputs** versioned environment
- **If a step fails** report solver errors before preparing structures

### Linux server

Use the Miniforge installer for your operating system and architecture, and verify it against the published release information. Command blocks assume Bash and the project root unless specified. The examples use the syntax of Vina 1.2.7, Uni-Dock 1.2.0, and GROMACS 2026.3. If Miniforge is already available, proceed to environment creation. [Miniforge Releases](https://github.com/conda-forge/miniforge/releases)

Example for Linux x86-64. Use the installer for your architecture.

**Environment:** `Bash`. **Expected files or evidence:** terminal output or the paths named below. For planning, use the per-stage budget in the quickstart.

```bash
bash Miniforge3-Linux-x86_64.sh -b -p "$HOME/miniforge3"
source "$HOME/miniforge3/etc/profile.d/conda.sh"
```

**Environment:** `docktools, ligandtools, gmx-cpu`. **Expected files or evidence:** terminal output or the paths named below. For planning, use the per-stage budget in the quickstart.

```bash
conda create -n docktools --override-channels -c conda-forge python=3.11 vina=1.2.7 meeko rdkit gemmi openbabel
conda create -n ligandtools --override-channels -c conda-forge ambertools acpype openbabel
conda create -n gmx-cpu --override-channels -c conda-forge gromacs=2026.3

conda activate docktools
vina --version
mk_prepare_receptor.py --help
mk_prepare_ligand.py --help
mk_export.py --help

conda activate ligandtools
command -v antechamber parmchk2 tleap sqm acpype obabel
acpype -h

conda activate gmx-cpu
gmx --version
```

Install Molscrub in `docktools` to enumerate protomers and tautomers. Run `scrub.py --help` to confirm the command-line interface and `python -m pip check` to verify dependencies. If dependency resolution fails, consult upstream installation instructions and document compatible versions. [Molscrub installation](https://github.com/forlilab/molscrub) · [Vina releases](https://github.com/forlilab/AutoDock-Vina/releases) · [conda-forge GROMACS](https://anaconda.org/conda-forge/gromacs)

**Environment:** `docktools`. **Expected files or evidence:** terminal output or the paths named below. For planning, use the per-stage budget in the quickstart.

```bash
conda activate docktools
python -m pip install molscrub
python -m pip check
scrub.py --help
```

### NVIDIA CUDA docking environment

Run these commands on a Linux GPU node or in WSL2 after completing the Windows setup below. The example uses the conda-forge Linux x86-64 build of Uni-Dock 1.2.0. Verify that the NVIDIA driver supports the package's CUDA runtime. The package installs its runtime dependencies. Source builds use the `nvcc` compiler. [Uni-Dock release notes](https://github.com/dptech-corp/Uni-Dock/releases) · [conda-forge builds](https://anaconda.org/conda-forge/unidock/files) · [NVIDIA CUDA compatibility](https://docs.nvidia.com/deploy/cuda-compatibility/latest/minor-version-compatibility.html)

**Environment:** `dockgpu`. **Expected files or evidence:** terminal output or the paths named below. For planning, use the per-stage budget in the quickstart.

```bash
nvidia-smi
conda create -n dockgpu --override-channels -c conda-forge 'unidock=1.2.0'
conda activate dockgpu
command -v unidock
unidock --help
conda list --show-channel-urls unidock
```

The CUDA version reported by `nvidia-smi` indicates driver support. Use `nvcc --version` to query a locally installed toolkit. If installation or execution fails because of CUDA compatibility, match the package build to the node's NVIDIA driver. Verify installation with the help command and verify GPU execution with the reference docking case in step 02. [NVIDIA nvidia-smi documentation](https://docs.nvidia.com/deploy/nvidia-smi/)

### GROMACS CUDA build

Verify GPU visibility with `nvidia-smi`. For a source build, select CUDA Toolkit, compiler, and CMake versions supported by the GROMACS installation guide, then run the commands from the extracted source tree. If a cluster module is available, load it and verify its GROMACS version and GPU backend. [GROMACS website](https://www.gromacs.org/) · [2026.3 build guide](https://manual.gromacs.org/2026.3/install-guide/index.html) · [GPU performance guide](https://manual.gromacs.org/documentation/current/user-guide/mdrun-performance.html)

**Environment:** `docking-gromacs`. **Expected files or evidence:** terminal output or the paths named below. For planning, use the per-stage budget in the quickstart.

```bash
nvidia-smi
nvcc --version
cmake --version
cmake -S . -B build-cuda -DGMX_GPU=CUDA -DGMX_BUILD_OWN_FFTW=ON  -DREGRESSIONTEST_DOWNLOAD=ON -DCMAKE_INSTALL_PREFIX="$HOME/opt/gromacs-2026.3-cuda"
cmake --build build-cuda --parallel 4
cmake --build build-cuda --target check
cmake --install build-cuda

source "$HOME/opt/gromacs-2026.3-cuda/bin/GMXRC"
gmx --version
```

Before starting MD, verify which GROMACS executable is on `PATH` with `command -v gmx`. Run shared-cluster jobs inside a scheduler allocation and match the thread count to the allocated resources. [Slurm documentation](https://slurm.schedmd.com/documentation.html)

### Windows + WSL2

Check the WSL configuration in PowerShell. If WSL is absent, install it with the second command block and restart if prompted. Run the Linux commands in Ubuntu under WSL. Store the simulation project and trajectory files on the Linux filesystem, for example in `~/docking-md-workshop`. [Microsoft WSL installation](https://learn.microsoft.com/windows/wsl/install) · [WSL filesystems](https://learn.microsoft.com/windows/wsl/filesystems)

**Environment:** `PowerShell`. **Expected files or evidence:** terminal output or the paths named below. For planning, use the per-stage budget in the quickstart.

```powershell
wsl --status
wsl -l -v
```

**Environment:** `PowerShell`. **Expected files or evidence:** terminal output or the paths named below. For planning, use the per-stage budget in the quickstart.

```powershell
wsl --install -d Ubuntu
```

Install the WSL-capable NVIDIA driver on the **Windows host** and check `nvidia-smi` from WSL Bash. Then install Uni-Dock CUDA as shown above or choose the CPU route. For a source build, follow NVIDIA's WSL instructions and select a Toolkit package without a bundled Linux display driver. Native Windows Vina 1.2.7 is covered in step 04A and CUDA docking in step 04B. [NVIDIA CUDA on WSL](https://docs.nvidia.com/cuda/wsl-user-guide/index.html) · [Vina batch syntax on Windows](https://autodock-vina.readthedocs.io/en/latest/docking_in_batch.html)

<a name="benchmark"></a>

## 02. Reference redocking benchmark

- **Input** Checksummed public inputs
- **Outputs** redocked poses and RMSD
- **If a step fails** review chemical identity and box geometry if redocking misses the reference

Use the Scripps c-Abl–imatinib example (PDB **1IEP**) as a reference redocking benchmark. Use the checksummed repository copy of the Scripps inputs in the quickstart. The search box is defined in the example receptor's coordinate frame.<sup>[2](REFERENCES.md#ref-2),[3](REFERENCES.md#ref-3),[4](REFERENCES.md#ref-4)</sup> [Official walkthrough](https://autodock-vina.readthedocs.io/en/latest/docking_basic.html) · [Upstream example files](https://github.com/forlilab/AutoDock-Vina/tree/develop/example/basic_docking) · [RCSB 1IEP](https://www.rcsb.org/structure/1IEP)

**Structure provenance and validation.** Record the structure DOI and reference ligand instance. Report the atom correspondence and symmetry treatment used for redocking RMSD.<sup>[5](REFERENCES.md#ref-5)</sup> [1IEP structure DOI](https://doi.org/10.2210/pdb1IEP/pdb) · [DockRMSD methodology](https://doi.org/10.1186/s13321-019-0362-7)

Run the manual comparison from the repository root. The ordering repair is limited to this checksummed fixture. Prefer the [verified five-command quickstart](QUICKSTART.md#dock) for the default CPU settings.

**Environment:** `docktools`. **Expected files or evidence:** `1iep_ligand.pdbqt`. For planning, use the per-stage budget in the quickstart.

```bash
conda activate docktools
python scripts/example_io.py order-example examples/1iep/1iep_receptorH.pdb 1iep_receptor_ordered.pdb
mk_prepare_receptor.py --read_pdb 1iep_receptor_ordered.pdb -o 1iep_receptor -p -v  --box_size 20 20 20 --box_center 15.190 53.903 16.917
mk_prepare_ligand.py -i examples/1iep/1iep_ligand.sdf -o 1iep_ligand.pdbqt
```

**CPU: AutoDock Vina**

**Environment:** `docking-gromacs`. **Expected files or evidence:** `1iep_docked.pdbqt`, `1iep_docked.sdf`. For planning, use the per-stage budget in the quickstart.

```bash
vina --receptor 1iep_receptor.pdbqt --ligand 1iep_ligand.pdbqt  --config 1iep_receptor.box.txt --scoring vina --cpu 4 --seed 202601  --exhaustiveness 32 --out 1iep_docked.pdbqt
mk_export.py 1iep_docked.pdbqt -s 1iep_docked.sdf
```

**GPU: Uni-Dock CUDA**

**Environment:** `dockgpu`. **Expected files or evidence:** terminal output or the paths named below. For planning, use the per-stage budget in the quickstart.

```bash
conda activate dockgpu
mkdir 1iep_gpu
unidock --receptor 1iep_receptor.pdbqt --gpu_batch 1iep_ligand.pdbqt  --config 1iep_receptor.box.txt --scoring vina --search_mode balance  --num_modes 20 --seed 202601 --dir 1iep_gpu > 1iep_gpu/unidock.log 2>&1
tail -25 1iep_gpu/unidock.log
find 1iep_gpu -maxdepth 1 -type f -name '*.pdbqt' -print
```

For the GPU run, apply the pose export and verification procedure in step 05. Confirm successful completion using the pose file, run log, and observed GPU activity.

**Check.** Confirm that the PDBQT contains pose and score records and that the recovered SDF is readable. Evaluate each engine's pose recovery and key contacts against the co-crystal reference. Calculate symmetry-aware ligand heavy-atom root-mean-square deviation (RMSD) in a common receptor frame without independently fitting the ligands. Approximately 2 Å is a conventional reference for pose recovery. A separate BioExcel tutorial covers MD complex setup. [Scripps expected results](https://autodock-vina.readthedocs.io/en/latest/docking_basic.html#expected-results) · [BioExcel complex setup](https://github.com/bioexcel/biobb_wf_protein-complex_md_setup)

**Quantitative redocking.** In the RCSB 1IEP entry, download the STI instance coordinates as SDF for the matching chain and save them as `1iep_crystal_ligand.sdf`. Verify the ligand conformer and common receptor frame in a structure viewer. After confirming chemical identity, use Open Babel `obrms` to calculate per-pose heavy-atom RMSD in Å. It searches equivalent correspondences by heavy-atom connectivity. Leave `-m` unset to preserve each pose in the receptor frame.<sup>[6](REFERENCES.md#ref-6)</sup> [RCSB 1IEP](https://www.rcsb.org/structure/1IEP) · [Open Babel obrms](https://github.com/openbabel/openbabel/blob/master/tools/obrms.cpp)

**Environment:** `docktools`. **Expected files or evidence:** terminal output or the paths named below. For planning, use the per-stage budget in the quickstart.

```bash
conda activate docktools
obabel examples/regression/1iep/crystal_ligand.sdf -ocan
obabel 1iep_docked.sdf -ocan
obrms examples/regression/1iep/crystal_ligand.sdf 1iep_docked.sdf | tee 1iep_cpu_redocking_rmsd.txt
```

Export the GPU poses to `1iep_gpu_docked.sdf` using step 05. Compare the top-ranked pose and other leading poses by RMSD and key contacts. Record separately whether the search recovered the reference pose and whether the scoring function ranked it first.

If a reference-like pose is sampled but ranked poorly, report its rank and redocking RMSD and review pocket contacts and ligand microstate. [Redocking troubleshooting](TROUBLESHOOTING.md#docking-errors)

**Environment:** `docking-gromacs`. **Expected files or evidence:** terminal output or the paths named below. For planning, use the per-stage budget in the quickstart.

```bash
obabel 1iep_gpu_docked.sdf -ocan
obrms examples/regression/1iep/crystal_ligand.sdf 1iep_gpu_docked.sdf | tee 1iep_gpu_redocking_rmsd.txt
```

[Back to contents](../README.md#contents)
