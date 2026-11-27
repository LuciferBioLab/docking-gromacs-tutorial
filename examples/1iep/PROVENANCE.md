# 1IEP prepared example provenance

The byte-for-byte Scripps prepared receptor and ligand input files originate from
the AutoDock Vina repository at commit
[`bb64e5e`](https://github.com/forlilab/AutoDock-Vina/tree/bb64e5e26b520569a86360d69248069b5e665b3f/example/basic_docking/data).
The upstream repository uses [Apache-2.0](../../licenses/Apache-2.0-AutoDock-Vina.txt).
Prepared files retain upstream terms. See the [experimental structure](https://doi.org/10.2210/pdb1IEP/pdb)
and [upstream protocol](https://autodock-vina.readthedocs.io/en/latest/docking_basic.html).
The selected input SDF has formal charge +1.

`SHA256SUMS` covers the two original prepared inputs. The runnable example
writes a separate serial-ordered receptor. Meeko 0.8.0 rejects the original
interrupted record for residue A:438. Sorting the pinned single-chain file
restores record order without changing atom coordinates. The archived
experimental ligand is [separate](../regression/PROVENANCE.md).

```bash
(cd examples/1iep && sha256sum -c SHA256SUMS)
```
