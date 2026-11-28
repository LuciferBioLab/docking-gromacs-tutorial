# Quickstart and verification record

**English** · [简体中文](QUICKSTART.zh-CN.md)

Languages synchronized 2026-11-29. [Verified workflow commit](https://github.com/LuciferBioLab/docking-gromacs-tutorial/commit/d139618900e79f0dc186d3bb64fbe5be4cc25914).

[Repository home](../README.md#contents)

Use Bash on Linux or in a WSL2 Linux distribution. Run repository commands from a local checkout containing `Makefile` and `examples/`. On Windows, use PowerShell for `wsl -l -v`, then open the Linux distribution and keep the working directory on its Linux filesystem. [Linux and WSL2 setup](ENVIRONMENT.md#setup)

If you need a checkout, use the following commands with Git and GNU Make available in your Linux shell.

```bash
git clone https://github.com/LuciferBioLab/docking-gromacs-tutorial.git
cd docking-gromacs-tutorial
```

| What you have | Start here |
| --- | --- |
| A receptor and ligand, or no prepared files yet | [Dock only](#dock) |
| A reviewed docked pose or a prepared MD system | [Run MD from an existing pose](#existing-pose) |
| A trajectory, or precomputed series and structures | [Analyze or make figures](#existing-trajectory) |

<a name="dock"></a>

## Dock and check a public co-crystal

Install once, then run the public 1IEP CPU example. The split `docktools` environment below installs the pinned docking tools for steps 01–05. If you already have the complete `docking-gromacs` environment, activate it and run the three commands after activation.

```bash
conda create -n docktools --override-channels -c conda-forge python=3.11 vina=1.2.7 \
  meeko=0.8.0 rdkit=2026.03.1 gemmi=0.7.5 openbabel=3.2.1
conda activate docktools
make fixtures
make dock RUN=runs/1iep-dock THREADS=4
bash scripts/check_05.sh runs/1iep-dock
```

`RUN` chooses a new isolated directory. `THREADS` is the requested per-job CPU thread allocation. The docking profile uses Vina `--exhaustiveness 8` for a short reference search, `--num_modes 5` to cap output, and `--seed 202601` by default to record the sampling seed. Vina may emit fewer than five modes. For a sensitivity check, compare exhaustiveness 8, 16, and 32 and several recorded seeds with all other inputs fixed.

In `runs/1iep-dock/`, expected files include `dock/docked.pdbqt`, `dock/lig_pose.sdf`, `dock/redocking.csv`, and `logs/vina.log`. The pinned 1IEP ligand is **+1**, which the chemistry checks enforce. The result below was observed with Vina 1.2.7, Meeko 0.8.0, Open Babel 3.2.1, four allocated CPU threads and seed 202601.

```text
PASS stage 04
Selected SDF record 1 of 3; identity and formal charge +1 match.
Top-1 RMSD 0.350 Å; best sampled RMSD 0.350 Å.
PASS stage 05
```

The top Vina score was −13.270 kcal/mol. This is a docking score. RMSD compares symmetry-equivalent heavy-atom matches to the archived ligand instance in the original receptor frame, without separately fitting the ligands and without aligning the receptor a second time. The three poses gave 0.350, 12.304, and 12.192 Å. The CI check requires at least one sampled pose at or under 2 Å. Exact floating-point results may vary with the executable and platform.

[Input provenance](../examples/1iep/PROVENANCE.md) · [Three crystal references](../examples/regression/PROVENANCE.md) · [Regression RMSD script](../scripts/redocking_rmsd.py)

For your own inputs, follow [receptor and ligand preparation](DOCKING.md#local-inputs) and the [CPU, CUDA or OpenCL docking steps](DOCKING.md#batch-docking). Use a search box defined for the receptor in Å. Keep the source SDF and raw PDBQT together with the log and selected pose record. If the fixture fails, start with the first error under `runs/1iep-dock/logs/` and the [docking error index](TROUBLESHOOTING.md#docking-errors).

<a name="existing-pose"></a>

## Run MD from an existing docking pose

Use Linux or WSL2 Bash. From a repository checkout, create or activate the full CPU environment if you need AmberTools, ACPYPE, RDKit and GROMACS together. If you use the [separate environments](ENVIRONMENT.md#setup), follow the activation commands for each stage.

Bring the reviewed MD-ready protein PDB and a single-record pose SDF with verified bond orders, stereochemistry, integer charge and docked heavy-atom coordinates in the **same receptor frame**. For a PDBQT-only pose, first recover the SDF using [step 05](DOCKING.md#pose-handoff). Preserve the source ligand chemistry and atom map. Use a separate directory for each force field, pose and replicate. Replace the illustrative source paths below before running.

```bash
conda env create -f environment.yml
conda activate docking-gromacs
```

```bash
protein='/path/to/reviewed_protein.pdb'
pose='/path/to/verified_pose.sdf'
run='runs/study01/amber_pose01_rep01'

test -s "$protein" && test -s "$pose" &&
  mkdir -p -- "$(dirname -- "$run")" && mkdir -- "$run" &&
  cp -- "$protein" "$run/protein.pdb" &&
  cp -- "$pose" "$run/lig_pose.sdf" &&
  cd -- "$run"
```

| Entry | Handoff |
| --- | --- |
| Reviewed pose SDF + protein PDB | [Parameterize](SYSTEM_SETUP.md#topology) with AMBER or CHARMM. Keep the net ligand charge in units of e and verify Å-to-nm conversions. [Assemble](SYSTEM_SETUP.md#complex-assembly) to obtain `complex_raw.gro` and `topol.top` plus its includes. |
| Matching assembled system and topology | Start at the applicable commands in [system preparation and equilibration](SIMULATION.md#equilibration) using the [stage MDPs](SYSTEM_SETUP.md#simulation). The box setup starts from an unsolvated `complex_raw.gro`. An already solvated or equilibrated system enters at its reviewed stage, using its own matching topology, coordinates, groups and checkpoint. |
| Reviewed NPT or pilot endpoint | Use the same-stage GRO and CPT in [production preparation](SIMULATION.md#production). Verify the compiled TPR and topology, then follow the [server handoff](SIMULATION.md#server-handoff). |

If preprocessing fails, read the first `grompp` error. Check charge, atom order, topology includes and restraint references in [parameterization and topology troubleshooting](TROUBLESHOOTING.md#topology-errors). Review [complex systems](TROUBLESHOOTING.md#complex-systems) before using this soluble-system example for a multichain pocket, nonstandard residue, metal, cofactor, or membrane assembly.

<a name="existing-trajectory"></a>

## Analyze an existing trajectory or make figures

Prepare a fresh analysis directory with a full-system XTC and its matching TPR, plus an index for that atom order. Step 11 uses the local names `md.xtc`, `md.tpr` and `index.ndx`. Use the existing GROMACS environment for calculations. If installing just for this route, install GROMACS 2026.3 from [the CPU setup](ENVIRONMENT.md#setup). Review the [input and index checks](ANALYSIS.md#analysis) before imaging or calculating ligand RMSD. A stripped trajectory needs a reference and groups for that exact subset and order. For precomputed XVG or a matching structure file, go directly to the [Python plotting](ANALYSIS.md#python-figures) or [PyMOL structure rendering](ANALYSIS.md#pymol-image-export).

The [published 1IEP v0.1.0 archive](https://github.com/LuciferBioLab/docking-gromacs-tutorial/releases/tag/v0.1.0) is suitable for plotting the included ligand RMSD and viewing `analysis/complex.pdb`. It contains the smoke XTC but omits the TPR and index required for the complete trajectory analysis. Keep the reported time and distance units when plotting archived XVG values.

<a name="quickstart-md"></a>

## Run the public 1IEP MD teaching example

Use the complete `docking-gromacs` environment from above and return to the repository root first. The smoke and 1 ns commands create new directories. Choose a new name for each run.

```bash
bash scripts/run_example.sh --dry-run smoke runs/1iep-smoke
make smoke RUN=runs/1iep-smoke THREADS=4
make quickstart RUN=runs/1iep-1ns THREADS=4
```

Run the smoke or the 1 ns profile according to your goal. The smoke profile performs 2 ps of production after brief numerical preflight, and the 1 ns profile uses 50 ps NVT and 100 ps NPT. Ten minutes is a hands-on onboarding target after installation. Actual wall time includes charge assignment, equilibration, and MD and may be substantially longer. These stages demonstrate handoff and data integrity. A research run requires a separate equilibration and sampling decision.

| Goal | Required | Can omit for that goal |
| --- | --- | --- |
| Docking only | Vina, Meeko, RDKit, Open Babel, prepared receptor and ligand, box | GROMACS, AmberTools, production, plotting |
| MD with a reviewed docked pose | Original ligand chemistry, verified coordinates, chosen force field, GROMACS | Redocking only if provenance and atom mapping are already validated |
| Analyze or make figures | Matching trajectory, topology or reference structure, and index; choose the analysis tool | Docking, parameterization and rerunning MD if inputs are consistent |

| Stage | Inputs → expected output | Planning time and disk |
| --- | --- | --- |
| 01 | `environment.yml` → tool commands available | Initial solve/download can take minutes; allow about 5 GiB including cache |
| 02 | Public PDB, SDF and checksum → `OK` | Seconds, under 2 MiB |
| 03 | Ordered PDB + SDF → receptor and ligand PDBQT | Seconds in 1IEP, under 2 MiB |
| 04 | PDBQT + box → `docked.pdbqt` with Vina scores | Seconds to minutes; under 2 MiB for this small run |
| 05 | PDBQT + source graph → `lig_pose.sdf`, `redocking.csv` | Seconds; under 1 MiB |
| 06 | Validated MOL2 + net charge → ACPYPE GRO/ITP | Minutes for AM1-BCC; allow several MiB for temporary files |
| 07 | Protein GRO + ligand GRO/ITP → `complex.gro`, `topol.top` | Seconds to minutes, a few MiB |
| 08 | Profile + seed → stage MDP files | Seconds; small text files |
| 09 | Solute + matching parameter files → `npt.gro`, `npt.cpt` | Depends on solvation and equilibration length; reserve tens of MiB for the smoke |
| 10 | NPT endpoint → `md.tpr`, `md.xtc`, `md.cpt` | Measure ns/day on the actual node; XTC size scales with output frames |
| 11 | Matched full-system XTC/TPR → `ligand-rmsd.xvg`, `complex.pdb` | Seconds for smoke; reimaged XTCs can require two extra copies |
| 12 | Validated outputs → `provenance/outputs.sha256` | Seconds for smoke; grows with files hashed |

If any stage fails, read `logs/<operation>.log` for the first error and use the relevant `scripts/check_XX.sh`. To inspect a manual step from another shell, re-enter the intended replicate directory and re-export its variables. [File map and checklist](WORKFLOW.md#toolchain) · [Triage order](TROUBLESHOOTING.md#triage)

<a name="version-matrix"></a>

## Version and platform matrix

Recorded on **2026-11-28**. The reproducibility target is the same repository snapshot as these commands. Record `git rev-parse HEAD` and the environment lock hash for every published run.

| Component | Version or route | Verification |
| --- | --- | --- |
| Vina | 1.2.7 | 1IEP redock |
| Meeko | 0.8.0 | Receptor and ligand preparation, mapped export |
| RDKit | 2026.03.1 | SDF identity and mapping checks |
| Open Babel | 3.2.1 | Format round trip and fixed-frame RMSD |
| AmberTools / ACPYPE | 26.0 / 2023.10.27 | 1IEP AM1-BCC and GAFF2 files |
| GROMACS | 2026.3, conda-forge thread-MPI build | Validation status below |
| Uni-Dock | 1.2.0, CUDA route | Versioned manual; no CUDA device in this validation |
| AutoDock-Vina-GPU | 2.1, OpenCL route | [Upstream source reviewed](DOCKING.md#vina-gpu-opencl); GPU run pending |
| CGenFF | 5.0 cutoff example | Upstream parameter and conversion documentation |

The environment YAML specifies the direct dependencies. The [Linux x86-64 lock](../environment/linux-64.explicit.txt) pins the exact package builds.

```bash
(cd environment && sha256sum -c SHA256SUMS)
conda create -n docking-gromacs-locked --file environment/linux-64.explicit.txt
```

| Platform | Starting budget for orientation | Limits |
| --- | --- | --- |
| CPU, Linux/WSL2 | 2–4 CPU cores, 8 GiB RAM, 8 GiB free SSD | Teaching example; measure performance for your system |
| CUDA workstation | 4+ CPU cores, 16 GiB RAM, 8 GiB VRAM as a planning starting point | Actual Uni-Dock batch size and MD atom count determine memory demand |
| Cluster | Start with the site-supported binary and local scratch | Match ranks and OpenMP threads to scheduler allocation |

<a name="validation-boundary"></a>

## Validation boundary

The full 01–12 CPU smoke passed using four CPU threads. Production was 2 ps. The run produced the prepared topology, readable TPR, CPT, XTC, and a protein-aligned ligand RMSD series. The short run reports **14.36 ns/day** for production, which is an observed smoke rate that includes short-run overhead. Charge assignment and preparation time are additional. See [verification outputs](../examples/expected/README.md).

| Workflow | Evidence and status |
| --- | --- |
| 1 ns CPU quickstart | Preparation and equilibration completed. The last production log record was 96.6 ps. The run ended before the target and left no production checkpoint. |
| Uni-Dock, Vina-GPU and GROMACS CUDA | Setup documented. No GPU throughput measurements. |
| CHARMM and the paired AMBER/CHARMM comparison | Parameterization and comparison design documented. Full runs and the paired comparison remain unverified. |
| CHARMM MM/PBSA | Settings matched to the upstream 1.7.0 example. Independent reproduction pending. [CHARMM endpoint setup](RESEARCH.md#free-energy) |

For the packaged example, stages 09 and 10 check that the final step in the dynamics log matches `init-step + nsteps` from the processed MDP. A normal-looking footer can also appear at an early stop.

Check hashes against the supplied files. Numerical trajectories should be interpreted with the software, inputs and settings recorded. Bitwise equality across CPU/GPU runs is not the scientific acceptance criterion. [Validation and sampling](RESEARCH.md#sampling)

<a name="production-budget"></a>

## 100 ns storage and time budget

At 2 fs (`dt = 0.002` ps), 100 ns takes 50,000,000 integration steps. For a fresh run starting at step 0, with a positive output stride `S` in steps, the complete XTC contains `ceil(nsteps / S) + 1` frames. The first and last coordinates are written, so the last interval can be shorter when the end step falls between regular writes. Use actual trajectory timestamps for frame-based analysis. [GROMACS 2026.3 coordinate-output settings](https://manual.gromacs.org/2026.3/user-guide/mdp-options.html#mdp-nstxout-compressed)

| Output interval | `nstxout-compressed` | Complete frames | Estimated XTC per replica |
| --- | ---: | ---: | ---: |
| 10 ps | 5,000 | 10,001 | 1.90 GiB |
| 30 ps | 15,000 | 3,335 | 0.63 GiB |

The estimates use 2,245,348 bytes across 11 full-system frames from the completed public CPU smoke (55,134 atoms, `compressed-x-precision = 1000`). For your own system, multiply the measured bytes per frame by the expected frame count and number of replicas. Reserve space separately for reimaged copies, logs, checkpoints, energy files and any uncompressed trajectory. Budget time as production ns divided by the measured ns/day. At 13.82 ns/day from the short public CPU benchmark, 100 ns would take about 7.24 days per replica, plus setup and equilibration. These figures are extrapolations from the short CPU reference.


## Measured performance on the public CPU fixture

| Task | Data and settings | Measurement |
| --- | --- | --- |
| Vina redocking | 1IEP, four threads, exhaustiveness 8 | 23 s docking; environment and input preparation excluded |
| AMBER production smoke | 55,134 atoms, four threads, 2 ps | 14.36 ns/day reported by GROMACS |
| CPU benchmark | Same TPR, one thread-MPI rank, four OpenMP threads, 5,000 steps | 13.82 ns/day reported by GROMACS |
| Uni-Dock / GROMACS CUDA | Run on your own allocation | Measurement pending |

The complete 01–12 CPU smoke took about 3 min 16 s, used about 53 MiB including intermediate files, and wrote about 2.14 MiB of compressed production coordinates. The 1 ns stage alone would take about 1 h 44 min at the measured short CPU benchmark rate, plus equilibration and setup. Report medians from repeated equivalent tests for planning. Use the [benchmark script](../scripts/benchmark.sh) and [results table template](../examples/results-template.csv).
