# Public crystal reference set

Deposited PDB coordinates and ligand-instance SDF exports come from the wwPDB/RCSB
archive and are covered by the [wwPDB usage policy](https://www.wwpdb.org/about/usage-policies).
See each deposition and its original citation. Untouched input bytes are pinned in `SHA256SUMS`.

| PDB | Ligand instance | Coverage | Status |
| --- | --- | --- | --- |
| [1IEP](https://www.rcsb.org/structure/1IEP) | STI, author chain A, residue 201 | Multi-aromatic kinase inhibitor; prepared microstate +1 | Automated example; recorded RMSD |
| [3PTB](https://www.rcsb.org/structure/3PTB) | BEN, author chain A, residue 1 | Compact benzamidine scaffold; review its amidinium microstate | Archived reference; independent preparation required |
| [1M17](https://www.rcsb.org/structure/1M17) | AQ4, author chain A, residue 999 | Quinazoline inhibitor with flexible side chains | Archived reference; independent preparation required |

The archive contains unmodified deposited PDBs and the corresponding ModelServer
ligand-instance SDFs. A deposited ligand instance provides the reference
coordinates. Choose and record a reviewed chemical microstate for the docking input.
Use the same receptor frame when comparing geometries. Archive alternative
locations, partner chains, symmetry handling, and input hashes.

```bash
(cd examples/regression && sha256sum -c SHA256SUMS)
```
