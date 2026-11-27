# 快速入门与验证记录

[English](QUICKSTART.md) · **简体中文**

中英文同步于 2026-11-28。[已验证的工作流提交](https://github.com/LuciferBioLab/docking-gromacs-tutorial/commit/d139618900e79f0dc186d3bb64fbe5be4cc25914)。

[仓库首页](../README.zh-CN.md#contents)

<a name="dock"></a>

## 对接并核验公开共晶结构

在 Linux 或 WSL2 的仓库根目录开始。激活环境后的三条是运行步骤。首次环境解算与下载另计。

```bash
conda env create -f environment.yml
conda activate docking-gromacs
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

<a name="quickstart-md"></a>

## 运行 MD 教学流程

使用相同环境和仓库根目录。这些命令会创建新目录，每次重跑请使用新名称。

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
| Uni-Dock 与 GROMACS CUDA | 已整理部署说明，尚无 CUDA 吞吐实测。 |
| CHARMM 与同体系 AMBER/CHARMM 对照 | 已整理参数化和对照设计，完整运行与对照结果尚待验证。 |
| CHARMM MM/PBSA | 设置已与上游 1.7.0 示例核对，尚未独立复跑。[CHARMM 端点法](RESEARCH.zh-CN.md#free-energy) |

打包示例的第 09 和 10 阶段会把动力学日志末步与处理后 MDP 中的 `init-step + nsteps` 对照。任务提前停止时，日志也可能出现正常的结束文字。

以所附文件的校验和核对完整性；轨迹解读参考软件、输入和设置记录。不同 CPU/GPU 的结果按科学判据核验。[验证与采样](RESEARCH.zh-CN.md#sampling)

若输出间隔为 `S` 步、积分步长为 `dt` ps，保存间隔为 `S × dt` ps。实测压缩轨迹 `F` 帧占 `B` 字节，在原子选择和压缩设置相同时，XTC 约占 `B/F × (floor(T_ps/(S × dt)) + 1)` 字节。100 ns、2 fs 下，每 2,500 步计算为 5 ps、约 20,001 帧；5,000 步为 10 ps、约 10,001 帧；50,000 步为 100 ps、约 1,001 帧。用自己的短试跑测实际大小，并为轨迹后处理留额外空间。


## 公开 CPU 示例的实测性能

| 任务 | 数据与设置 | 实测 |
| --- | --- | --- |
| Vina 共晶重对接 | 1IEP，四线程，exhaustiveness 8 | 对接 23 s，环境与输入制备单独计时 |
| AMBER 生产段短测试 | 55,134 原子，四线程，2 ps | GROMACS 报告 14.36 ns/day |
| CPU 基准 | 同一 TPR，1 个 thread-MPI rank，4 个 OpenMP 线程，5,000 步 | GROMACS 报告 13.82 ns/day |
| Uni-Dock / GROMACS CUDA | 在自己的调度配额内运行 | 待实测 |

完整 01–12 CPU 短测试约 3 分 16 秒，含中间文件约 53 MiB，压缩生产轨迹约 2.2 MiB。按短程 CPU 基准外推，仅 1 ns 生产段约需 1 小时 44 分钟，另计平衡和制备。排期使用同等条件下多次测量的中位数。见[基准脚本](../scripts/benchmark.sh)和[结果表模板](../examples/results-template.csv)。
