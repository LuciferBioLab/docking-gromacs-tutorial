# Frequently asked questions

**English** · [简体中文](FAQ.zh-CN.md)

[Repository home](../README.md#contents)

<a name="faq"></a>

## Where do I start?

Use [the quickstart](QUICKSTART.md#dock) if you have no prepared files. For an existing docking pose, begin with [pose transfer](DOCKING.md#pose-handoff). For an existing trajectory, start with [trajectory analysis](ANALYSIS.md#analysis).

## What failed first?

Read the earliest failure in the earliest unfinished stage, then check tool version, input hashes, and output existence in that order. Run the corresponding `check_01.sh` through `check_12.sh`. See the [error index](TROUBLESHOOTING.md#triage).

## Why did Meeko fail on the upstream PDB?

The public 1IEP input has a displaced atom record. Meeko 0.8.0 reported the following actual error.

```text
ValueError: interrupted residues in PDB: {'A:438'}
```

The example restores the pinned receptor atom order by serial number while preserving coordinates. It saves the repaired PDB separately. A different PDB with interrupted chains, alternate conformations, or mixed models needs a separate review. [Input provenance](../examples/1iep/PROVENANCE.md)

## Why is the ligand charge +1?

The pinned prepared SDF encodes a protonated ligand. Open Babel round-trips the MOL2 to SDF before RDKit validates chemistry and coordinates. In development, reading this MOL2 directly with RDKit produced the actual error below. The round-trip validated the intended cation.

```text
Explicit valence for atom # 16 N, 4, is greater than permitted
```

Use the verified input charge with ACPYPE. The GROMACS examples elsewhere use a neutral generic ligand only when declared.

## What about WSL2, quoting, and permissions?

Store Linux work directories and active trajectories in the WSL filesystem. The Windows-mounted filesystem adds cross-filesystem overhead and can have different permission semantics. Quote paths containing spaces in Bash or PowerShell. Use a short ASCII working path for legacy native Windows tooling when it fails to parse a path. Keep shell scripts and text configuration files in LF format, and use plain ASCII quotes for commands. The repository sets line endings for scripts. Use writable scratch rather than running as root inside a container or on a cluster. [Microsoft WSL file-system guidance](https://learn.microsoft.com/windows/wsl/filesystems)

## Can I ignore warnings or restart from a failed stage?

GROMACS preprocessing stops on warnings by default. Trace missing parameters, topology mismatch and invalid restraints before proceeding. The example creates a fresh run directory. For a validated production checkpoint, use the [checkpoint restart guide](SIMULATION.md#server-handoff). Keep the original inputs, topology, MDP, TPR, CPT, sampled trajectory, and logs. Scratch outputs can be removed after verifying the archived copies.

[Open a reproducible issue](https://github.com/LuciferBioLab/docking-gromacs-tutorial/issues/new/choose)
