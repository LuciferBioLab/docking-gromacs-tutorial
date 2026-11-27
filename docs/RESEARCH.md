# Complex systems and research extensions

**English** · [简体中文](RESEARCH.zh-CN.md)

Languages synchronized 2026-11-28. [Verified workflow commit](https://github.com/LuciferBioLab/docking-gromacs-tutorial/commit/d139618900e79f0dc186d3bb64fbe5be4cc25914).

[Repository home](../README.md#contents)

<a name="sampling"></a>

## Sampling and benchmark design

| Checkpoint | Evidence to record | Action if the check fails |
| --- | --- | --- |
| Minimization | Maximum force, energy trend, remaining local clashes | Inspect problematic atoms and parameters before dynamics |
| NVT | Temperature around the setpoint, stable energy and restraint behavior | Check thermostat groups, time step, and starting velocities |
| NPT | Time-windowed density and volume, temperature, mean pressure and variability | Review solvation, barostat, restraints and initial relaxation |
| Production | Protein-aligned ligand RMSD and displacement, contacts, and block estimates with uncertainty | Examine jumps and state transitions, extend or increase replicas when uncertainty changes the inference |

Run at least three independently initialized trajectories as a practical starting point for an exploratory comparison. State what you vary and analyze each replica before pooling. Remove a declared equilibration period, compare successive block averages, increase block length until the uncertainty estimate stabilizes, and verify coverage of the states needed for the research question. An RMSD plateau is one diagnostic. Density and pressure depend on the system, size, and ensemble. Set tolerances from the chosen protocol and the uncertainty needed for the observable.<sup>[R1](#research-ref-1)</sup>

<a name="complex-systems"></a>

## Complex systems before parameterization

| System | Minimum checklist |
| --- | --- |
| Multichain or oligomer | Obtain the biological assembly and verify chain IDs and TER records; retain interface chains; define termini and check interchain covalent bonds deliberately |
| Membrane | Select a biological orientation, membrane composition, and compatible lipid/ion parameters; use a membrane equilibration protocol and verify box dimensions and membrane properties |
| Essential metal or cofactor | Preserve coordination geometry, cofactor connectivity and redox/protonation state; choose a validated model for that element, coordination, and force field |
| Covalent ligand | Verify reaction product, atom charges, bond graph and residue naming; use an appropriate covalent-docking and parameterization method |
| Missing or unusual residue | Review density/sequence context, alternative states, and breaks; validate modeled regions and add explicit force-field entries where needed |

For a reviewed multichain protein, the following GROMACS 2026.3 example splits at changes of chain ID or TER and writes separate chain topologies. Use it only if these boundaries represent chemically separate chains. For an interchain disulfide or another covalent link, confirm the link and consider deliberate chain merging, then verify the actual bonds and molecule counts in the expanded topology.<sup>[R2](#research-ref-2)</sup>

```bash
gmx pdb2gmx -f reviewed_assembly.pdb -o protein.gro -p protein.top -ff amber99sb-ildn -water tip3p -chainsep id_or_ter -merge no
```

Input is a curated assembly. Output is a GRO and chain topology files. Check termini, disulfides, residue logs and chain/molecule counts; stop at the first missing atom or unrecognized residue. Expected time and disk depend on assembly size.

<a name="alternative-parameters"></a>

## Parameterization and a paired AMBER–CHARMM comparison

Choose the protein force field for the scientific protocol and use the corresponding ligand, water and ion parameter ecosystem. The public CPU smoke uses AMBER99SB-ILDN, GAFF2 and AM1-BCC. The reference CHARMM procedure uses CHARMM36m, CGenFF and the CHARMM-modified TIP3P and ion definitions from the selected cutoff port. Report the exact release of the parameter files and archive CGenFF atom mappings and parameter penalties. Per the CGenFF guidance, treat scores below 10 as a close analogy, 10–50 as a reason to validate the assigned parameter, and above 50 as a priority for detailed validation or reparameterization. Prioritize chemically important torsions and charges even at lower scores.<sup>[R3](#research-ref-3)</sup>

Keep two independent directories. Match the source chemical graph, docked coordinates, temperature, salt target, time budgets and scientific observables. Use each force field's own parameter and switching scheme. Compare replicate distributions of ligand RMSD and contacts, density and uncertainty. The public example has a measured AMBER CPU smoke result. The matching CGenFF run requires a reviewed stream and its corresponding cutoff port.

OpenFF Sage plus OpenFF Interchange can export a compatible small-molecule system to GROMACS. LigParGen is an option for a compatible OPLS-AA route. Check functional forms, combination rules, 1–4 scaling, charges, and topology/coordinate order before assembling components.<sup>[R4](#research-ref-4),[R5](#research-ref-5)</sup>

<a name="interaction-analysis"></a>

## Interaction analysis and figure evidence

Use the matching complex frame from the verified trajectory as PLIP input. Preserve chain and residue identifiers. Review candidate assignments in [open-source PyMOL](https://github.com/schrodinger/pymol-open-source). Use ProLIF to assign frame-level interaction fingerprints and compute occupancy as observed frames divided by analyzed frames. State the window, stride, PBC treatment, protonation, interaction types and cutoffs. Report missing atoms and ambiguous ligand selection.<sup>[R6](#research-ref-6),[R7](#research-ref-7)</sup>

```bash
plip -f analysis/complex.pdb -o analysis/plip -x
```

Run from the replicate directory with PLIP in a separate environment. Output is an XML report. PLIP 2.4.0 completed on the public 1IEP smoke frame. It annotated four hydrogen bonds, 11 hydrophobic contacts and one π-stacking interaction using its own typing and geometric rules. [Checked result](../examples/expected/plip-summary.csv) · [Adasme et al., PLIP 2021](https://doi.org/10.1093/nar/gkab294). One frame gives structure-level annotations; use the ProLIF trajectory workflow for occupancies. Time and disk scale with number of frames and interactions. For submission panels, retain the exported image and editable layout. Use the journal's specifications for final dimensions, resolution and fonts. Inkscape can assemble vector plots; GIMP or Krita can prepare raster panels. Follow [figure and agent guidance](ANALYSIS.md#agent-workflow).

<a name="free-energy"></a>

## CHARMM endpoint setup and alchemical extensions

Create a separate results directory and use the CHARMM soluble protein–small-molecule example from gmx_MMPBSA upstream as a compatibility check. Reimage and subsample a full-system XTC against the matching TPR, verify the receptor and ligand group IDs, and use the corresponding processed CHARMM topology. For GB, check supported radii and the GB model against the installed version. For PB, record ionic strength, radii, solvent/solute dielectrics and sampling stride. A 0.15 M bulk salt example is distinct from the final explicit ion count. Select groups and window from the actual run, then review the conversion log and per-frame outputs.<sup>[R8](#research-ref-8)</sup>

For gmx_MMPBSA 1.7.0, save the following starting settings as `charmm_pbsa.in`. These radii are specific to CHARMM. The converter omits CHARMM CMAP terms. Assess that limitation before interpreting quantitative endpoint values.

```ini
&general
  startframe=1,
  endframe=4,
  PBRadii=7,
/
&pb
  radiopt=0,
  istrng=0.150,
  fillratio=4.0,
/
```

```bash
gmx_MMPBSA -nogui -i charmm_pbsa.in -cs md.tpr -ct charmm_window.xtc -ci index.ndx -cg "$protein_group" "$ligand_group" -cp md_processed.top -o CHARMM_PBSA.dat -eo CHARMM_PBSA.csv
```

Set both shell group variables for the reviewed index before running. Input syntax and environment installation are in [the endpoint walkthrough](ANALYSIS.md#endpoint-energy). Start on a few frames and scale according to the measured runtime and disk cost.

Use relative alchemical binding free energies for a well-defined set of congeneric, consistently parameterized ligands with agreed atom mappings. Absolute binding free energies require a separate restraint and standard-state protocol. Both require state overlap and convergence diagnostics. AI docking models can supply additional candidate poses for independent redocking, chemical and geometric checks.<sup>[R9](#research-ref-9)</sup>

<a name="research-references"></a>

## References and official documentation

- <a name="research-ref-1"></a> [Grossfield et al. Best Practices for Quantification of Uncertainty and Sampling Quality in Molecular Simulations](https://doi.org/10.33011/livecoms.1.1.5067)
- <a name="research-ref-2"></a> [GROMACS 2026.3 pdb2gmx](https://manual.gromacs.org/2026.3/onlinehelp/gmx-pdb2gmx.html)
- <a name="research-ref-3"></a> [MacKerell Lab CHARMM parameter sets and GROMACS ports](https://mackerell.umaryland.edu/charmm_ff.shtml) · [CGenFF tutorial](https://docs.silcsbio.com/2026/cgenff/usage.html)
- <a name="research-ref-4"></a> [OpenFF Interchange](https://github.com/openforcefield/openff-interchange)
- <a name="research-ref-5"></a> [LigParGen](https://doi.org/10.1093/nar/gkx312)
- <a name="research-ref-6"></a> [Salentin et al. PLIP: fully automated protein–ligand interaction profiler](https://doi.org/10.1093/nar/gkv315) · [PLIP GitHub](https://github.com/pharmai/plip)
- <a name="research-ref-7"></a> [Bouysset and Fiorucci. ProLIF: a library to encode molecular interactions as fingerprints](https://doi.org/10.1186/s13321-021-00548-6) · [ProLIF Documentation](https://prolif.readthedocs.io/)
- <a name="research-ref-8"></a> [gmx_MMPBSA 1.7.0 CHARMM protein–ligand example](https://valdes-tresanco-ms.github.io/gmx_MMPBSA/1.7.0/examples/Protein_ligand_CHARMMff/)
- <a name="research-ref-9"></a> [Mey et al. Best Practices for Alchemical Free Energy Calculations](https://doi.org/10.33011/livecoms.2.1.18378)
