# 制备、对接与位姿交接

[English](DOCKING.md) · **简体中文**

[仓库首页](../README.zh-CN.md#contents)

<a name="docking"></a>

## 03. receptor（受体）与配体制备

- **输入** 经审核的蛋白 PDB 和配体 SDF
- **输出** 输出 receptor（受体）及配体 PDBQT
- **失败时的操作** 结构或质子化存疑时先停止

新建 Linux 工作目录时使用下面的命令。若已按[本地输入章节](#local-inputs)建立项目，只在对应的项目目录执行最后一行。

**环境：** `Bash`。**预期文件或核查依据：** 终端输出或下方命令指定的文件。耗时和磁盘规划见快速入门的分阶段表。

```bash
mkdir -p "$HOME/docking-md-workshop"
cd "$HOME/docking-md-workshop"
mkdir -p input ligands/pdbqt dock qc md
```

<a name="local-inputs"></a>

### 从现有文件开始

在新的项目工作目录中打开 PowerShell，分别填写原始 PDB 和 SDF 的绝对路径。下例只复制指定文件，副本使用本教程的统一文件名。PowerShell 用于导入，后续标为 Bash 的命令在 WSL 或 Linux 中执行。已在 Linux 中工作时，直接把指定文件复制到项目的 `input/`，使用相同文件名。 [Microsoft WSL filesystem guidance](https://learn.microsoft.com/en-us/windows/wsl/filesystems)

<details>
<summary>PowerShell 导入示例</summary>

**环境：** `PowerShell`。**预期文件或核查依据：** 终端输出或下方命令指定的文件。耗时和磁盘规划见快速入门的分阶段表。

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

`wsl pwd` 用来确认 WSL 中当前目录对应的路径。在该目录核对两个副本。若后续将项目移到 Linux 文件系统，重新核对工作目录和输入路径。

</details>

| 原始输入 | 进入下一步的条件 |
| --- | --- |
| `input/protein_raw.pdb` | 核对组装、链、口袋、非标准成分及缺失区域。之后分别准备 MD 用的 `protein.pdb` 和对接用的 `receptorH.pdb`。 |
| `input/ligand_raw.sdf`，2D | 先确定 bond order（键级）、手性和微观状态，再生成 3D 构象及显式氢，供 Meeko 制备。 |
| `input/ligand_raw.sdf`，3D | 审核坐标、显式氢、化学状态和记录号。合格的单条记录可直接用于配体制备。 |

[Ligand input requirements](https://meeko.readthedocs.io/en/develop/lig_prep_basic.html) · [复杂结构审核](TROUBLESHOOTING.zh-CN.md#complex-systems)

| 输入 | 准备要求 |
| --- | --- |
| `input/protein.pdb` | 准备供 MD 使用的蛋白，确认生物学装配、链、替代构象、缺失残基和 heavy atom（重原子）、二硫键、端基以及 His 状态。保留原始结构、PDB ID 和取舍依据。 |
| `input/receptorH.pdb` | 使用同一 receptor（受体）坐标系和已审查的质子化假设，提供适合 Meeko 的 receptor（受体）。逐个审查水、离子和辅因子对口袋的作用。 |
| `input/ligand_raw.sdf` | 获取有明确 bond order（键级）、手性和身份的小分子记录。记录 CID 或其他来源、pH 假设和每个候选的整数净电荷。 |
| `dock/box.txt` | 根据共晶配体或其他口袋证据确定搜索盒，目视确认它覆盖预期区域。中心和三个边长均以 Å 计。每个 receptor（受体）或不同口袋应保留自己的配置。 |

来源与命令参考 · [RCSB PDB](https://www.rcsb.org/) · [PubChem](https://pubchem.ncbi.nlm.nih.gov/) · [Meeko receptor options](https://meeko.readthedocs.io/en/develop/rec_cli_options.html) · [Molscrub CLI](https://molscrub.readthedocs.io/en/latest/cli.html)

**receptor（受体）分两份处理** 从同一份源结构确定链、altloc、缺失部分、口袋水和所需辅助成分。可用开源 PyMOL 查看和选择链，保存经审核的 `input/protein.pdb`。为 `input/receptorH.pdb` 确定氢与 protonation state（质子化状态）后，用 Meeko 制备 receptor（受体） PDBQT。已有 AutoDockTools 的读者可用它辅助加氢、查看旧 GPF 或准备对接 receptor（受体），但应逐项复核化学状态和盒范围。MD 仍从经审核的蛋白 PDB 用 `pdb2gmx` 生成 topology（拓扑）。 [Meeko receptor preparation](https://meeko.readthedocs.io/en/develop/rec_cli_options.html) · [Scripps AutoDock Suite](https://ccsb.scripps.edu/autodocksuite/)

下例从 Molscrub 输出中选第 1 条作为候选。按实际审核结果替换记录号。若已有确认过的带显式氢、单记录 3D SDF，可直接将其保存为 `ligands/state001.sdf`。为不同化学状态使用独立 ID。

**环境：** `docktools`。**预期文件或核查依据：** 终端输出或下方命令指定的文件。耗时和磁盘规划见快速入门的分阶段表。

```bash
conda activate docktools
scrub.py input/ligand_raw.sdf -o ligands/candidates.sdf --ph 7.4
obabel ligands/candidates.sdf -ocan
obabel ligands/candidates.sdf -f 1 -l 1 -O ligands/state001.sdf
```

**用 RDKit 检查候选** 命令块在已激活的 `docktools` 中执行。进入 Python 后读入所选 SDF，核对手性、整数净电荷、显式氢和 3D 标记。若读取失败或结构与预期不符，回到候选选择。退出 Python 后再调用 Meeko。 [RDKit Python guide](https://www.rdkit.org/docs/GettingStartedInPython.html)

**环境：** `docking-gromacs`。**预期文件或核查依据：** 终端输出或下方命令指定的文件。耗时和磁盘规划见快速入门的分阶段表。

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

**环境：** `Bash`。**预期文件或核查依据：** 终端输出或下方命令指定的文件。耗时和磁盘规划见快速入门的分阶段表。

```bash
mk_prepare_receptor.py --read_pdb input/receptorH.pdb -o dock/receptor -p
mk_prepare_ligand.py -i ligands/state001.sdf -o ligands/pdbqt/state001.pdbqt
sha256sum input/* > qc/input_sha256.txt
```

将下列六项保存为 `dock/box.txt`，把示例值替换为自己测定的中心与尺寸。旧 AutoGrid 参数中的网格间隔数乘间距才得到 Å。对于无已知口袋的结构，可另建探索性搜索盒并检查采样收敛和口袋证据。

```ini
center_x = 15.190
center_y = 53.903
center_z = 16.917
size_x = 20.0
size_y = 20.0
size_z = 20.0
```

**验收** 核对 SDF 记录、显式氢、手性、bond order（键级）和净电荷。配体 PDBQT 应保留 Meeko 写入的化学映射信息。receptor（受体）文件、参考配体和搜索盒应在同一坐标系中。 [Meeko documentation](https://meeko.readthedocs.io/) · [Open Babel CLI](https://openbabel.org/docs/Command-line_tools/babel.html)

**结构与化学核对** 实验结构使用 wwPDB 验证报告复核质量，配体标识可用化学组分字典核对。 [wwPDB validation reports](https://www.wwpdb.org/validation/validation-reports) · [Chemical Component Dictionary](https://www.wwpdb.org/data/ccd)

**局部筛选、盲对接和复筛** 有共晶或可靠位点时，优先用局部盒并用重对接验收。无已知口袋时，用单独的探索性盒（如 `dock/box_blind.txt`）记录范围、种子和搜索力度，检查候选是否集中在有结构依据的口袋，再为候选口袋新建局部盒和输出目录进行复筛。保留不同盒的独立结果。旧 GPF 可用 `grep -E '^(npts|spacing|gridcenter)[[:space:]]' receptor.gpf` 查字段。例如 `npts 60 60 60` 和 `spacing 0.375` 对应三边各 22.5 Å。若 `gridcenter` 为 `auto`，应重新核实真实中心再填写。 [Vina FAQ](https://autodock-vina.readthedocs.io/en/latest/faq.html)

<a name="batch-docking"></a>

## 04. CPU 与 CUDA 批量对接

- **输入** PDBQT、对接盒和清单
- **输出** 输出已打分的 docking pose（对接位姿）和日志
- **失败时的操作** 续跑前检查失败条目

两条路线共用步骤 03 的 receptor（受体） PDBQT、配体 PDBQT 和搜索盒。为每个筛选条件保留独立目录。可逐个调用 Meeko 生成配体 PDBQT，或用 `--multimol_outdir` 处理已审核的多记录 SDF。保留候选 ID 与原始 SDF 的对应表，并检查重名和漏项。<sup>[7](REFERENCES.zh-CN.md#ref-7)</sup> [Meeko ligand CLI](https://meeko.readthedocs.io/en/develop/lig_cli_options.html)

### A. CPU · AutoDock Vina

先跑一个已审核配体，核对日志和 docking pose（对接位姿）后再开始批量筛选。

**环境：** `docktools`。**预期文件或核查依据：** 终端输出或下方命令指定的文件。耗时和磁盘规划见快速入门的分阶段表。

```bash
conda activate docktools
mkdir dock/cpu_single_202601
vina --receptor dock/receptor.pdbqt --ligand ligands/pdbqt/state001.pdbqt  --config dock/box.txt --scoring vina --cpu 4 --exhaustiveness 32  --num_modes 20 --seed 202601 --out dock/cpu_single_202601/state001_out.pdbqt  > dock/cpu_single_202601/vina.log 2>&1
tail -20 dock/cpu_single_202601/vina.log
grep -E '^MODEL|^REMARK VINA RESULT' dock/cpu_single_202601/state001_out.pdbqt
```

**环境：** `docking-gromacs`。**预期文件或核查依据：** 终端输出或下方命令指定的文件。耗时和磁盘规划见快速入门的分阶段表。

```bash
mkdir dock/cpu_batch_202601
time vina --receptor dock/receptor.pdbqt --batch ligands/pdbqt/*.pdbqt  --config dock/box.txt --scoring vina --cpu 4 --exhaustiveness 32  --num_modes 20 --seed 202601 --dir dock/cpu_batch_202601  > dock/cpu_batch_202601/vina.log 2>&1
find ligands/pdbqt -maxdepth 1 -type f -name '*.pdbqt' | wc -l
find dock/cpu_batch_202601 -maxdepth 1 -type f -name '*.pdbqt' | wc -l
```

`--batch` 针对同一 receptor（受体）逐个处理配体，`--cpu 4` 控制一次 Vina 进程的线程数。拆分大库后可在 CPU 配额内并行运行多个独立批次。多个 receptor（受体）分别使用各自的搜索盒。 [Vina native batch mode](https://autodock-vina.readthedocs.io/en/latest/docking_in_batch.html)

#### Windows 原生 Vina 与 WSL2 文件交接

如果使用 WSL Bash 做准备、原生 Windows 运行 Vina，先把必要的对接文件复制到 Windows 用户目录。替换 `YOUR_WINDOWS_USER`，在 WSL 项目根目录执行。原始 SDF 和 receptor（受体）供 MD 使用的 PDB 留在 WSL 项目中。Windows 盘在这里只用于交接。 [Microsoft WSL filesystems](https://learn.microsoft.com/windows/wsl/filesystems)

**环境：** `Bash`。**预期文件或核查依据：** 终端输出或下方命令指定的文件。耗时和磁盘规划见快速入门的分阶段表。

```bash
win_user='YOUR_WINDOWS_USER'
win_job="/mnt/c/Users/$win_user/MD_exchange/target01"
mkdir -p "/mnt/c/Users/$win_user/MD_exchange"
mkdir "$win_job" &&
  mkdir -p "$win_job/dock" "$win_job/ligands/pdbqt" &&
  cp dock/receptor.pdbqt dock/box.txt "$win_job/dock/" &&
  cp ligands/pdbqt/*.pdbqt "$win_job/ligands/pdbqt/"
```

在 Windows PowerShell 进入交接目录。示例假定官方可执行文件放在该目录并命名为 `vina.exe`。如已安装在其他位置，将 `$Vina` 改为完整路径。 [Official Windows batch instructions](https://autodock-vina.readthedocs.io/en/latest/docking_in_batch.html)

**环境：** `PowerShell`。**预期文件或核查依据：** 终端输出或下方命令指定的文件。耗时和磁盘规划见快速入门的分阶段表。

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

回到同一 WSL 项目根目录和 Bash 会话，复制这一批的完整输出，检查日志与候选姿态。若打开了新终端，先重新设定 `win_job`。在步骤 05 将 `pose_file` 设为实际复制回来的候选 PDBQT 路径；后续建系与轨迹都在 WSL 文件系统内运行。

**环境：** `Bash`。**预期文件或核查依据：** 终端输出或下方命令指定的文件。耗时和磁盘规划见快速入门的分阶段表。

```bash
test -d "$win_job/dock/cpu_batch_win_202601" &&
  test ! -e dock/cpu_batch_win_202601 &&
  cp -a "$win_job/dock/cpu_batch_win_202601" dock/
find dock/cpu_batch_win_202601 -maxdepth 1 -type f -name '*.pdbqt' -print
tail -20 dock/cpu_batch_win_202601/vina.log
```

### B. NVIDIA GPU · Uni-Dock CUDA

在 Linux 或 WSL2 的项目根目录执行。首次用 `--gpu_batch` 测一个配体。独立终端运行 `nvidia-smi -l 1` 可观察稍长测试的 GPU 使用情况。 [Uni-Dock CLI](https://github.com/dptech-corp/Uni-Dock/tree/main/unidock)

**环境：** `dockgpu`。**预期文件或核查依据：** 终端输出或下方命令指定的文件。耗时和磁盘规划见快速入门的分阶段表。

```bash
conda activate dockgpu
mkdir dock/gpu_single_202601
unidock --receptor dock/receptor.pdbqt --gpu_batch ligands/pdbqt/state001.pdbqt  --config dock/box.txt --scoring vina --search_mode balance  --num_modes 20 --seed 202601 --dir dock/gpu_single_202601  > dock/gpu_single_202601/unidock.log 2>&1
tail -25 dock/gpu_single_202601/unidock.log
find dock/gpu_single_202601 -maxdepth 1 -type f -name '*.pdbqt' -print
```

批量任务用 `--ligand_index` 读取清单。每行一个相对路径，使用无空格且唯一的文件名。先用小批代表性输入测量显存占用、耗时和输出完整性，再调整批次大小。

**环境：** `Bash`。**预期文件或核查依据：** 终端输出或下方命令指定的文件。耗时和磁盘规划见快速入门的分阶段表。

```bash
mkdir dock/gpu_batch_202601
find ligands/pdbqt -maxdepth 1 -type f -name '*.pdbqt' | LC_ALL=C sort  > dock/gpu_batch_202601/ligands.txt
test -s dock/gpu_batch_202601/ligands.txt
```

确认清单非空后运行。显存不足时用 `split -l 32 dock/gpu_batch_202601/ligands.txt dock/gpu_chunk_` 拆分清单。每次更换清单路径、日志和输出目录。

**环境：** `dockgpu`。**预期文件或核查依据：** 终端输出或下方命令指定的文件。耗时和磁盘规划见快速入门的分阶段表。

```bash
time unidock --receptor dock/receptor.pdbqt  --ligand_index dock/gpu_batch_202601/ligands.txt  --config dock/box.txt --scoring vina --search_mode balance  --num_modes 20 --seed 202601 --dir dock/gpu_batch_202601  > dock/gpu_batch_202601/unidock.log 2>&1
wc -l dock/gpu_batch_202601/ligands.txt
find dock/gpu_batch_202601 -maxdepth 1 -type f -name '*.pdbqt' | wc -l
tail -25 dock/gpu_batch_202601/unidock.log
```

`fast`、`balance`、`detail` 调整 Uni-Dock 的搜索力度。复筛可换种子或提高搜索力度，并使用新的输出目录。每个文件需有有效姿态和评分记录。按候选 ID 对照清单与输出，查日志中的 CUDA 或解析错误，单独记录未完成项。 [Uni-Dock modes and batch manifest](https://github.com/dptech-corp/Uni-Dock/blob/main/unidock/README.md)

### 对接引擎基准比较

用相同输入、口袋和配体清单，记录引擎版本、评分函数、搜索参数、种子、CPU 线程或 GPU 型号、实耗时、成功配体数和峰值显存。用成功配体数除以墙钟时间计算吞吐。分别检查已知配体的重对接所得 docking pose（对接位姿）、关键接触、候选排名和重复种子一致性。CPU 与 CUDA 引擎各自的搜索策略和参数定义有差异，原始分数保留在各自结果表中。<sup>[8](REFERENCES.zh-CN.md#ref-8)</sup>

**其他 GPU 实现** Vina-GPU 2.1 可在上游支持的 Windows 或 Linux 环境使用 OpenCL，仓库提供自带示例，批量输入输出选项为 `--ligand_directory` 与 `--output_directory`。NVIDIA 环境的构建说明会用到 CUDA Toolkit 路径，其搜索内核用 OpenCL 执行。Scripps 的 AutoDock-GPU 支持 CUDA/OpenCL，使用 AutoDock4 路线和相应的亲和力图。<sup>[9](REFERENCES.zh-CN.md#ref-9),[10](REFERENCES.zh-CN.md#ref-10)</sup> [Vina-GPU 2.1](https://github.com/DeltaGroupNJUPT/Vina-GPU-2.1) · [Scripps AutoDock-GPU](https://github.com/forlilab/AutoDock-GPU)

### 候选复筛与 docking pose（对接位姿）记录

用同一化学状态、receptor（受体）坐标和局部盒为候选重复对接。示例对 CPU 路线再用 `202602`、`202603` 重复步骤 04A 的单配体命令，替换 `--seed`、日志和目录。CUDA 路线可在 `balance` 下换种子检验稳定性，再用 `detail` 检查增加搜索力度后的结果。逐个 docking pose（对接位姿）看口袋位置、空间冲突和参考接触，按可解释的 heavy atom（重原子） docking pose（对接位姿）相似性分组；记录分组依据及进入 MD 的具体 docking pose（对接位姿）。保留以下字段，另列失败项。

| 记录 | 字段 |
| --- | --- |
| 输入 | receptor（受体）链、盒配置、配体来源、SDF 记录 ID、净电荷 |
| 对接 | 引擎、版本、搜索力度、种子、输出文件和 MODEL 或 SDF 记录号、分数 |
| 筛选 | 重对接参考、构象分组、关键接触、被淘汰原因、入选 docking pose（对接位姿） |

<a name="pose-handoff"></a>

## 05. docking pose（对接位姿）的两条 MD 交接路线

- **输入** 所选 docking pose（对接位姿）及原始化学图
- **输出** 输出已核查 SDF/MOL2
- **失败时的操作** 映射不明时重对接

两条路线都交付 `lig_pose.sdf`。原始结构提供 bond order（键级）、formal charge（形式电荷）、protonation state（质子化状态）和手性，所选 docking pose（对接位姿）提供原位 heavy atom（重原子）坐标。根据手头的结构文件选择恢复工具，再按需要选择对接设备。

**交接依据** Meeko 的软件论文说明 PDBQT 与分子图的互操作，Open Babel 文档提供后续格式转换命令。<sup>[1](REFERENCES.zh-CN.md#ref-1),[6](REFERENCES.zh-CN.md#ref-6)</sup> [Meeko paper](https://doi.org/10.1021/acs.jcim.5c02271) · [Open Babel CLI](https://openbabel.org/docs/Command-line_tools/babel.html) · [Open Babel paper](https://doi.org/10.1186/1758-2946-3-33)

| 路线 | 何时使用 | 如何恢复 |
| --- | --- | --- |
| **A · Meeko 保留映射 | 新项目，或结果仍含 Meeko 写入的 SMILES 与索引。 | Molscrub/RDKit → Meeko PDBQT → 对接 → `mk_export.py` 导出 SDF → RDKit 核对。 |
| **[B · 旧 ADT + SDF 模板](#legacy-adt-handoff)** | 已有旧 ADT docking pose（对接位姿），并保存了同一化学状态的原始 SDF。 | 选定 PDBQT MODEL → 核对一一映射 → RDKit 回填 heavy atom（重原子）坐标、补氢及核对 → SDF。 |

保留原始 SDF 和所选运行的输出。每套 force field（力场）、姿态和独立重复各用一个目录。以下示例选 AMBER + CPU docking pose（对接位姿）。如选择 CHARMM，把 `ff_family=amber` 改为 `ff_family=charmm`。使用 GPU docking pose（对接位姿）时，从步骤 04B 输出目录查找该配体的 PDBQT，把 `pose_file` 改成查到的实际路径。

**环境：** `docktools`。**预期文件或核查依据：** 终端输出或下方命令指定的文件。耗时和磁盘规划见快速入门的分阶段表。

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

### A. 保留 Meeko 映射

对接前归档原始 SDF 及 Meeko 制备的配体 PDBQT。对接后检查输出的 `REMARK SMILES`、`REMARK SMILES IDX`，并核对 `REMARK H PARENT` 记录（如有）。 [Meeko export documentation](https://meeko.readthedocs.io/en/develop/export_usage.html)

**环境：** `Bash`。**预期文件或核查依据：** 终端输出或下方命令指定的文件。耗时和磁盘规划见快速入门的分阶段表。

```bash
awk '/^REMARK SMILES / && $3 != "IDX" {print; found=1; exit}
     END {if (!found) exit 1}' selected_run.pdbqt
grep -m 1 '^REMARK SMILES IDX ' selected_run.pdbqt
grep -m 1 '^REMARK H PARENT ' selected_run.pdbqt || true
```

映射检查通过后导出。对接输出没有这些记录时，旧 ADT 结果按路线 B 处理。若需要重新对接，为新 docking pose（对接位姿）单独记录引擎、参数和筛选依据。

**环境：** `docking-gromacs`。**预期文件或核查依据：** `docked_poses.sdf`。耗时和磁盘规划见快速入门的分阶段表。

```bash
mk_export.py selected_run.pdbqt -s docked_poses.sdf
grep -E '^MODEL|^REMARK VINA RESULT' selected_run.pdbqt
obabel docked_poses.sdf -ocan
```

**Uni-Dock 备选交接** 如果某个 Uni-Dock PDBQT 文件缺少 Meeko 化学映射，可用 Uni-Dock Tools 从原 SDF 准备 GPU 输入，然后以同一个 receptor（受体）和盒重新对接，取得有化学图的 SDF。这是补充路径，取得的是一次新对接的 docking pose（对接位姿）。在步骤 05 的重复目录中开始，下面第一条命令会返回项目根目录。保留上面的 `run_dir` 变量。 [Uni-Dock Tools instructions](https://github.com/dptech-corp/Uni-Dock/blob/main/unidock_tools/README.md)

**环境：** `dockgpu`。**预期文件或核查依据：** 终端输出或下方命令指定的文件。耗时和磁盘规划见快速入门的分阶段表。

```bash
cd ../..
conda install -n dockgpu --override-channels -c conda-forge python=3.11 pip
conda activate dockgpu
python -m pip install 'git+https://github.com/dptech-corp/Uni-Dock.git@1.2.0#subdirectory=unidock_tools'
mkdir -p dock/gpu_sdfprep_202601 dock/gpu_sdf_202601
unidocktools ligandprep -l ligands/state001.sdf -sd dock/gpu_sdfprep_202601
find dock/gpu_sdfprep_202601 -maxdepth 1 -type f -name '*.sdf' -print
```

确认输出是所选的单一化学状态，再运行下面命令。检查输出只有一个配体的 SDF 文件（其内可以有多个 docking pose（对接位姿）），再复制到当前重复目录。

**环境：** `dockgpu`。**预期文件或核查依据：** 终端输出或下方命令指定的文件。耗时和磁盘规划见快速入门的分阶段表。

```bash
unidock --receptor dock/receptor.pdbqt --gpu_batch dock/gpu_sdfprep_202601/*.sdf  --config dock/box.txt --scoring vina --search_mode balance --keep_nonpolar_H  --num_modes 20 --seed 202601 --dir dock/gpu_sdf_202601  > dock/gpu_sdf_202601/unidock.log 2>&1
find dock/gpu_sdf_202601 -maxdepth 1 -type f -name '*_out.sdf' -print
```

**环境：** `docktools`。**预期文件或核查依据：** 终端输出或下方命令指定的文件。耗时和磁盘规划见快速入门的分阶段表。

```bash
cp dock/gpu_sdf_202601/*_out.sdf "$run_dir/docked_poses.sdf"
cd "$run_dir"
conda activate docktools
obabel docked_poses.sdf -ocan
```

核对 SDF 记录、docking pose（对接位姿）来源和评分后再提取。使用 PDBQT 转出的 SDF 时，核对 SDF 记录与 PDBQT MODEL 的对应关系。下面以第 1 条为示例。

**环境：** `docking-gromacs`。**预期文件或核查依据：** 终端输出或下方命令指定的文件。耗时和磁盘规划见快速入门的分阶段表。

```bash
obabel docked_poses.sdf -f 1 -l 1 -O lig_pose.sdf
obabel state_original.sdf -ocan
obabel lig_pose.sdf -ocan
```

<a name="legacy-adt-handoff"></a>

### B. 原始 SDF 模板恢复旧 ADT docking pose（对接位姿）

把同一化学状态的原始 SDF 保存为 `state_original.sdf`，把旧 Vina 输出保存为 `selected_run.pdbqt`，放在本步骤的独立目录。利用原始 ADT 输入、原子名和制备记录核对一一映射，逐项确认 heavy atom（重原子）元素、连接和序号。仅凭元素相同或行顺序相同无法确认对应关系。模板、映射或手性无法确认时，回到 A 重新准备并对接。

下面以 MODEL 1 为例，按实际选择更改。输出各列是 PDBQT serial、三维坐标（Å）和 AutoDock 类型。如果输入是 AutoDock4 `.dlg`，先在对应工具中提取所选 docking pose（对接位姿）。如果单一 docking pose（对接位姿）没有 MODEL 标记，先确认文件只含所选 docking pose（对接位姿），再单独提取。

**环境：** `Bash`。**预期文件或核查依据：** 终端输出或下方命令指定的文件。耗时和磁盘规划见快速入门的分阶段表。

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

将经核对的映射保存为 `atom_map.tsv`，每行两列，无表头。第一列是 RDKit 读入原始 SDF 并去普通氢后的 heavy atom（重原子）编号，**从 1 起**。第二列是该原子在所选 PDBQT MODEL 的 serial。用下列命令查看模板编号和元素。

**环境：** `docktools`。**预期文件或核查依据：** 终端输出或下方命令指定的文件。耗时和磁盘规划见快速入门的分阶段表。

```bash
conda activate docktools
python - <<'RDKIT'
from rdkit import Chem

template, = Chem.SDMolSupplier("state_original.sdf", removeHs=True)
for atom in template.GetAtoms():
    print(atom.GetIdx() + 1, atom.GetSymbol())
RDKIT
```

映射审核后运行。本例适用于常规有机小分子。RDKit 从模板复制化学图，回填对接 heavy atom（重原子）坐标后补氢。从三维构象重新感知的 stereochemistry（立体化学）要与模板一致。遇到断言报错时暂停并复核。 [RDKit stereochemistry API](https://www.rdkit.org/docs/source/rdkit.Chem.rdmolops.html#rdkit.Chem.rdmolops.AssignStereochemistryFrom3D)

**环境：** `docking-gromacs`。**预期文件或核查依据：** 终端输出或下方命令指定的文件。耗时和磁盘规划见快速入门的分阶段表。

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

`0.02 Å` 是这里校验文件写出与原位坐标的工程容差。归档原始 SDF、ADT 输入、MODEL 号和映射表，校验通过后再用 `lig_pose.sdf`。

### docking pose（对接位姿）与化学结构验收

在已激活的 `docktools` 环境进入 Python，对照原始化学状态和恢复 docking pose（对接位姿）。两条输出分别检查规范异构 SMILES 和净电荷。为比较化学图，RDKit 在内存中移除普通显式氢；用于参数化的原 SDF 文件保持显式氢与原位坐标。结果不同或分子读入失败时，先查明原因。

**环境：** `docking-gromacs`。**预期文件或核查依据：** 终端输出或下方命令指定的文件。耗时和磁盘规划见快速入门的分阶段表。

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

**验收** 用原始 SDF 与输出核对分子图、bond order（键级）、手性和整数净电荷。逐原子核对入选 MODEL 与 SDF 的 heavy atom（重原子）坐标。叠加时保留绝对坐标。原始 docking pose（对接位姿）或化学身份无法确认时，回到路线 A 重新生成候选。通过后进入第 06 节参数化。 [Meeko export in the Vina tutorial](https://autodock-vina.readthedocs.io/en/latest/docking_basic.html#exporting-results-to-sdf)

[返回目录](../README.zh-CN.md#contents)

## 选择位姿交接与搜索配置

| 观察 | 路线 | 验收 |
| --- | --- | --- |
| 所选 PDBQT 模型含完整 Meeko SMILES 和原子索引元数据 | A：用 Meeko 映射导出 SDF | 核对化学图、立体化学、形式电荷和固定参考系坐标 |
| Meeko 元数据缺失或不一致 | B：原始 SDF 加经过核查的唯一原子映射 | 核对同样四项并保存映射表 |
| 映射不明确或化学核查失败 | 从原始微观状态重新制备并重对接 | 对新生成的 docking pose（对接位姿）执行 A |

若安装的 Uni-Dock 1.2.0 支持，初筛用 `fast`，复筛用 `balance`，少量经审阅的候选用 `detail`。记录本机帮助、随机种子与搜索模式，筛选前用已知 docking pose（对接位姿）校准。用[批次清单与续跑参数](../examples/README.md)和[对接盒模板](../config/box.template.txt)保存每个作业的文件。盲对接盒应覆盖计划搜索的 receptor（受体）区域，在 PyMOL 中核查，尺寸单位统一为 Å。
