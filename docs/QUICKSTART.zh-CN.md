# 快速入门与验证记录

[English](QUICKSTART.md) · **简体中文**

中英文同步于 2026-11-29。[已验证的工作流提交](https://github.com/LuciferBioLab/docking-gromacs-tutorial/commit/d139618900e79f0dc186d3bb64fbe5be4cc25914)。

[仓库首页](../README.zh-CN.md#contents)

在 Linux 或 WSL2 的 Linux 发行版中使用 Bash。仓库命令从包含 `Makefile` 和 `examples/` 的本地仓库根目录运行。在 Windows 中先用 PowerShell 运行 `wsl -l -v` 检查发行版，再进入 Linux，工作目录放在其 Linux 文件系统中。[Linux 与 WSL2 环境](ENVIRONMENT.zh-CN.md#setup)

若尚未下载仓库，先确认 Linux shell 中有 Git 与 GNU Make，再运行以下命令。

```bash
git clone https://github.com/LuciferBioLab/docking-gromacs-tutorial.git
cd docking-gromacs-tutorial
```

| 已有材料 | 入门路线 |
| --- | --- |
| 已有受体和配体，或尚无制备好的输入 | [只做对接](#dock) |
| 已核验的对接位姿，或已建系的 MD 输入 | [从已有位姿开始 MD](#existing-pose) |
| 已有轨迹，或已算好的指标和结构 | [分析或出图](#existing-trajectory) |

<a name="dock"></a>

## 对接并核验公开共晶结构

初次安装后即可运行公开 1IEP CPU 示例。下方的独立 `docktools` 环境安装步骤 01–05 所需的固定版本工具。若已有完整的 `docking-gromacs` 环境，激活该环境后执行下面激活命令之后的三条命令。

```bash
conda create -n docktools --override-channels -c conda-forge python=3.11 vina=1.2.7 \
  meeko=0.8.0 rdkit=2026.03.1 gemmi=0.7.5 openbabel=3.2.1
conda activate docktools
make fixtures
make dock RUN=runs/1iep-dock THREADS=4
bash scripts/check_05.sh runs/1iep-dock
```

`RUN` 指定新的独立目录。`THREADS` 是单个作业申请的 CPU 线程数。对接档以 Vina 的 `--exhaustiveness 8` 做短程参考搜索，`--num_modes 5` 限定输出上限，默认 `--seed 202601` 以记录采样种子。实际可能少于五个模式。做灵敏度检查时，可在固定其他输入的前提下比较 8、16 和 32 及多个已记录的种子。

预期输出包括 `dock/docked.pdbqt`、`dock/lig_pose.sdf`、`dock/redocking.csv` 和 `logs/vina.log`。固定的 1IEP 配体带 **+1** 的 formal charge（形式电荷），化学检查严格核对。下列结果来自 Vina 1.2.7、Meeko 0.8.0、Open Babel 3.2.1，使用四个 CPU 线程，种子为 202601。

```text
PASS stage 04
Selected SDF record 1 of 3; identity and formal charge +1 match.
Top-1 RMSD 0.350 Å; best sampled RMSD 0.350 Å.
PASS stage 05
```

Vina 第一名得分为 −13.270 kcal/mol，报告为对接分数。RMSD 使用对称等效的 heavy atom（重原子）匹配，在原 receptor（受体）坐标系下与归档的配体实例比较。无配体独立叠合，也无需再次叠合 receptor（受体）。三条 docking pose（对接位姿）的结果为 0.350、12.304、12.192 Å。CI 检查要求至少采到一条 ≤2 Å 的 docking pose（对接位姿）。浮点值会随程序和平台有所差异。

[输入来源](../examples/1iep/PROVENANCE.md) · [三个共晶参考](../examples/regression/PROVENANCE.md) · [回归 RMSD 脚本](../scripts/redocking_rmsd.py)

使用自己的输入时，从[受体和配体制备](DOCKING.zh-CN.md#local-inputs)接到 [CPU、CUDA 或 OpenCL 对接](DOCKING.zh-CN.md#batch-docking)。搜索盒的位置和边长须与该 receptor（受体）坐标系对应，单位为 Å。保留原始 SDF、原始 PDBQT、日志和位姿记录。公开示例失败时，先查 `runs/1iep-dock/logs/` 中的第一条报错，再看[对接排错](TROUBLESHOOTING.zh-CN.md#docking-errors)。

<a name="existing-pose"></a>

## 从已有 docking pose（对接位姿）开始 MD

使用 Linux 或 WSL2 Bash。若需要同时使用 AmberTools、ACPYPE、RDKit 与 GROMACS，从仓库根目录创建或激活完整的 CPU 环境。使用[拆分环境](ENVIRONMENT.zh-CN.md#setup)时，按各阶段命令切换。

准备已审查、可用于 MD 的蛋白 PDB，以及单记录位姿 SDF。核对 SDF 的键级、手性、整数净电荷和对接重原子坐标，确认两者处于**同一 receptor（受体）坐标系**。若只有 PDBQT 位姿，先按[步骤 05](DOCKING.zh-CN.md#pose-handoff)恢复 SDF。保留原始配体化学结构和原子映射。每个 force field（力场）、位姿和重复使用独立目录，执行前替换下方示例源路径。

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

| 已有输入 | 接到哪一步 |
| --- | --- |
| 已核验的位姿 SDF 和蛋白 PDB | 选择 AMBER 或 CHARMM [参数化路线](SYSTEM_SETUP.zh-CN.md#topology)。记录配体净电荷（e），核对 Å 到 nm 的转换。[组装](SYSTEM_SETUP.zh-CN.md#complex-assembly)后得到 `complex_raw.gro`、`topol.top` 及其 include 文件。 |
| 已配对的组装结构和 topology（拓扑） | 从[体系准备与平衡](SIMULATION.zh-CN.md#equilibration)的对应步骤进入，并使用[各阶段 MDP](SYSTEM_SETUP.zh-CN.md#simulation)。加盒示例从未溶剂化的 `complex_raw.gro` 开始。已有溶剂化或平衡结构时，从已验收的阶段进入，使用与该阶段匹配的拓扑、坐标、索引组和检查点。 |
| 已验收的 NPT 或 Pilot 终态 | 用同一阶段的 GRO 和 CPT [生成生产 TPR](SIMULATION.zh-CN.md#production)。核对 TPR 与拓扑，再按[服务器交接](SIMULATION.zh-CN.md#server-handoff)执行。 |

预处理失败时先读第一条 `grompp` 报错，再按[参数化与拓扑排错](TROUBLESHOOTING.zh-CN.md#topology-errors)核对电荷、原子顺序、拓扑 include 文件与位置限制参考。若体系有多链口袋、非标准残基、金属、辅因子或膜组装，先查[复杂体系](TROUBLESHOOTING.zh-CN.md#complex-systems)再选择方案。

<a name="existing-trajectory"></a>

## 用已有轨迹分析或出图

在新分析目录中放入全体系 XTC、与之配对的 TPR 和对应同一原子顺序的索引。步骤 11 使用本地文件名 `md.xtc`、`md.tpr` 和 `index.ndx`。轨迹计算使用已有的 GROMACS 环境。只需安装分析工具时，可按 [CPU 环境设置](ENVIRONMENT.zh-CN.md#setup)安装 GROMACS 2026.3。处理周期边界或计算配体 RMSD 前，先做[输入和索引核查](ANALYSIS.zh-CN.md#analysis)。抽取过原子的轨迹需搭配相同原子子集和顺序的参考结构与索引。已有 XVG 或配对的结构文件时，可直接使用 [Python 绘图](ANALYSIS.zh-CN.md#python-figures)或 [PyMOL 结构渲染](ANALYSIS.zh-CN.md#pymol-image-export)。

[已发布的 1IEP v0.1.0 示例包](https://github.com/LuciferBioLab/docking-gromacs-tutorial/releases/tag/v0.1.0)可用于绘制包内的配体 RMSD 并查看 `analysis/complex.pdb`。其中含短测 XTC，且完整轨迹分析所需的 TPR 和索引须另外准备。用归档 XVG 出图时保留其时间与距离单位。

<a name="quickstart-md"></a>

## 运行公开 1IEP MD 教学示例

使用前面创建的完整 `docking-gromacs` 环境，并先回到仓库根目录。短测和 1 ns 示例都会新建目录，每次运行请选择新的目录名。

```bash
bash scripts/run_example.sh --dry-run smoke runs/1iep-smoke
make smoke RUN=runs/1iep-smoke THREADS=4
make quickstart RUN=runs/1iep-1ns THREADS=4
```

按目标选择 smoke 或 1 ns 档。smoke 档在简短数值预检后做 2 ps 生产段。1 ns 档采用 50 ps NVT 和 100 ps NPT。十分钟是安装后的上手操作目标；实耗时还包括算电荷、平衡和 MD，可能明显更长。教学档验证的是流程交接及数据完整性，研究生产段应独立判断平衡和采样要求。

| 目标 | 必需工具或文件 | 可略过 |
| --- | --- | --- |
| 只做对接 | Vina、Meeko、RDKit、Open Babel、已制备 receptor（受体）与配体、搜索盒 | GROMACS、AmberTools、生产段、绘图 |
| 用已核验的 docking pose（对接位姿）跑 MD | 原始化学图、核验后的坐标、选定的 force field（力场）、GROMACS | 来源与 atom mapping（原子映射）均已核验时，可略去重对接 |
| 只分析或出图 | 相匹配的轨迹、topology（拓扑）或参考文件、索引以及所选分析工具 | 文件一致时可略过对接、参数化和重跑 MD |

| 阶段 | 输入 → 预期输出 | 规划耗时和磁盘 |
| --- | --- | --- |
| 01 | `environment.yml` → 工具命令可调用 | 首次解算和下载可达数分钟；含缓存预留约 5 GiB |
| 02 | 公开 PDB、SDF 与哈希 → `OK` | 数秒，小于 2 MiB |
| 03 | 排序后的 PDB、SDF → receptor（受体）和配体 PDBQT | 1IEP 数秒，小于 2 MiB |
| 04 | PDBQT 与搜索盒 → 含分数的 `docked.pdbqt` | 数秒到数分钟，本例小于 2 MiB |
| 05 | PDBQT 与原始化学图 → `lig_pose.sdf`、`redocking.csv` | 数秒，小于 1 MiB |
| 06 | 已核验 MOL2 与净电荷 → ACPYPE GRO/ITP | AM1-BCC 可达数分钟；临时文件留数 MiB |
| 07 | 蛋白 GRO 与配体 GRO/ITP → `complex.gro`、`topol.top` | 数秒至数分钟，数 MiB |
| 08 | 档位与种子 → 各阶段 MDP | 数秒，小型文本 |
| 09 | 溶质与匹配的参数文件 → `npt.gro`、`npt.cpt` | 取决于溶剂化与平衡时长；smoke 留几十 MiB |
| 10 | NPT 末态 → `md.tpr`、`md.xtc`、`md.cpt` | 对目标节点实测 ns/day；XTC 占用随帧数增长 |
| 11 | 匹配的全体系 XTC/TPR → `ligand-rmsd.xvg`、`complex.pdb` | smoke 数秒；周期边界处理可能多出两份 XTC |
| 12 | 通过验收的输出 → `provenance/outputs.sha256` | smoke 数秒，取决于校验文件大小 |

某一阶段失败时，先查 `logs/<operation>.log` 最早的错误，再跑对应的 `scripts/check_XX.sh`。另开终端后先进入正确的重复目录，并重设当节用到的变量。[文件地图与核查表](WORKFLOW.zh-CN.md#toolchain) · [排错顺序](TROUBLESHOOTING.zh-CN.md#triage)

<a name="version-matrix"></a>

## 版本与平台矩阵

验证记录日期为 **2026-11-28**。复现目标是与本文命令同一份仓库快照。发表时另记 `git rev-parse HEAD` 与环境锁的哈希。

| 组件 | 版本或路线 | 验证 |
| --- | --- | --- |
| Vina | 1.2.7 | 1IEP 重对接 |
| Meeko | 0.8.0 | receptor（受体）与配体制备，按映射导出 |
| RDKit | 2026.03.1 | SDF 化学身份与映射检查 |
| Open Babel | 3.2.1 | 格式往返及固定坐标系 RMSD |
| AmberTools / ACPYPE | 26.0 / 2023.10.27 | 1IEP AM1-BCC 与 GAFF2 文件 |
| GROMACS | 2026.3，conda-forge thread-MPI 构建 | 验证状态见下方 |
| Uni-Dock | 1.2.0，CUDA 路线 | 对照版本手册；此次验证环境无 CUDA |
| AutoDock-Vina-GPU | 2.1，OpenCL 路线 | [已核对上游源码](DOCKING.zh-CN.md#vina-gpu-opencl)，待 GPU 实跑 |
| CGenFF | 5.0 普通截断示例 | 对照上游参数与移植文档 |

`environment.yml` 声明直接依赖。[Linux x86-64 锁文件](../environment/linux-64.explicit.txt) 固定实际软件包构建。

```bash
(cd environment && sha256sum -c SHA256SUMS)
conda create -n docking-gromacs-locked --file environment/linux-64.explicit.txt
```

| 平台 | 起步预算 | 边界 |
| --- | --- | --- |
| Linux/WSL2 CPU | 2–4 核、8 GiB 内存、SSD 留 8 GiB | 供教学例起步；按实际体系测速度 |
| CUDA 工作站 | 4 核以上、16 GiB 内存，8 GiB 显存作为规划起点 | Uni-Dock 批量大小及 MD 原子数决定实际显存 |
| 集群 | 使用站点提供的二进制并在本地 scratch 运行 | MPI 进程数与 OpenMP 线程需对齐调度配额 |

<a name="validation-boundary"></a>

## 验证范围

完整的 01–12 CPU 短测试已用 4 个线程通过。生产段为 2 ps，生成经准备的 topology（拓扑）、可读的 TPR、CPT、XTC 及按蛋白叠合后的配体 RMSD 序列。生产段日志实测 **14.36 ns/day**，数值含短运行开销，另需计入参数化与制备时间。见[验证产物](../examples/expected/README.md)。

| 流程 | 验证依据与状态 |
| --- | --- |
| 1 ns CPU 快跑 | 已完成制备和平衡。生产日志最后记录到 96.6 ps，未达到计划终点，也未留下生产检查点。 |
| Uni-Dock、Vina-GPU 与 GROMACS CUDA | 已整理部署说明，尚无 GPU 吞吐实测。 |
| CHARMM 与同体系 AMBER/CHARMM 对照 | 已整理参数化和对照设计，完整运行与对照结果尚待验证。 |
| CHARMM MM/PBSA | 设置已与上游 1.7.0 示例核对，尚未独立复跑。[CHARMM 端点法](RESEARCH.zh-CN.md#free-energy) |

打包示例的第 09 和 10 阶段会把动力学日志末步与处理后 MDP 中的 `init-step + nsteps` 对照。任务提前停止时，日志也可能出现正常的结束文字。

以所附文件的校验和核对完整性；轨迹解读参考软件、输入和设置记录。不同 CPU/GPU 的结果按科学判据核验。[验证与采样](RESEARCH.zh-CN.md#sampling)

<a name="production-budget"></a>

## 100 ns 磁盘与耗时估算

积分步长为 2 fs（`dt = 0.002` ps）时，100 ns 需积分 50,000,000 步。从第 0 步开始的新任务，若每 `S` 步写一次轨迹，完整 XTC 含 `ceil(nsteps / S) + 1` 帧。首帧和末帧都会写入，末步未落在常规输出步点上时，最后一个间隔更短。分析时以轨迹实际时间戳为准。[GROMACS 2026.3 坐标输出参数](https://manual.gromacs.org/2026.3/user-guide/mdp-options.html#mdp-nstxout-compressed)

| 输出间隔 | `nstxout-compressed` | 完整帧数 | 每个重复的 XTC 估算 |
| --- | ---: | ---: | ---: |
| 10 ps | 5,000 | 10,001 | 1.90 GiB |
| 30 ps | 15,000 | 3,335 | 0.63 GiB |

估算基于已完成的公开 CPU 短测试。全体系 55,134 个原子，`compressed-x-precision = 1000`，11 帧共 2,245,348 字节。对自己的体系，用实际每帧字节数乘预计帧数和独立重复数，另留重映像轨迹、日志、检查点、能量文件及未压缩轨迹的空间。耗时用生产段 ns 除以实测 ns/day。按公开 CPU 短基准的 13.82 ns/day 外推，每个 100 ns 生产段约 7.24 天，另计制备和平衡。表中数值均来自短测试外推。


## 公开 CPU 示例的实测性能

| 任务 | 数据与设置 | 实测 |
| --- | --- | --- |
| Vina 共晶重对接 | 1IEP，四线程，exhaustiveness 8 | 对接 23 s，环境与输入制备单独计时 |
| AMBER 生产段短测试 | 55,134 原子，四线程，2 ps | GROMACS 报告 14.36 ns/day |
| CPU 基准 | 同一 TPR，1 个 thread-MPI rank，4 个 OpenMP 线程，5,000 步 | GROMACS 报告 13.82 ns/day |
| Uni-Dock / GROMACS CUDA | 在自己的调度配额内运行 | 待实测 |

完整 01–12 CPU 短测试约 3 分 16 秒，含中间文件约 53 MiB，压缩生产轨迹约 2.14 MiB。按短程 CPU 基准外推，仅 1 ns 生产段约需 1 小时 44 分钟，另计平衡和制备。排期使用同等条件下多次测量的中位数。见[基准脚本](../scripts/benchmark.sh)和[结果表模板](../examples/results-template.csv)。
