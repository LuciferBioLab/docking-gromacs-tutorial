# 平衡与生产模拟

[English](SIMULATION.md) · **简体中文**

中英文同步于 2026-11-28。[已验证的工作流提交](https://github.com/LuciferBioLab/docking-gromacs-tutorial/commit/d139618900e79f0dc186d3bb64fbe5be4cc25914)。

[仓库首页](../README.zh-CN.md#contents)

<a name="equilibration"></a>

## 09. 建系、能量最小化与平衡

- **输入** 待建盒复合物与 MDP
- **输出** 输出已溶剂化、最小化及平衡体系
- **失败时的操作** 定位首条预处理或动力学错误

### 建盒、溶剂化和离子

按所选路线先执行一个建盒命令。以下示例使用 AMBER 1.2 nm 或 CHARMM 1.4 nm 的初始溶质到盒边距。按实际盒形、截断和溶质尺寸验证周期映像间距。

**环境：** `docking-gromacs`。**预期文件或核查依据：** `boxed.gro`。耗时和磁盘规划见快速入门的分阶段表。

```bash
# AMBER
gmx editconf -f complex_raw.gro -o boxed.gro -c -d 1.2 -bt dodecahedron
```

**环境：** `docking-gromacs`。**预期文件或核查依据：** `boxed.gro`。耗时和磁盘规划见快速入门的分阶段表。

```bash
# CHARMM
gmx editconf -f complex_raw.gro -o boxed.gro -c -d 1.4 -bt dodecahedron
```

核对所选 force field（力场） `ions.itp` 的分子名。下例使用 `NA`、`CL`，应与实际 topology（拓扑）一致。

**环境：** `docking-gromacs`。**预期文件或核查依据：** `solv.gro`, `topol.top`, `ions.tpr`, `ions_processed.top`, `solv_ions.gro`。耗时和磁盘规划见快速入门的分阶段表。

```bash
cp topol.top topol_before_solvation.top
gmx solvate -cp boxed.gro -cs spc216.gro -o solv.gro -p topol.top

gmx grompp -f ions.mdp -c solv.gro -p topol.top -o ions.tpr  -pp ions_processed.top -po ions_out.mdp

cp topol.top topol_before_ions.top
gmx genion -s ions.tpr -o solv_ions.gro -p topol.top  -pname NA -nname CL -neutral -conc 0.15 -seed 202601
```

在 `genion` 提示中选择连续的纯水组 **SOL**，使用终端给出的实际组号。核对 topology（拓扑）中水和离子数、总电荷、盒间距。额外的中和离子会影响最终离子强度。这里借用 `spc216.gro` 作为三点水坐标模板，实际水模型由 topology（拓扑）定义。路线 A 使用 AMBER TIP3P，路线 B 使用保留氢原子 LJ 项的 CHARMM TIP3P。 [GROMACS grompp](https://manual.gromacs.org/current/onlinehelp/gmx-grompp.html) · [GROMACS MD tutorial](https://tutorials.gromacs.org/docs/md-intro-tutorial.html)

### 最速下降能量最小化

**环境：** `docking-gromacs`。**预期文件或核查依据：** `topol.top`, `em.tpr`, `em_processed.top`, `potential.xvg`。耗时和磁盘占用取决于体系大小与模拟时长。

```bash
gmx grompp -f em.mdp -c solv_ions.gro -p topol.top -o em.tpr  -pp em_processed.top -po em_out.mdp
gmx mdrun -v -deffnm em -nb cpu
gmx energy -f em.edr -o potential.xvg
```

在 `gmx energy` 选择 **Potential**，输入 `0` 结束。查看 `em.log` 的结束原因、最大力和能量变化。示例目标为最大力小于 1,000 kJ mol⁻¹ nm⁻¹。失败时先检查位阻、原子顺序、分子 topology（拓扑）和参数。

### 建立命名分组

以下原子分组依赖步骤 07 的蛋白 → 配体顺序，水和离子位于其后。用当前 `em.tpr` 生成索引并核对各组数量。若系统的默认 Backbone 或 C-alpha 分组不同，用 `gmx make_ndx -f em.gro` 查看并按实际组名调整。

**环境：** `docking-gromacs`。**预期文件或核查依据：** `em.tpr`, `index.ndx`, `index_review.ndx`。耗时和磁盘规划见快速入门的分阶段表。

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

用 `q` 退出索引检查。确认 `Complex` 和 `Water_and_ions` 互斥并覆盖全部原子。检查 `Ligand` 数量与配体 GRO 一致，并确保 `Backbone` 与 `C_alpha` 来自蛋白。后续使用原始 `index.ndx`。

### NVT → NPT

在当前 Bash 会话中，为步骤 09 的平衡及步骤 10 的模拟选择下面**一个**设备配置。此处以单节点、四 OpenMP 线程为示例。CUDA 示例使用单卡的 thread-MPI 构建。使用集群外部 MPI 构建时，按站点文档选择启动器和进程配置。在新终端续跑前重新设置数组。 [GROMACS runtime performance](https://manual.gromacs.org/documentation/current/user-guide/mdrun-performance.html)

**环境：** `Bash`。**预期文件或核查依据：** 终端输出或下方命令指定的文件。耗时和磁盘规划见快速入门的分阶段表。

```bash
# CPU
md_backend=(-ntomp 4 -nb cpu -pme cpu)
```

**环境：** `Bash`。**预期文件或核查依据：** 终端输出或下方命令指定的文件。耗时和磁盘规划见快速入门的分阶段表。

```bash
# NVIDIA GPU, thread-MPI
md_backend=(-ntmpi 1 -ntomp 4 -nb gpu -pme auto)
```

CUDA 路线查看 `nvt.log` 和 `pilot.log` 确认设备及卸载任务。短程非键合强制 GPU，PME 由 GROMACS 自动选择。

**环境：** `docking-gromacs`。**预期文件或核查依据：** `topol.top`, `nvt.tpr`, `nvt_processed.top`, `temperature.xvg`。耗时和磁盘占用取决于体系大小与模拟时长。

```bash
gmx grompp -f nvt.mdp -c em.gro -r em.gro -p topol.top -n index.ndx  -o nvt.tpr -pp nvt_processed.top -po nvt_out.mdp
gmx mdrun -v -deffnm nvt "${md_backend[@]}"
gmx energy -f nvt.edr -o temperature.xvg
```

选择 **Temperature**，观察目标温度附近的波动与漂移，再进入 NPT。

**环境：** `docking-gromacs`。**预期文件或核查依据：** `topol.top`, `npt.tpr`, `npt_processed.top`, `density.xvg`, `volume.xvg`, `pressure.xvg`。耗时和磁盘占用取决于体系大小与模拟时长。

```bash
gmx grompp -f npt.mdp -c nvt.gro -t nvt.cpt -r em.gro -p topol.top -n index.ndx  -o npt.tpr -pp npt_processed.top -po npt_out.mdp
gmx mdrun -v -deffnm npt "${md_backend[@]}"
gmx energy -f npt.edr -o density.xvg
gmx energy -f npt.edr -o volume.xvg
gmx energy -f npt.edr -o pressure.xvg
```

分别按文件选择 **Density**、**Volume** 和 **Pressure**。确认温度、密度和体积没有持续漂移，检查压力时间平均与合理波动。瞬时压力可有较大波动。检查日志与结构后，再进入无位置限制试跑。

<a name="production"></a>

## 10. 短试跑、生产与续跑

- **输入** 经核验的平衡结构与检查点
- **输出** 输出生产轨迹和检查点
- **失败时的操作** 续跑前核对检查点和输出一致性

以下 20 ps 短试跑和 1 ns pilot 可用于验证解除位置限制后的数值稳定性及性能。对于已经有等效验收记录的体系，可从合格末态进入生产准备。检查展开 topology（拓扑）中的 `[ position_restraints ]`，并核查 LINCS、SETTLE 与非有限能量等异常。 [平衡与轨迹](TROUBLESHOOTING.zh-CN.md#simulation-errors)

**环境：** `docking-gromacs`。**预期文件或核查依据：** `topol.top`, `smoke.tpr`, `smoke_processed.top`。耗时和磁盘规划见快速入门的分阶段表。

```bash
gmx grompp -f smoke.mdp -c npt.gro -t npt.cpt -p topol.top -n index.ndx  -o smoke.tpr -pp smoke_processed.top -po smoke_out.mdp
grep -n 'position_restraints' smoke_processed.top
```

**环境：** `docking-gromacs`。**预期文件或核查依据：** 终端输出或下方命令指定的文件。耗时和磁盘占用取决于体系大小与模拟时长。

```bash
gmx mdrun -v -deffnm smoke "${md_backend[@]}"
```

**环境：** `docking-gromacs`。**预期文件或核查依据：** `topol.top`, `pilot.tpr`, `pilot_processed.top`。耗时和磁盘占用取决于体系大小与模拟时长。

```bash
gmx grompp -f pilot.mdp -c smoke.gro -t smoke.cpt -p topol.top -n index.ndx  -o pilot.tpr -pp pilot_processed.top -po pilot_out.mdp
gmx mdrun -v -deffnm pilot "${md_backend[@]}"
gmx check -f pilot.xtc
grep -A2 'Performance:' pilot.log
```

从选定的合格末态生成生产 TPR。示例用 `pilot`；若研究方案从通过验收的 NPT 末态开始，将其改为 `npt`，始终使用同一阶段配套的 GRO 和 CPT。核对处理后的 MDP、展开 topology（拓扑）与实际 TPR，并记录起点选择理由。

**环境：** `docking-gromacs`。**预期文件或核查依据：** `topol.top`, `md.tpr`, `md_processed.top`。耗时和磁盘规划见快速入门的分阶段表。

```bash
START=pilot
gmx grompp -f md.mdp -c "$START.gro" -t "$START.cpt" -p topol.top -n index.ndx  -o md.tpr -pp md_processed.top -po md_out.mdp
grep -n 'position_restraints' md_processed.top
grep -Ei '^[[:space:]]*(dt|nsteps|nstxout-compressed|compressed-x-grps)[[:space:]]*=' md_out.mdp
```

<a name="server-handoff"></a>

### 服务器交接与生产验收

**提交前** 保留 `md.tpr`、处理后的 MDP、起点 GRO 与 CPT、`index.ndx`、顶层 topology（拓扑）及全部 include 和 force field（力场）依赖。随包附软件版本、选定的起点和平衡验收依据。有校验清单时，上传后在目标服务器核对文件。参考验收时先读实际 TPR，再与处理后的 MDP 和展开 topology（拓扑）对照。

在目标机器的对应作业目录执行只读检查。若包中提供 `SHA256SUMS`，先执行校验。

**环境：** `docking-gromacs`。**预期文件或核查依据：** `md.tpr`。耗时和磁盘规划见快速入门的分阶段表。

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

| 验收项 | 实际核对 |
| --- | --- |
| 运行长度与输出 | 对照 `nsteps × dt`、坐标输出间隔、原子组和预期的起始步。 |
| 体系和约束 | 对照原子数、索引、温压耦合、topology（拓扑）中有效的位置限制与已选的键长约束。 |
| 起点与状态 | 核对 GRO/CPT 来源、复制后的校验值、生成或继承速度的设置，以及目标机的 TPR 可读性。 |

将状态记录为**已验收输入、运行中、生产完成**。生产完成以现场日志、实际步数与轨迹为依据。下方启动命令仅在计划提交正式生产时执行。若目标机读取失败或无法追加已有结果，先按排错页核对。<sup>[20](REFERENCES.zh-CN.md#ref-20)</sup> [gmx dump](https://manual.gromacs.org/documentation/current/onlinehelp/gmx-dump.html) · [GROMACS checkpoints and restart](https://manual.gromacs.org/documentation/current/user-guide/managing-simulations.html) · [服务器与续跑排错](TROUBLESHOOTING.zh-CN.md#server-errors)

**环境：** `docking-gromacs`。**预期文件或核查依据：** 终端输出或下方命令指定的文件。耗时和磁盘占用取决于体系大小与模拟时长。

```bash
gmx mdrun -v -deffnm md "${md_backend[@]}" -cpt 15
```

同一生产任务中断后，保留原始输出，确认 `md.cpt` 与生产段 TPR、日志和轨迹配套。若修改了运行设备或卸载配置，记录实际设置。GROMACS 找不到检查点时会从 TPR 的首步启动。下方的文件检查会在 `md.cpt` 缺失或为空时阻止启动。检查点无法找回时，在独立目录从已验收的起点重新运行，并单独记录。 [GROMACS 2026.3 mdrun](https://manual.gromacs.org/2026.3/onlinehelp/gmx-mdrun.html)

**环境：** `docking-gromacs`。**预期文件或核查依据：** 终端输出或下方命令指定的文件。耗时和磁盘占用取决于体系大小与模拟时长。

```bash
(
  set -e
  test -s md.cpt
  ls -lh md.cpt md.tpr md.log md.xtc
  gmx mdrun -v -deffnm md -cpi md.cpt -append "${md_backend[@]}" -cpt 15
)
```

### 延长已有生产模拟

原生产达到计划终点后，如需追加 10 ns，在同一重复目录运行。`-extend` 的单位是 ps。保留原 `md.tpr`，从延长后新的 TPR 继续，沿用 `-deffnm md` 和最新的 `md.cpt`。原输出有改名、缺失或校验失败时，先找回配套文件，或按手册用 `-noappend` 生成分段输出。延长过的任务再次中断时，应显式指定该次延长后的 TPR。 [GROMACS run management](https://manual.gromacs.org/2026.3/user-guide/managing-simulations.html)

**环境：** `docking-gromacs`。**预期文件或核查依据：** `md.tpr`, `md_extended.tpr`。耗时和磁盘占用取决于体系大小与模拟时长。

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

按日志和轨迹末帧核对达到预期步数与时间，再进入分析。若多次延长，从最近一次使用的 TPR 继续延长，并保留各次 TPR 和日志。

### 独立重复

独立重复在不同目录使用不同的 NVT `gen-seed`，例如 202601、202602、202603，分别完成 NVT、NPT 和后续模拟。根据研究问题决定是否使用不同起始姿态或对照。 [MD reliability and reproducibility checklist](https://www.nature.com/articles/s42003-023-04653-0)

[返回目录](../README.zh-CN.md#contents)
