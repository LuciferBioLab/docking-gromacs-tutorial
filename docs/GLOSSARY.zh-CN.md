# 术语表与命令参数

[English](GLOSSARY.md) · **简体中文**

[仓库首页](../README.zh-CN.md#contents)

<a name="glossary"></a>

## 核心术语

| 术语 | 定义 |
| --- | --- |
| PDBQT（AutoDock 坐标格式） | 记录坐标、partial charge（部分电荷）、原子类型及配体扭转树 |
| SDF（结构数据文件） | 保存坐标与化学图的分子记录 |
| MOL2（Tripos 分子格式） | 保存坐标、连通关系、类型和电荷 |
| docking pose（对接位姿） | 在 receptor（受体）坐标系下预测的配体取向和构象 |
| receptor（受体） | 采用确定建模状态的目标生物大分子 |
| force field（力场） | 势能模型及其参数集 |
| topology（拓扑） | 原子顺序、相互作用、参数和分子数量 |
| PME（粒子网格 Ewald） | 周期体系下电子静电相互作用的长程求和方法 |
| LJ-PME（Lennard–Jones 粒子网格 Ewald） | 长程色散的格点求和 |
| RESI（残基名称） | CHARMM 参数文件中的残基或配体标识 |
| GRO / TPR / CPT | GROMACS 坐标（nm）、运行输入和检查点 |
| XTC（压缩轨迹） | 有损压缩的坐标轨迹 |
| PLIP / ProLIF | 结构相互作用注释工具 / 轨迹和 docking pose（对接位姿）的相互作用指纹工具 |

<a name="flags"></a>

## 常用命令参数

| 参数 | 用途 |
| --- | --- |
| Vina `--receptor`、`--ligand`、`--config` | 设置对接 receptor（受体）、配体和搜索盒输入 |
| Vina `--seed`、`--exhaustiveness`、`--num_modes`、`--out` | 记录随机种子、调节搜索力度、限制输出模式数及指定文件 |
| GROMACS `-f`、`-c`、`-s`、`-p` | 按子命令查询：grompp 的 `-f`、`-c`、`-p` 分别是参数、坐标和 topology（拓扑）；多数分析的 `-f`、`-s` 分别是轨迹和 TPR/参考结构 |
| grompp `-r`、`-t`、`-n`、`-pp`、`-po`、`-o` | 输入限制参考、检查点及索引，记录展开的 topology（拓扑）、预处理参数和 TPR |
| mdrun `-deffnm`、`-ntmpi`、`-ntomp`、`-cpi` | 设定文件前缀、进程数、每进程线程数和续跑检查点 |
| GROMACS 2026.3 `hbond` 的 `-r`、`-t`、`-num` | 显式选择参考组与目标组，输出氢键数量随时间变化 |
| ACPYPE `-i`、`-b`、`-a`、`-c`、`-n` | MOL2 输入、输出前缀、GAFF 系列、电荷模型和已核验的配体总电荷 |

[GROMACS 2026.3 Manual](https://manual.gromacs.org/2026.3/) · [AutoDock Vina Documentation](https://autodock-vina.readthedocs.io/en/latest/)
