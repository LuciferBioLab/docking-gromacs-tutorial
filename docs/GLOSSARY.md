# Glossary and command reference

**English** · [简体中文](GLOSSARY.zh-CN.md)

Languages synchronized 2026-11-28. [Verified workflow commit](https://github.com/LuciferBioLab/docking-gromacs-tutorial/commit/d139618900e79f0dc186d3bb64fbe5be4cc25914).

[Repository home](../README.md#contents)

<a name="glossary"></a>

## Core terms

| Term | Definition |
| --- | --- |
| PDBQT | AutoDock coordinates with partial charges, atom types, and ligand torsion trees |
| SDF | Structure records containing coordinates and a chemical graph |
| MOL2 | Tripos representation for coordinates, connectivity, types and charges |
| Docking pose | Predicted ligand orientation and conformation in the receptor frame |
| Receptor | Target macromolecule in a specified modeling state |
| Force field | Potential energy model and parameter set |
| Topology | Atom order, interactions, parameters and molecule counts |
| PME | Particle mesh Ewald, a periodic long-range electrostatics method |
| LJ-PME | Lattice-sum treatment of long-range Lennard–Jones dispersion |
| RESI | Residue or ligand identifier in CHARMM parameter files |
| GRO / TPR / CPT | GROMACS coordinates (nm), run input, and checkpoint |
| XTC | Lossily compressed coordinate trajectory |
| PLIP / ProLIF | Interaction annotator for structures / interaction fingerprints for trajectories and poses |

<a name="flags"></a>

## Frequently used command flags

| Flag | Reason |
| --- | --- |
| Vina `--receptor`, `--ligand`, `--config` | Set docking receptor, ligand and search box inputs |
| Vina `--seed`, `--exhaustiveness`, `--num_modes`, `--out` | Record RNG seed, vary search effort, limit written poses, and specify the output file |
| GROMACS `-f`, `-c`, `-s`, `-p` | Check the subcommand: for grompp these are parameter file, coordinates and topology via `-f`, `-c`, `-p`; many analysis commands use `-f` for the trajectory and `-s` for TPR/reference |
| grompp `-r`, `-t`, `-n`, `-pp`, `-po`, `-o` | Supply restrained reference, checkpoint, and index; save expanded topology, processed parameters and TPR |
| mdrun `-deffnm`, `-ntmpi`, `-ntomp`, `-cpi` | Set file prefix, ranks, threads per rank, and restart checkpoint |
| hbond `-r`, `-t`, `-num` in GROMACS 2026.3 | Select reference and target explicitly and write counts versus time |
| ACPYPE `-i`, `-b`, `-a`, `-c`, `-n` | MOL2 input, output basename, GAFF family, charge model, and verified total ligand charge |

[GROMACS 2026.3 Manual](https://manual.gromacs.org/2026.3/) · [AutoDock Vina Documentation](https://autodock-vina.readthedocs.io/en/latest/)
