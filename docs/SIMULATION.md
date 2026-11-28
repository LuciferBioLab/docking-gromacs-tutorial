# Equilibration and production

**English** · [简体中文](SIMULATION.zh-CN.md)

Languages synchronized 2026-11-29. [Verified workflow commit](https://github.com/LuciferBioLab/docking-gromacs-tutorial/commit/d139618900e79f0dc186d3bb64fbe5be4cc25914).

[Repository home](../README.md#contents)

<a name="equilibration"></a>

## 09. System setup, energy minimization, and equilibration

- **Input** Box-ready complex and MDPs
- **Outputs** solvated minimized equilibrated system
- **If a step fails** inspect first grompp or dynamics failure

Run from the prepared replicate directory with GROMACS 2026.3 on `PATH`. Check that `complex_raw.gro`, `topol.top`, its local includes, and the stage MDPs are present before boxing. An already solvated system starts from its matching coordinate and topology files at the appropriate later stage.

### Box, solvent, and ions

Use the box command for your force-field route. The examples set an initial solute-to-box boundary distance of 1.2 nm for AMBER and 1.4 nm for CHARMM. Verify solute–image separation for the chosen periodic box and cutoff.

**Environment:** `docking-gromacs`. **Expected files or evidence:** `boxed.gro`. For planning, use the per-stage budget in the quickstart.

```bash
# AMBER
gmx editconf -f complex_raw.gro -o boxed.gro -c -d 1.2 -bt dodecahedron
```

**Environment:** `docking-gromacs`. **Expected files or evidence:** `boxed.gro`. For planning, use the per-stage budget in the quickstart.

```bash
# CHARMM
gmx editconf -f complex_raw.gro -o boxed.gro -c -d 1.4 -bt dodecahedron
```

Check molecule names in the selected force field's `ions.itp`. The example uses `NA` and `CL`; confirm that they match your actual topology.

**Environment:** `docking-gromacs`. **Expected files or evidence:** `solv.gro`, `topol.top`, `ions.tpr`, `ions_processed.top`, `solv_ions.gro`. For planning, use the per-stage budget in the quickstart.

```bash
cp topol.top topol_before_solvation.top
gmx solvate -cp boxed.gro -cs spc216.gro -o solv.gro -p topol.top

gmx grompp -f ions.mdp -c solv.gro -p topol.top -o ions.tpr  -pp ions_processed.top -po ions_out.mdp

cp topol.top topol_before_ions.top
gmx genion -s ions.tpr -o solv_ions.gro -p topol.top  -pname NA -nname CL -neutral -conc 0.15 -seed 202601
```

At the `genion` prompt, select the contiguous water-only group **SOL**. Verify the solvent and ion counts, total charge, and periodic clearance. Additional counterions used for neutralization affect the final ionic strength. The `spc216.gro` file supplies coordinates for a three-site solvent. The topology defines the water model. Use AMBER TIP3P for route A and CHARMM TIP3P with hydrogen Lennard–Jones terms for route B. [GROMACS grompp](https://manual.gromacs.org/current/onlinehelp/gmx-grompp.html) · [GROMACS MD tutorial](https://tutorials.gromacs.org/docs/md-intro-tutorial.html)

### Steepest-descent minimization

**Environment:** `docking-gromacs`. **Expected files or evidence:** `topol.top`, `em.tpr`, `em_processed.top`, `potential.xvg`. Runtime and output size depend on system size and simulated duration.

```bash
gmx grompp -f em.mdp -c solv_ions.gro -p topol.top -o em.tpr  -pp em_processed.top -po em_out.mdp
gmx mdrun -v -deffnm em -nb cpu
gmx energy -f em.edr -o potential.xvg
```

In `gmx energy`, select **Potential**, then type `0` to end the selection. Review minimization termination, energy, and maximum force in `em.log`. The example force criterion is 1,000 kJ mol⁻¹ nm⁻¹. For failed minimizations, diagnose steric clashes, atom order, bonded topology, and parameter assignments.

### Build named index groups

These selections follow the atom order set in step 07: protein first, ligand next, then solvent and ions. Generate the index from `em.tpr` and verify group counts. If the default Backbone or C-alpha name differs, inspect groups with `gmx make_ndx -f em.gro` and adjust the selections.

**Environment:** `docking-gromacs`. **Expected files or evidence:** `em.tpr`, `index.ndx`, `index_review.ndx`. For planning, use the per-stage budget in the quickstart.

```bash
protein_atoms=$(sed -n '2p' protein.gro | tr -d '[:space:]')
ligand_atoms=$(sed -n '2p' ligand.gro | tr -d '[:space:]')
solute_atoms=$((protein_atoms + ligand_atoms))
ligand_start=$((protein_atoms + 1))

gmx select -s em.tpr -on index.ndx -select  "\"System\" all;
   \"Protein\" atomnr 1 to $protein_atoms;
   \"Ligand\" atomnr $ligand_start to $solute_atoms;
   \"Complex\" atomnr 1 to $solute_atoms;
   \"Water_and_ions\" atomnr > $solute_atoms;
   \"Backbone\" group \"Backbone\";
   \"C_alpha\" group \"C-alpha\";
   \"Protein_heavy\" (atomnr 1 to $protein_atoms) and mass > 2.5;
   \"Ligand_heavy\" (atomnr $ligand_start to $solute_atoms) and mass > 2.5"
gmx make_ndx -f em.gro -n index.ndx -o index_review.ndx
```

Exit the index viewer with `q`. Confirm that `Complex` and `Water_and_ions` are disjoint and cover the system, that `Ligand` matches the ligand GRO atom count, and that `Backbone` and `C_alpha` contain protein atoms. Use the original `index.ndx` below.

### NVT → NPT

Select one compute configuration in the current Bash session for equilibration in step 09 and production in step 10. The examples use four OpenMP threads on one node. The CUDA example uses one GPU with a thread-MPI build. Use the site-specific launcher and rank layout for an external-MPI build. Reinitialize the Bash array when restarting from a new shell. [GROMACS runtime performance](https://manual.gromacs.org/documentation/current/user-guide/mdrun-performance.html)

**Environment:** `Bash`. **Expected files or evidence:** terminal output or the paths named below. For planning, use the per-stage budget in the quickstart.

```bash
# CPU
md_backend=(-ntomp 4 -nb cpu -pme cpu)
```

**Environment:** `Bash`. **Expected files or evidence:** terminal output or the paths named below. For planning, use the per-stage budget in the quickstart.

```bash
# NVIDIA GPU, thread-MPI
md_backend=(-ntmpi 1 -ntomp 4 -nb gpu -pme auto)
```

For CUDA, check `nvt.log` and `pilot.log` for device and task assignment. These flags request GPU short-range nonbonded calculations and leave PME placement to GROMACS.

**Environment:** `docking-gromacs`. **Expected files or evidence:** `topol.top`, `nvt.tpr`, `nvt_processed.top`, `temperature.xvg`. Runtime and output size depend on system size and simulated duration.

```bash
gmx grompp -f nvt.mdp -c em.gro -r em.gro -p topol.top -n index.ndx  -o nvt.tpr -pp nvt_processed.top -po nvt_out.mdp
gmx mdrun -v -deffnm nvt "${md_backend[@]}"
gmx energy -f nvt.edr -o temperature.xvg
```

Select **Temperature**. Inspect fluctuations and sustained drift around the set point before proceeding to NPT equilibration.

**Environment:** `docking-gromacs`. **Expected files or evidence:** `topol.top`, `npt.tpr`, `npt_processed.top`, `density.xvg`, `volume.xvg`, `pressure.xvg`. Runtime and output size depend on system size and simulated duration.

```bash
gmx grompp -f npt.mdp -c nvt.gro -t nvt.cpt -r em.gro -p topol.top -n index.ndx  -o npt.tpr -pp npt_processed.top -po npt_out.mdp
gmx mdrun -v -deffnm npt "${md_backend[@]}"
gmx energy -f npt.edr -o density.xvg
gmx energy -f npt.edr -o volume.xvg
gmx energy -f npt.edr -o pressure.xvg
```

Select **Density**, **Volume**, and **Pressure** for the corresponding outputs. Examine temperature, density, and volume for sustained drift. Assess pressure using its time average and fluctuations. Review the logs and structure before the unrestrained short test and pilot.

<a name="production"></a>

## 10. Pilot runs, production, and checkpoint restart

- **Input** Reviewed equilibrium and checkpoint
- **Outputs** production trajectory and checkpoint
- **If a step fails** verify checkpoint and output consistency before resuming

The optional 20 ps smoke test and 1 ns pilot assess numerical stability after releasing position restraints and provide a performance estimate. If equivalent validation is already available, use the validated endpoint for production preparation. Inspect the processed topology for active `[ position_restraints ]` and review LINCS or SETTLE warnings and nonfinite energies. [Simulation troubleshooting](TROUBLESHOOTING.md#simulation-errors)

**Environment:** `docking-gromacs`. **Expected files or evidence:** `topol.top`, `smoke.tpr`, `smoke_processed.top`. For planning, use the per-stage budget in the quickstart.

```bash
gmx grompp -f smoke.mdp -c npt.gro -t npt.cpt -p topol.top -n index.ndx  -o smoke.tpr -pp smoke_processed.top -po smoke_out.mdp
if grep -n -E '^[[:space:]]*\[[[:space:]]*position_restraints[[:space:]]*\]' smoke_processed.top; then
  echo 'Review active position restraints before running this TPR.' >&2
fi
```

**Environment:** `docking-gromacs`. **Expected files or evidence:** terminal output or the paths named below. Runtime and output size depend on system size and simulated duration.

```bash
gmx mdrun -v -deffnm smoke "${md_backend[@]}"
```

To run the pilot directly from accepted NPT, set `PILOT_START=npt` in the block below. Use `smoke` only when the optional smoke run finished and its GRO and CPT passed review. Keep `pilot.mdp` unrestrained as described in [step 08](SYSTEM_SETUP.md#simulation).

**Environment:** `docking-gromacs`. **Expected files or evidence:** `topol.top`, `pilot.tpr`, `pilot_processed.top`. Runtime and output size depend on system size and simulated duration.

```bash
(
  set -e
  PILOT_START=smoke
  test -s "$PILOT_START.gro" && test -s "$PILOT_START.cpt" || exit 1
  gmx grompp -f pilot.mdp -c "$PILOT_START.gro" -t "$PILOT_START.cpt" -p topol.top -n index.ndx  -o pilot.tpr -pp pilot_processed.top -po pilot_out.mdp
  gmx mdrun -v -deffnm pilot "${md_backend[@]}"
  gmx check -f pilot.xtc
  grep -A2 'Performance:' pilot.log
)
```

Compile the production TPR from the selected validated endpoint. The example uses `pilot`. Set it to `npt` for a protocol that starts from an accepted NPT endpoint, and keep the GRO and checkpoint from the same stage. Check the processed MDP, expanded topology, and compiled TPR, and document the choice of starting state.

**Environment:** `docking-gromacs`. **Expected files or evidence:** `topol.top`, `md.tpr`, `md_processed.top`. For planning, use the per-stage budget in the quickstart.

```bash
START=pilot
gmx grompp -f md.mdp -c "$START.gro" -t "$START.cpt" -p topol.top -n index.ndx  -o md.tpr -pp md_processed.top -po md_out.mdp
if grep -n -E '^[[:space:]]*\[[[:space:]]*position_restraints[[:space:]]*\]' md_processed.top; then
  echo 'Review active position restraints before running this TPR.' >&2
fi
grep -Ei '^[[:space:]]*(dt|nsteps|nstxout-compressed|compressed-x-grps)[[:space:]]*=' md_out.mdp
```

<a name="server-handoff"></a>

### Server handoff and production verification

**Before submission.** Archive `md.tpr`, the processed MDP, starting GRO and CPT, `index.ndx`, the top-level topology, and all includes and force-field dependencies. Include software versions, starting-state provenance, and equilibration records. Verify the package on the target server against its checksum manifest, and reconcile the compiled TPR with the processed MDP and topology.

Run the read-only checks in the job directory on the target. If the bundle includes `SHA256SUMS`, verify it first.

**Environment:** `docking-gromacs`. **Expected files or evidence:** `md.tpr`. For planning, use the per-stage budget in the quickstart.

```bash
(
  set -e
  if [ -f SHA256SUMS ]; then
    sha256sum -c SHA256SUMS
  fi
  gmx --version
  gmx dump -s md.tpr > md_tpr_dump.txt
  grep -Ei '^[[:space:]]*(dt|nsteps|init-step|nstxout-compressed|continuation)[[:space:]]*=' md_tpr_dump.txt
)
```

| Check | What to verify |
| --- | --- |
| Run length and output | Verify `nsteps × dt`, coordinate-output interval, atom group, and expected starting step. |
| System and restraints | Compare atom counts, index groups, coupling settings, active position restraints, and intended bond constraints. |
| Starting state | Verify starting GRO/CPT provenance, transferred checksums, velocity handling, and TPR readability on the target. |

Track **validated input, running, and completed production** as separate states. Confirm completion from the job log, actual steps, and trajectory. Use the command below when submitting production. If the TPR cannot be read or a restart cannot append, consult the troubleshooting guide first.<sup>[20](REFERENCES.md#ref-20)</sup> [gmx dump](https://manual.gromacs.org/documentation/current/onlinehelp/gmx-dump.html) · [GROMACS checkpoints and restart](https://manual.gromacs.org/documentation/current/user-guide/managing-simulations.html) · [Server and restart troubleshooting](TROUBLESHOOTING.md#server-errors)

**Environment:** `docking-gromacs`. **Expected files or evidence:** terminal output or the paths named below. Runtime and output size depend on system size and simulated duration.

```bash
gmx mdrun -v -deffnm md "${md_backend[@]}" -cpt 15
```

Before restarting an interrupted run, preserve its outputs and verify that `md.cpt` matches the production TPR, log, and trajectory. Record any device or offload changes. A missing checkpoint makes GROMACS start at the first step in the TPR. The file check below keeps the restart command from running if `md.cpt` is absent or empty. If the checkpoint is unavailable, recover the latest matching checkpoint or record a fresh run from a validated starting state in a separate directory. [GROMACS 2026.3 mdrun](https://manual.gromacs.org/2026.3/onlinehelp/gmx-mdrun.html)

**Environment:** `docking-gromacs`. **Expected files or evidence:** terminal output or the paths named below. Runtime and output size depend on system size and simulated duration.

```bash
(
  set -e
  test -s md.cpt
  ls -lh md.cpt md.tpr md.log md.xtc
  gmx mdrun -v -deffnm md -cpi md.cpt -append "${md_backend[@]}" -cpt 15
)
```

### Extend a production run

After reaching the planned endpoint, run these commands from the same replicate directory to add 10 ns. `-extend` uses ps. Keep the original `md.tpr` and continue from the new TPR with the same `-deffnm md` and latest `md.cpt`. If outputs were renamed, are missing, or fail checksum verification, restore the matching files or use `-noappend` for separate parts as documented. If an extended run is interrupted, pass the extended TPR explicitly when resuming. [GROMACS run management](https://manual.gromacs.org/2026.3/user-guide/managing-simulations.html)

**Environment:** `docking-gromacs`. **Expected files or evidence:** `md.tpr`, `md_extended.tpr`. Runtime and output size depend on system size and simulated duration.

```bash
(
  set -e
  test -s md.cpt
  gmx convert-tpr -s md.tpr -extend 10000 -o md_extended.tpr
  gmx mdrun -v -s md_extended.tpr -deffnm md -cpi md.cpt -append "${md_backend[@]}" -cpt 15
  gmx check -f md.xtc
  tail -25 md.log
)
```

Check the end step and time against the log and trajectory before analysis. For another extension, start from the latest TPR used and retain the input and log for each extension.

### Independent replicates

Run independent replicates in separate directories with distinct NVT `gen-seed` values, for example 202601, 202602, and 202603. Equilibrate and simulate each replicate independently. Select starting poses and controls based on the study design. [MD reliability and reproducibility checklist](https://www.nature.com/articles/s42003-023-04653-0)

[Back to contents](../README.md#contents)
