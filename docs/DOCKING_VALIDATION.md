# 多阶段分子对接验证指南 / Multi-stage docking and validation

[主教程 / Main tutorial](../README.md#contents) · [共晶重对接 / Reference redocking](../README.md#benchmark) · [排错指南 / Troubleshooting](TROUBLESHOOTING.md#troubleshooting-contents)

适用于结合口袋未知、受体由多条链组成，或一个配体可能具有多种起始构象的非共价对接。流程覆盖**受体修复 → 配体构象 → 重叠盒初筛 → 候选口袋精细搜索 → 位姿验收 → 相互作用复核**。代码使用通用文件名和示例设置。阈值应在公开共晶对照上预先验收，并随工作流版本归档。  
This guide covers noncovalent docking with an unknown pocket, a multichain receptor, or multiple ligand starting conformers. The workflow proceeds through receptor repair, conformer generation, overlapping-box screening, local refinement, pose validation, and interaction review. The commands use generic filenames and illustrative settings. Qualify the settings with a public co-crystal control and record them with the workflow version.

1. [先定位错误发生在哪一层 / Triage by failure stage](#validation-triage)
2. [受体缺原子、模板和组装体 / Receptor repair and templates](#receptor-repair)
3. [配体构象、化学状态和往返转换 / Ligand conformers and identity](#conformer-preparation)
4. [重叠搜索盒和任务验收 / Tiled search and run validation](#tiled-search)
5. [局部搜索、口袋迁移和重复性 / Local search and reproducibility](#pose-validation)
6. [亚基对称性与相互作用复核 / Subunit symmetry and interaction review](#interaction-review)
7. [归档、工具与参考文献 / Archiving, tools, and references](#validation-references)

<a name="validation-triage"></a>

## 1. 先定位错误发生在哪一层 / Triage by failure stage

| 现象 / Symptom | 常见原因 / Likely cause | 处理与复核 / Corrective action and verification |
| --- | --- | --- |
| `ModuleNotFoundError`，同一工具在另一终端可用 / Import fails in one shell | 当前解释器与安装工具的环境不同 / The shell resolves a different Python interpreter | 在运行命令的环境中检查 `sys.executable` 和包版本，按用途分开管理结构修复、对接和相互作用分析环境。 / Resolve the interpreter and check versions in the shell that runs the task. |
| Meeko 找不到模板、价态异常 / Template or valence error | 已解析残基缺侧链原子，补入侧链严重重叠，或异质组分缺少模板重原子。 / An observed residue lacks side-chain atoms, rebuilt atoms overlap, or a retained component lacks template atoms. | 逐残基核对，再重跑受体参数化，见[第 2 节](#receptor-repair)。 / Diagnose the exact residue and rerun parameterization. |
| PowerShell 报 `NativeCommandError`，日志正文像警告 / Warning reaches the native error stream | 外部程序把警告写入 stderr，Windows PowerShell 对重定向的处理因版本而异。 / A native tool writes its warning to stderr, whose handling varies by PowerShell version. | 在 WSL 内分流日志，结合退出码与新输出验收。 / Redirect inside WSL, then check the exit status and fresh outputs. |
| 无可旋转键，仍恢复出多个几何构象 / Multiple geometries for a ligand with no rotatable bonds | 环折叠可产生不同三维几何，独立起始文件也可能属于同一构象类别。 / Ring puckering can vary, and independent input files can represent one conformer family. | 用化学一致性与对齐 RMSD 验收低能构象，见[第 3 节](#conformer-preparation)。 / Verify identity and align low-energy conformers for deduplication. |
| 上次运行有输出，续跑却重复或读到半写入文件 / Duplicate or truncated results on resume | 只按文件名判定完成，输入、配置或模式块未经检查。 / File presence was used as the completion criterion. | 校验清单、结构和哈希，再接纳结果，见[第 4 节](#tiled-search)。 / Validate the manifest, pose blocks, and hashes. |
| 局部搜索得分低，配体却偏到邻近口袋 / A strong local score accompanies pocket migration | 搜索盒覆盖相邻区域，输出的最优构象可能属于另一个位置。 / The local search box also admits a neighboring pocket. | 同时检查空间位置和残基接触，单独归档迁移，见[第 5 节](#pose-validation)。 / Check position and contacts jointly and retain migrated poses for review. |
| 同源亚基出现相似结果，或距离线被当作氢键 / Repeated subunit poses or ambiguous contact labels | 对称位置可能重复计数，几何近接与化学作用采用不同定义。 / Symmetry can duplicate sites, and proximity and chemical interactions use distinct criteria. | 分别做受体坐标系下的对称性检查和供受体复核，见[第 6 节](#interaction-review)。 / Check receptor-based symmetry and verify donor–acceptor geometry separately. |

在实际运行命令的终端检查环境。将受体修复环境中的两个包替换成当前阶段需要的包即可复用此命令。  
Run this preflight in the same shell as the analysis. Change the package list to match the active stage.

```bash
python -c 'import sys; print(sys.executable)'
python -c 'from importlib.metadata import version; print({p: version(p) for p in ("pdbfixer", "openmm")})'
```

<a name="receptor-repair"></a>

## 2. 受体缺原子、模板和组装体 / Receptor repair and templates

**先确定受体组成。** 从结构来源核对所用模型、组装体、链间界面及靠近目标区域的缺失片段。为每个 `HETATM` 组分记录原始标识、完整性、保留决定和依据。移除待重对接的配体时，将原坐标另存为参照。维持生物学状态所需的金属、辅因子、连接糖或脂质需要专项建模。采用实验替代构建体时，将突变、结构状态及解释范围记录为新受体模型。  
**Define the receptor composition.** Document the source model, assembly, interfaces, and gaps near the target region. Record the identity, completeness, disposition, and rationale for each hetero component. Archive the coordinates of the reference ligand before stripping it for redocking. Essential cofactors and nonstandard chemistry require a system-specific model. An experimental surrogate construct is a separate receptor model with its own scope. [Complex-system preparation](TROUBLESHOOTING.md#complex-systems)

**缺原子与缺片段分别处理。** 对替代构象按残基选择一个相容状态，保留无替代标记的共享原子，记录占有率和平局规则。下面的 PDBFixer 示例只修补已解析残基的内部缺原子。若未解析片段位于目标口袋或形成界面，暂停并评估其他结构、经验证的补模方案或应排除的区域。检查链端、插入码、断链与二硫键，并按链、残基号、插入码、残基名、原子名比对原始和修复文件。  
**Separate missing atoms from missing segments.** Resolve alternate locations coherently per residue. Retain shared atoms with blank altloc identifiers and record the occupancy-based selection rule. The PDBFixer example repairs missing atoms within observed residues. If an unresolved segment borders the pocket or interface, review alternative structures or an independently justified modeling procedure. Compare source and repaired files with residue and atom identifiers, and verify chain breaks, termini, and disulfides. [PDBFixer manual](https://github.com/openmm/pdbfixer/blob/master/Manual.html)

将下段另存为 `repair_atoms.py`。`protein_input.pdb` 是已筛选链、处理替代构象的蛋白文件。另行保留的组分应在同一坐标系中按已核实的标识和连接关系并入。  
Save as `repair_atoms.py`. The input is a chain-selected, altloc-resolved protein PDB. Reintroduce independently reviewed retained components using verified identifiers, connectivity, and the same coordinate frame.

```python
from openmm.app import PDBFile
from pdbfixer import PDBFixer

model = PDBFixer(filename="protein_input.pdb")
model.findMissingResidues()
print("Unresolved residue blocks:", len(model.missingResidues))
model.missingResidues.clear()

model.findMissingAtoms()
print("Missing atoms in observed residues:", sum(map(len, model.missingAtoms.values())))
model.missingTerminals.clear()
model.addMissingAtoms()

with open("protein_repaired.pdb", "x") as handle:
    PDBFile.writeFile(model.topology, model.positions, handle, keepIds=True)

check = PDBFixer(filename="protein_repaired.pdb")
check.findMissingResidues()
check.missingResidues.clear()
check.findMissingAtoms()
if check.missingAtoms:
    for residue, atoms in check.missingAtoms.items():
        print(residue.chain.id, residue.id, residue.name, [atom.name for atom in atoms])
    raise SystemExit("Internal atom repair is incomplete.")
```

**补完以后仍报模板错误。** 从 stderr 定位链与残基，对照重原子清单、键连接及已有修饰。对补入侧链导致的局部冲突，可用开源 PyMOL 的同类型 rotamer 检查备选构象。用目标残基以外的近邻做几何复核，按原子名回写允许变更的坐标，并核对主链和应保留的原始重原子。只替换新原子时还需复核侧链的键长、键角和手性。PyMOL 的 bump score 用于筛选局部重叠，需要配合几何和化学检查。遇到不完整的非必需组分，可将其按明确依据排除并记录。对必需组分使用已核实的完整模型或专项模板，再验证最终 PDBQT 实际保留了哪些组分。  
**Diagnose persistent template failures.** Locate the chain and residue in stderr and inspect its heavy-atom inventory, connectivity, and modifications. For clashes involving rebuilt side chains, use the open-source PyMOL wizard to sample rotamers of the same residue type. Check neighboring atoms, transfer only the permitted coordinates by atom name, and verify original atoms and backbone positions. If only newly added atoms are moved, verify side-chain geometry after the coordinate transfer. Document removal of an incomplete nonessential component. For essential components, validate a complete model or template and check the final PDBQT inventory. [Meeko receptor preparation](https://meeko.readthedocs.io/en/develop/rec_cli_options.html) · [PyMOL rotamer implementation](https://github.com/schrodinger/pymol-open-source/blob/master/modules/pymol/wizard/mutagenesis.py)

在 Linux 或 WSL 终端的全新输出目录中运行。`receptor_qc.pdb` 是已经完成上述受体审核的坐标文件。保留 JSON、处理后 PDB、PDBQT 及两路日志。  
Run in a fresh working directory in Linux or WSL. Use the reviewed receptor coordinates and archive the preparation JSON, processed PDB, PDBQT, and both logs.

```bash
if mk_prepare_receptor.py --read_pdb receptor_qc.pdb -o receptor -p -j --write_pdb receptor.pdb \
    > prep.stdout.log 2> prep.stderr.log; then
    test -s receptor.pdbqt && test -s receptor.json && test -s receptor.pdb
else
    status=$?
    tail -n 30 prep.stderr.log >&2
    exit "$status"
fi
```

从 Windows PowerShell 调用 WSL 时，可用同一条命令在 Linux 层分流 stderr。先确认 WSL 当前目录对应工作目录，并已激活或明确指定包含 Meeko 的环境。以下示例在当前 WSL 登录环境可找到命令时使用。退出码为 0 且产物存在后，仍需检查模板和组分警告。  
When launching from PowerShell, redirect inside WSL. Confirm the WSL working directory and the active environment first. Review warnings on templates and retained components after checking the exit code and artifacts. [Microsoft PowerShell native-command guidance](https://learn.microsoft.com/en-us/powershell/scripting/learn/shell/running-commands)

```powershell
wsl.exe -- pwd
wsl.exe -- bash -lc 'exec mk_prepare_receptor.py --read_pdb receptor_qc.pdb -o receptor -p -j --write_pdb receptor.pdb > prep.stdout.log 2> prep.stderr.log'
$status = $LASTEXITCODE
if ($status -ne 0) { throw "Receptor preparation exited with code $status. Read prep.stderr.log." }
foreach ($file in 'receptor.pdbqt', 'receptor.json', 'receptor.pdb') {
    if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { throw "Missing $file" }
    if ((Get-Item -LiteralPath $file).Length -eq 0) { throw "Empty $file" }
}
```

<a name="conformer-preparation"></a>

## 3. 配体构象、化学状态和往返转换 / Ligand conformers and identity

先逐个核对盐、互变异构体、质子化状态、形式电荷和手性。MolScrub 可枚举候选化学状态，RDKit 在每个选定状态内部采样三维构象。可旋转键很少的配体也可能因环折叠而出现不同的三维构象。对于带未定义立体中心或 MMFF 参数不全的输入，先明确化学状态或更换经验证的构象生成方案。  
First review salts, tautomers, protonation, formal charge, and stereochemistry. MolScrub can enumerate microstates. Generate conformers within each selected microstate. Cyclic ligands can have multiple geometries with few rotatable bonds. Resolve undefined stereochemistry and review unsupported MMFF chemistry before proceeding. [MolScrub](https://github.com/forlilab/molscrub) · [RDKit conformer-generation guide](https://www.rdkit.org/docs/RDKit_Book.html#conformer-generation)

将下段另存为 `sample_conformers.py`，输入为已有明确化学状态的单条记录 `ligand.sdf`。同一化学态内以 MMFF 能量筛出低能构象，再按对齐重原子 RMSD 去冗余。生产任务宜使用多个嵌入种子，并保留每批的收敛数和构象类别。  
Save as `sample_conformers.py` and use a single, chemically defined SDF record. Filter by MMFF energy within the same microstate and deduplicate with aligned heavy-atom RMSD. For production use multiple embedding seeds and archive convergence and family membership.

```python
from math import isfinite
from pathlib import Path
from rdkit import Chem
from rdkit.Chem import AllChem, rdMolAlign

records = list(Chem.SDMolSupplier("ligand.sdf"))
if len(records) != 1 or records[0] is None:
    raise SystemExit("Expected one readable, chemically defined SDF record.")
ligand = Chem.AddHs(records[0])
ligand.RemoveAllConformers()
if not AllChem.MMFFHasAllMoleculeParams(ligand):
    raise SystemExit("Missing MMFF parameters. Choose a validated alternative.")

embed = AllChem.ETKDGv3()
embed.randomSeed = 41
embed.useSmallRingTorsions = True
embed.enforceChirality = True
embed.pruneRmsThresh = -1.0
ids = list(AllChem.EmbedMultipleConfs(ligand, numConfs=24, params=embed))
if not ids:
    raise SystemExit("Conformer embedding failed.")

optimized = AllChem.MMFFOptimizeMoleculeConfs(ligand, mmffVariant="MMFF94s", maxIters=1000)
ranked = sorted(
    (energy, cid)
    for cid, (status, energy) in zip(ids, optimized)
    if status == 0 and isfinite(energy)
)
if not ranked:
    raise SystemExit("No conformer reached MMFF convergence.")

heavy = Chem.RemoveHs(ligand)
selected = []
for energy, cid in ranked:
    if energy - ranked[0][0] > 4.0:
        break
    if all(
        rdMolAlign.GetBestRMS(Chem.Mol(heavy), heavy, prbId=cid, refId=ref, maxMatches=100000) >= 0.35
        for ref in selected
    ):
        selected.append(cid)

folder = Path("conformers")
folder.mkdir()
for index, cid in enumerate(selected, 1):
    with Chem.SDWriter(str(folder / f"conformer_{index:02d}.sdf")) as out:
        out.write(ligand, confId=cid)
print(f"Converged {len(ranked)}/{len(ids)}; retained {len(selected)} conformer families")
```

Meeko 接收带三维坐标的 SDF。制备后检查对接文件的化学映射元数据，回读位姿时核对分子图、手性与形式电荷，并在固定坐标系比较对应重原子。对 PDBQT 部分电荷采用单独的数值检查，并与 SDF 的形式电荷分开记录。来自不同文件或嵌入种子的同一类构象在统计时合并。  
Meeko takes a 3D ligand structure. Preserve the chemical mapping metadata, and validate the molecular graph, stereochemistry, formal charge, and mapped heavy-atom coordinates after export. Record PDBQT partial-charge checks separately from SDF formal charge. Pool equivalent conformers even when they came from different inputs or embedding seeds. [Meeko ligand and pose transfer](../README.md#pose-handoff) · [Meeko export documentation](https://meeko.readthedocs.io/en/develop/export_usage.html)

```bash
mk_prepare_ligand.py -i conformers/conformer_01.sdf -o ligand.pdbqt
```

<a name="tiled-search"></a>

## 4. 重叠搜索盒和任务验收 / Tiled search and run validation

### 4.1 用坐标生成并验收重叠搜索盒 / Construct and verify overlapping boxes

全局盒过大时，单个 Vina 任务承担更大的搜索空间。将指定目标部分的重原子范围分成相邻重叠盒，原始受体可保留有依据的邻链来提供界面环境。报告搜索范围和实际参与评分的受体组分。下面代码计算各轴中心，在保留至少包含一个目标重原子的盒后，逐原子核对覆盖。覆盖率描述**所选已建模原子**，搜索的充分性仍需通过共晶验收、边界检查及重复搜索评估。  
Split the target heavy-atom bounds into overlapping boxes. The scoring receptor may retain documented partner chains for interface context. Report box-generation atoms and scoring components separately. The script verifies coverage of selected modeled atoms after empty boxes are dropped. Use a public control and repeated searches to assess sampling. [Vina search-space guidance](https://autodock-vina.readthedocs.io/en/latest/faq.html)

将下段另存为 `build_boxes.py`。`target_atoms.pdb` 是经选择的目标蛋白原子，用标有正确元素的标准 PDB `ATOM` 记录。使用与对接受体相同的坐标系。  
Save as `build_boxes.py`. Use PDB `ATOM` records with valid element fields and the same coordinate frame as the scoring receptor.

```python
from itertools import product
from math import ceil
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree

edge, stride, padding = 28.0, 18.0, 3.0  # Angstrom, illustrative
points = []
for line in Path("target_atoms.pdb").read_text().splitlines():
    if line.startswith("ATOM  "):
        element = line[76:78].strip().upper()
        if not element:
            raise SystemExit("Missing element field in target_atoms.pdb.")
        if element not in {"H", "D"}:
            points.append([float(line[i:i + 8]) for i in (30, 38, 46)])
xyz = np.asarray(points)
if xyz.size == 0 or not np.isfinite(xyz).all():
    raise SystemExit("No valid finite heavy-atom coordinates.")

lower, upper = xyz.min(axis=0) - padding, xyz.max(axis=0) + padding
axes = []
for lo, hi in zip(lower, upper):
    span = hi - lo
    count = max(1, ceil((span - edge) / stride) + 1)
    centers = [(lo + hi) / 2] if count == 1 else np.linspace(lo + edge / 2, hi - edge / 2, count)
    axes.append(centers)

candidates = np.round(np.asarray(list(product(*axes))), 4)
within = cKDTree(xyz).query_ball_point(candidates, r=edge / 2, p=np.inf, return_length=True)
centers = candidates[within > 0]
if len(centers) == 0:
    raise SystemExit("No nonempty box.")
distance, _ = cKDTree(centers).query(xyz, p=np.inf)
if np.any(distance > edge / 2):
    raise SystemExit("Uncovered modeled atoms. Review grid spacing and rounding.")

folder = Path("boxes")
folder.mkdir()
for index, center in enumerate(centers, 1):
    with (folder / f"box_{index:04d}.txt").open("x") as out:
        for axis, value in zip("xyz", center):
            out.write(f"center_{axis} = {value:.4f}\nsize_{axis} = {edge:.4f}\n")
print(f"Covered {len(xyz)} modeled heavy atoms with {len(centers)} boxes")
```

### 4.2 完成条件包括输出结构与输入一致性 / Validate outputs and provenance before resuming

每项任务以**受体、配体输入、配置、评分函数、引擎版本、参数和种子**标识。记录输入哈希、退出码与模式数。使用临时文件，验收后改为正式文件名。历史文件可在输入和配置的指纹相符时复用。`num_modes` 是输出上限，实际个数受搜索和 `energy_range` 影响。  
Key each task by receptor, ligand input, box, scoring function, engine version, arguments, and seed. Record input hashes, exit status, and validated pose count. Promote temporary output only after validation. Reuse earlier outputs after matching their input and configuration fingerprints. `num_modes` sets an upper limit on returned poses. [Vina manual](https://vina.scripps.edu/manual/)

将下段另存为 `validate_poses.py`。示例针对 Vina 刚性受体的配体位姿 PDBQT，传入预期重原子数。若使用柔性受体或其他方言，需先分离配体记录并确认解析规则。  
Save as `validate_poses.py`. This check expects Vina ligand-only PDBQT from rigid-receptor jobs and the expected heavy-atom count. Flexible-receptor or other PDBQT variants need an appropriate parser.

```python
from math import isfinite
from pathlib import Path
import sys

expected = int(sys.argv[2])
if expected < 1:
    raise SystemExit("Expected a positive heavy-atom count.")

models = set()
active = False
for line in Path(sys.argv[1]).read_text().splitlines():
    if line.startswith("MODEL"):
        fields = line.split()
        if active or len(fields) != 2 or fields[1] in models:
            raise SystemExit("Nested, malformed or duplicate MODEL record.")
        model = fields[1]
        active, score, heavy = True, None, 0
    elif line.startswith("ENDMDL"):
        if not active or score is None or heavy != expected:
            raise SystemExit("Unmatched ENDMDL, missing score or unexpected heavy-atom count.")
        models.add(model)
        active = False
    elif line.startswith("REMARK VINA RESULT:"):
        if not active or score is not None:
            raise SystemExit("Unexpected or duplicate Vina score.")
        score = float(line.split()[3])
        if not isfinite(score):
            raise SystemExit("Nonfinite Vina score.")
    elif line.startswith(("ATOM  ", "HETATM")):
        atom_type = line[77:].strip().upper()
        if not active or not atom_type:
            raise SystemExit("Atom outside MODEL or missing AutoDock type.")
        coords = [float(line[i:i + 8]) for i in (30, 38, 46)]
        if not all(map(isfinite, coords)):
            raise SystemExit("Nonfinite pose coordinates.")
        heavy += atom_type not in {"H", "HD", "HS", "D"}

if active or not models:
    raise SystemExit("Output contains no complete set of poses.")
print(f"Validated {len(models)} complete poses")
```

下面运行一个全局任务。每个搜索盒、起始构象和种子在独立任务目录中使用相应配置及文件名。结果转入精细阶段前另做配体化学与原子映射检查。  
The example runs one screening task. Use independent task directories and explicit inputs for each box, starting conformer, and seed. Verify the ligand chemistry and atom mapping before passing the result to refinement.

```bash
set -eu
expected_heavy=$(python -c 'from rdkit import Chem; m=Chem.SDMolSupplier("conformers/conformer_01.sdf")[0]; print(m.GetNumHeavyAtoms())')
cp boxes/box_0001.txt box.txt
vina --version > engine-version.txt
sha256sum receptor.pdbqt ligand.pdbqt box.txt conformers/conformer_01.sdf > inputs.sha256
command=(vina --receptor receptor.pdbqt --ligand ligand.pdbqt --config box.txt
    --scoring vina --exhaustiveness 16 --num_modes 12 --energy_range 4
    --seed 41 --cpu 2 --out poses.partial.pdbqt)
printf '%q ' "${command[@]}" > invocation.txt
printf '\n' >> invocation.txt
"${command[@]}" > vina.stdout.log 2> vina.stderr.log
python validate_poses.py poses.partial.pdbqt "$expected_heavy"
mv poses.partial.pdbqt poses.pdbqt
sha256sum poses.pdbqt > poses.sha256
```

<a name="pose-validation"></a>

## 5. 局部搜索、口袋迁移和重复性 / Local search and reproducibility

**先定义口袋，再比较分数。** 将全局输出里的所有合格模式按目标接触筛选。用配体重原子几何中心和接触残基集合去除重叠盒产生的重复。残基键应包括链、残基编号、插入码及残基名。一个可复现的简化策略是按分数和稳定的任务标识排序，选先到的位姿为固定锚点，后续同时满足中心距离与接触 Jaccard 阈值者归入该口袋。每个起始构象各自选定候选口袋，再合并短名单。记录锚点的来源和接触集合。  
**Define pockets before comparing scores.** Review all valid screening poses with target contacts. Deduplicate across overlapping boxes using geometric centers and residue-contact sets. Include chain, residue number, insertion code, and residue name in each key. A reproducible option is to sort by score and stable job identifiers, choose fixed anchors, and assign subsequent poses only when they satisfy both proximity and contact-overlap criteria. Shortlist pockets per starting conformer, then combine the shortlists.

**局部盒用参考位姿的全部重原子定界。** 以参考坐标外接盒中心为中心，以最大轴跨度加两侧余量确定边长。任一参考原子挨近盒面时，复核多个参考是否来自同一口袋，或重新设定有依据的边界。在同一口袋、评分方案与参考盒下用多个记录在案的种子重复搜索。例如可把全局命令中的配置、`--exhaustiveness` 和 `--seed` 替换成经预实验验收的局部设置，逐次运行并验收。局部最优分数和全局最优分数来自不同搜索，报告它们各自的统计口径。  
**Size the local box from all reference heavy atoms.** Use the midpoint of the coordinate bounds and add a margin on both sides of the largest span. Review reference poses that lie near the box faces or span distinct sites. Repeat the local searches with recorded seeds under a shared box and scoring protocol. Report screening and refinement scores with their respective summary definitions.

**对精细输出做独立验收。** 恢复配体 SDF 并核对化学身份和映射后，按位置、接触、近距离重叠和边界分类。以下函数可用于逐位姿报告。阈值为演示用，`residue_keys` 每项对应受体蛋白重原子，`target_residues` 为允许入选的目标残基，`receptor_heavy` 使用实际参与评分的全部受体重原子。`refs` 中的每个参考配对为该口袋的几何中心和接触残基集合。  
**Validate refinement poses independently.** After SDF recovery and chemical/atom-map verification, audit position, residue contacts, severe overlap, and box geometry. The function below illustrates per-pose classification. Build `refs` from the reference centers and residue-contact sets for the same pocket. Use the full scoring receptor to test severe overlap.

```python
import numpy as np
from scipy.spatial import cKDTree

def local_box(reference_xyz, margin=5.0):
    points = np.vstack(reference_xyz)
    lower, upper = points.min(axis=0), points.max(axis=0)
    center = (upper + lower) / 2
    edge = max(22.0, float(np.ceil((upper - lower).max() + 2 * margin)))
    if edge > 30.0:
        raise ValueError("Review the pocket and reference poses before enlarging the box.")
    return center, edge

def jaccard(left, right):
    union = left | right
    return len(left & right) / len(union) if union else 0.0

def review_pose(pose, protein_heavy, residue_keys, target_residues, receptor_heavy, refs, box):
    center, edge = box
    hits = cKDTree(protein_heavy).query_ball_point(pose, r=4.0)
    contacts = {residue_keys[i] for indices in hits for i in indices}
    centroid = pose.mean(axis=0)
    if not refs:
        raise ValueError("At least one pocket reference is required.")
    comparisons = [(float(np.linalg.norm(centroid - c)), jaccard(contacts, r)) for c, r in refs]
    nearest = float(cKDTree(receptor_heavy).query(pose)[0].min())
    margin = float((edge / 2 - np.abs(pose - center)).min())

    flags = []
    if not contacts & target_residues:
        flags.append("NO_TARGET_CONTACT")
    if not any(distance <= 4.5 and overlap >= 0.30 for distance, overlap in comparisons):
        flags.append("POCKET_MIGRATION")
    if nearest < 1.6:
        flags.append("SEVERE_CLASH")
    if margin < -0.01:
        flags.append("OUTSIDE_BOX")
    return {"flags": flags, "min_distance_A": nearest, "box_margin_A": margin, "references": comparisons}
```

将迁移模式另存，以便判断邻近区域是否值得单独复核。一个位姿可能触发多条标记，报告独立异常位姿数和各原因的计数。轻微出盒的容许量仅用于数值判定，严重近接阈值仅筛查明显重叠。  
Archive migrated poses for separate review. A pose can trigger multiple flags, so report the number of affected poses and the count per reason. The box tolerance handles numerical precision, and the short-distance threshold screens for obvious overlaps.

### 5.1 按固定坐标系聚类，按种子汇总 / Cluster in the receptor frame and summarize seeds

游离配体构象去重可用 `GetBestRMS` 做最优叠合。对接位姿处在同一受体坐标系，使用 `CalcRMS` 做配体原子对称性校正，保持位姿的绝对位置与方向。在各口袋内以预先声明的阈值聚类。采用完全连接约束时，新成员须与簇内**所有位姿**同时满足阈值。按起始构象和种子分组，在每簇内每个种子至多计入一个位姿。汇总命中数、评分中位数、极差及最大两两 RMSD。使用到其他种子代表的距离总和最小的实际输出位姿作为 medoid，保留对应文件、种子和模式号。  
Use `GetBestRMS` for aligned, free-conformer deduplication. For docked poses in a common receptor frame, `CalcRMS` accounts for ligand atom symmetry without fitting away placement or orientation. Declare the within-pocket clustering threshold before inspection. A complete-link constraint requires a new member to be within the threshold of every current cluster member. Count at most one pose per seed and starting conformer in each cluster. Report seed hits, median score, score range, and maximum pairwise RMSD. A medoid is an observed pose with the smallest sum of distances to the other seed representatives. [RDKit alignment API](https://www.rdkit.org/docs/source/rdkit.Chem.rdMolAlign.html)

```python
from rdkit import Chem
from rdkit.Chem import rdMolAlign

def fixed_frame_rmsd(probe, reference):
    left, right = Chem.RemoveHs(probe), Chem.RemoveHs(reference)
    if Chem.MolToSmiles(left, isomericSmiles=True) != Chem.MolToSmiles(right, isomericSmiles=True):
        raise ValueError("The selected poses represent different chemical graphs or stereoisomers.")
    return rdMolAlign.CalcRMS(left, right, maxMatches=100000)
```

对公开共晶重对接同时报告排名第一位姿、搜索到的最接近实验位姿，以及后者的排名。这样可以区分搜索未命中与命中后排序偏低。多种子重现率描述计算搜索重复性，单独报告实验参照与模型限制。  
For a co-crystal control, report the top-ranked pose, the closest sampled pose to the experimental ligand, and the rank of that closest pose. This distinguishes failure to sample the reference geometry from failure to rank it first. Report seed reproducibility alongside the experimental control and model scope. [Public redocking benchmark](../README.md#benchmark)

<a name="interaction-review"></a>

## 6. 亚基对称性与相互作用复核 / Subunit symmetry and interaction review

**链互换后可能是同一个候选结合模式。** 先根据接触残基和结构模型确定比较的亚基。按序列与结构匹配受体 Cα，在一致的构象区域计算 Kabsch 刚体变换。将**同一个**受体变换施加到移动亚基及其配体，再算固定坐标系配体 RMSD。界面位姿还需把参与接触的其他链纳入同一映射。分别报告匹配原子数、亚基对齐 RMSD、配体 RMSD 和接触关系。链各自独立拟合或重新叠合配体可能掩盖口袋位置差异。  
**Compare symmetry-related poses using a receptor-derived transformation.** Match homologous Cα atoms in equivalent structural regions. Apply one proper Kabsch rotation and translation to both the moving receptor and its ligand. For interface poses, verify the participating partner chains under the same mapping. Report matched atoms, receptor alignment RMSD, transformed ligand RMSD, and contact equivalence. [Kabsch 1976](https://doi.org/10.1107/S0567739476001873)

以下函数接收按相同顺序匹配的两组受体坐标。配体输入为随移动亚基一起变换的重原子坐标。若配体原子序不同，先建立映射或将变换后坐标交给第 5 节的对称性校正 RMSD。  
Pass the matched receptor coordinates in the same order. The ligand coordinates move with the receptor. Use the atom mapping or symmetry-corrected RMSD from Section 5 for the transformed ligand.

```python
import numpy as np

def transfer_receptor_frame(moving_ca, fixed_ca, ligand_xyz):
    if moving_ca.shape != fixed_ca.shape or len(moving_ca) < 3:
        raise ValueError("Matching C-alpha coordinate sets are required.")
    moving_origin = moving_ca.mean(axis=0)
    fixed_origin = fixed_ca.mean(axis=0)
    left, right = moving_ca - moving_origin, fixed_ca - fixed_origin
    if min(np.linalg.matrix_rank(left), np.linalg.matrix_rank(right)) < 2:
        raise ValueError("The matched C-alpha atoms must be non-collinear.")
    u, _, vt = np.linalg.svd(left.T @ right)
    if np.linalg.det(u @ vt) < 0:
        u[:, -1] *= -1
    rotation = u @ vt
    receptor_rmsd = float(np.sqrt(np.mean(np.sum((left @ rotation - right) ** 2, axis=1))))
    transformed_ligand = (ligand_xyz - moving_origin) @ rotation + fixed_origin
    return receptor_rmsd, transformed_ligand
```

**用实际对接的受体模型构建复合物。** 将所选单一位姿导出 SDF。核对配体与原始输出的重原子映射和坐标。用于绘图的受体 PDB 与打分用 PDBQT 需按原子身份核对坐标和组分；单向最近邻距离适合做快速几何排查。保留受体中已核实的连接、配体化学结构和复合物中唯一的配体残基标识。  
**Build the complex from the actual scoring model.** Recover the chosen pose to SDF and verify mapped heavy-atom coordinates against its source mode. Compare the scoring PDBQT and complex PDB by atom identity, coordinates, and component inventory. A one-way nearest-neighbor check serves as a geometric preflight. Retain verified connectivity and assign an unambiguous ligand residue identifier in the complex.

```bash
# selected_pose.pdbqt is one audited MODEL/ENDMDL block with its Meeko mapping.
mk_export.py selected_pose.pdbqt -s selected_pose.sdf
# complex.pdb contains the matching receptor and the audited pose.
plip -f complex.pdb -o interactions -x -t --maxthreads 1
```

**PLIP 报告按目标配体读取。** XML 可能同时包含保留辅因子或脂质对应的位点。按配体残基名、链和残基号锁定报告条目，再按原子身份和坐标回查索引。对候选氢键分别核对供受体身份与质子化、D···A 与 H···A 距离及 D–H···A 角度。蛋白供体类型可疑、角度偏离或索引不匹配时，保留待核验标记。结构图把普通近接、候选氢键和环心距离分别标注，并保留 PyMOL 源会话和距离表。  
**Select the intended ligand in PLIP reports.** A report may contain independent sites for cofactors or lipids. Select the XML site by residue name, chain, and residue number, then cross-check atom indices against identities and coordinates. Review donor/acceptor identity, protonation, D···A and H···A distances, and the D–H···A angle for each putative hydrogen bond. Flag questionable assignments. Distinguish proximity, putative hydrogen bonds, and ring-centroid distances in figures. Archive the PyMOL session and the measurement table. [PLIP CLI and source](https://github.com/pharmai/plip) · [Publication figures](../README.md#publication-figures)

<a name="validation-references"></a>

## 7. 归档、工具与参考文献 / Archiving, tools, and references

| 阶段 / Stage | 至少归档 / Minimum record |
| --- | --- |
| 输入与制备 / Input and preparation | 数据来源和版本、链与组分清单、化学状态、修复前后差异、参数化日志和软件版本 / Source versions, chain and component inventory, microstate, repair changes, preparation logs, and versions |
| 全局与局部搜索 / Screening and refinement | 盒中心与尺寸（Å）、覆盖报告、任务参数与种子、输入输出哈希、任务状态和位姿数 / Box centers and dimensions in Å, coverage report, arguments and seeds, file hashes, status, and pose count |
| 位姿验收与解读 / Pose validation and interpretation | 原始模式编号、化学映射、排除原因、参考口袋、种子支持、最终实际位姿、原始 XML 和复查表 / Source pose ID, chemistry map, rejection reasons, reference pocket, seed support, selected pose, raw XML, and review table |

### 工具 / Tools

| 工具 / Tool | 用途 / Role | 手册与源码 / Documentation and source |
| --- | --- | --- |
| AutoDock Vina | 全局与局部对接 / Screening and local docking | [Manual](https://autodock-vina.readthedocs.io/) · [GitHub](https://github.com/ccsb-scripps/AutoDock-Vina) |
| PDBFixer / OpenMM | 已解析残基缺原子修复和坐标读写 / Repair observed residues and write coordinates | [PDBFixer manual](https://github.com/openmm/pdbfixer/blob/master/Manual.html) · [OpenMM](https://github.com/openmm/openmm) |
| PyMOL Open Source | rotamer 排查和结构图 / Rotamer inspection and molecular views | [PyMOL](https://pymol.org/) · [Open-source repository](https://github.com/schrodinger/pymol-open-source) |
| MolScrub / RDKit | 化学状态、构象与 RMSD / Microstates, conformers, and RMSD | [MolScrub](https://github.com/forlilab/molscrub) · [RDKit](https://github.com/rdkit/rdkit) · [RDKit documentation](https://www.rdkit.org/docs/) |
| Meeko | 受体与配体制备、恢复对接位姿 / Preparation and pose export | [Documentation](https://meeko.readthedocs.io/) · [GitHub](https://github.com/forlilab/Meeko) |
| NumPy / SciPy | 坐标、空间索引和距离检查 / Coordinate arrays and spatial queries | [NumPy](https://numpy.org/doc/stable/) · [SciPy cKDTree](https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.cKDTree.html) |
| PLIP | 相互作用注释与复核 / Interaction annotation and review | [Open-source repository and CLI](https://github.com/pharmai/plip) |

### 参考文献 / References

1. Trott O, Olson AJ. AutoDock Vina: improving the speed and accuracy of docking with a new scoring function, efficient optimization, and multithreading. *J Comput Chem.* 2010. [DOI](https://doi.org/10.1002/jcc.21334)
2. Eberhardt J, Santos-Martins D, Tillack AF, Forli S. AutoDock Vina 1.2.0: New Docking Methods, Expanded Force Field, and Python Bindings. *J Chem Inf Model.* 2021. [DOI](https://doi.org/10.1021/acs.jcim.1c00203)
3. Martis EAF, Téletchéa S. Ten quick tips to perform meaningful and reproducible molecular docking calculations. *PLoS Comput Biol.* 2025. [DOI](https://doi.org/10.1371/journal.pcbi.1013030)
4. Eastman P, et al. OpenMM 7: Rapid development of high performance algorithms for molecular dynamics. *PLoS Comput Biol.* 2017. [DOI](https://doi.org/10.1371/journal.pcbi.1005659)
5. Riniker S, Landrum GA. Better Informed Distance Geometry: Using What We Know To Improve Conformation Generation. *J Chem Inf Model.* 2015. [DOI](https://doi.org/10.1021/acs.jcim.5b00654)
6. Wang S, Witek J, Landrum GA, Riniker S. Improving Conformer Generation for Small Rings and Macrocycles Based on Distance Geometry and Experimental Torsional-Angle Preferences. *J Chem Inf Model.* 2020. [DOI](https://doi.org/10.1021/acs.jcim.0c00025)
7. Halgren TA. MMFF VI. MMFF94s option for energy minimization studies. *J Comput Chem.* 1999. [PubMed](https://pubmed.ncbi.nlm.nih.gov/34376030/)
8. Santos-Martins D, et al. Meeko: Molecule Parametrization and Software Interoperability for Docking and Beyond. *J Chem Inf Model.* 2025. [DOI](https://doi.org/10.1021/acs.jcim.5c02271)
9. Kabsch W. A solution for the best rotation to relate two sets of vectors. *Acta Crystallogr A.* 1976. [DOI](https://doi.org/10.1107/S0567739476001873)
10. Salentin S, et al. PLIP: fully automated protein–ligand interaction profiler. *Nucleic Acids Res.* 2015. [DOI](https://doi.org/10.1093/nar/gkv315)
11. Schake P, et al. PLIP 2025: introducing protein–protein interactions to the protein–ligand interaction profiler. *Nucleic Acids Res.* 2025. [DOI](https://doi.org/10.1093/nar/gkaf361)

感谢上游开源项目和数据维护者。通用的软件引用、力场资料及适用范围见[主教程的参考文献与软件引用](../README.md#references)。  
We acknowledge the upstream developers and data maintainers. For broader software and force-field citations and scope, see the [main tutorial references](../README.md#references).
