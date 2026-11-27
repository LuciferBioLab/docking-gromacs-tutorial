# 复杂体系与研究扩展

[English](RESEARCH.md) · **简体中文**

中英文同步于 2026-11-28。[已验证的工作流提交](https://github.com/LuciferBioLab/docking-gromacs-tutorial/commit/d139618900e79f0dc186d3bb64fbe5be4cc25914)。

[仓库首页](../README.zh-CN.md#contents)

<a name="sampling"></a>

## 采样与基准设计

| 检查点 | 记录的证据 | 失败后的操作 |
| --- | --- | --- |
| 能量最小化 | 最大力、能量趋势、局部冲突 | 动力学模拟前定位问题原子及参数 |
| NVT | 目标温度附近的波动、能量及限制行为 | 检查温控组、时间步长和初始速度 |
| NPT | 分窗统计密度和体积、温度、压力均值和波动 | 复核溶剂化、压控、限制和初始松弛 |
| 生产模拟 | 蛋白叠合后的配体 RMSD、位移、接触及分块不确定度 | 检查跳变和状态转换；结论受不确定度影响时延长采样或增加重复 |

探索性比较可从至少三个独立初始化的轨迹开始。说明各重复改变了什么，先逐条分析，再考虑合并。剔除预先声明的平衡段，比较连续分块均值，增大分块长度直到不确定度估计稳定，并核对采样是否覆盖研究问题需要的状态。RMSD 平台只是一个诊断项。密度与压力的统计特性取决于体系、大小和系综，按方案及目标观测量精度定义容许范围。<sup>[R1](#research-ref-1)</sup>

<a name="complex-systems"></a>

## 复杂体系参数化前的最低核查

| 体系 | 最低核查 |
| --- | --- |
| 多链或多聚体 | 获取生物学组装，核对链 ID 与 TER；保留界面相关链；确定末端和链间共价连接 |
| 膜体系 | 核对膜中朝向、膜组成及相容的脂质和离子参数；采用膜体系平衡方案，核验盒尺寸与膜性质 |
| 必需金属或辅因子 | 保留配位几何、辅因子化学图与氧化/质子化状态；为对应元素、配位与 force field（力场）选择有验证的模型 |
| 共价配体 | 确认反应产物、原子电荷、键图和残基命名；选用适配的共价对接和参数化方法 |
| 缺失或非标准残基 | 复核密度/序列信息、替代状态和断裂；验证建模区域，按需补充明确的 force field（力场）条目 |

以下 GROMACS 2026.3 示例按链 ID 变化或 TER 分链，分别生成链的 topology（拓扑）。用于已确认这些位置确为独立化学链的组装。遇到链间二硫键或其他共价连接时，先确认连接，根据方案判断是否需要合并链，再核对展开 topology（拓扑）里的键和分子数量。<sup>[R2](#research-ref-2)</sup>

```bash
gmx pdb2gmx -f reviewed_assembly.pdb -o protein.gro -p protein.top -ff amber99sb-ildn -water tip3p -chainsep id_or_ter -merge no
```

输入为已核查的组装。输出为 GRO 和各链 topology（拓扑）。核对末端、二硫键、残基日志及链与分子数量；遇到缺原子或无法识别的残基时先停止。耗时和磁盘占用取决于组装大小。

<a name="alternative-parameters"></a>

## 参数化路线与 AMBER–CHARMM 配对比较

根据研究方案选定蛋白 force field（力场），以及同体系的配体、水和离子参数。公开 CPU 短测试用 AMBER99SB-ILDN、GAFF2 和 AM1-BCC。CHARMM 参考路线采用 CHARMM36m、CGenFF，以及所选普通截断移植包的 CHARMM-modified TIP3P 和离子参数。记录确切的参数版本并归档 CGenFF 原子映射与惩分。参考 CGenFF 指南，低于 10 表示相近类比，10–50 建议验证所分配参数，高于 50 优先详细验证或重新参数化。重要扭转和电荷即使惩分较低，也要优先核对。<sup>[R3](#research-ref-3)</sup>

分别建两个运行目录。匹配原始化学图、docking pose（对接位姿）坐标、温度、盐目标、模拟时长预算和所分析的观测量；各自采用其 force field（力场）配套参数和切换方式。比较各重复的配体 RMSD、接触、密度分布与不确定度。已实测的是公开 AMBER CPU 短测试。配对的 CGenFF 分支需先取得已核查的 stream 及相应普通截断移植包。

OpenFF Sage 和 OpenFF Interchange 可以将相容的小分子体系导出至 GROMACS。LigParGen 可用于相容的 OPLS-AA 路线。组装前核对函数形式、组合规则、1–4 缩放、电荷和 topology（拓扑）与坐标顺序。<sup>[R4](#research-ref-4),[R5](#research-ref-5)</sup>

<a name="interaction-analysis"></a>

## 接触分析与出图证据

用已核查轨迹中匹配的复合物帧作为 PLIP 输入，保留链与残基标识。在[开源 PyMOL](https://github.com/schrodinger/pymol-open-source)中核对候选相互作用。用 ProLIF 建逐帧相互作用指纹，以出现帧数除以分析帧数计算占有率。报告采样窗、步幅、PBC 处理、质子化状态、相互作用类型和阈值。注明缺原子和不确定的配体选择。<sup>[R6](#research-ref-6),[R7](#research-ref-7)</sup>

```bash
plip -f analysis/complex.pdb -o analysis/plip -x
```

在重复目录中用独立环境执行 PLIP。输出 XML 报告。PLIP 2.4.0 已在公开 1IEP 短测试的单帧完成分析。按该工具的原子分类与几何规则，得到 4 条氢键、11 个疏水接触与 1 个 π 堆积事件。[核验结果](../examples/expected/plip-summary.csv) · [Adasme et al., PLIP 2021](https://doi.org/10.1093/nar/gkab294)。单帧用于结构注释，占有率用 ProLIF 轨迹工作流计算。时间与磁盘占用随帧数和接触数量改变。投稿时保留导出的图与可编辑布局，成图尺寸、分辨率和字形遵循期刊要求。用 Inkscape 组装矢量图，用 GIMP 或 Krita 整理栅格图像。见[出图和 agent 说明](ANALYSIS.zh-CN.md#agent-workflow)。

<a name="free-energy"></a>

## CHARMM 端点法与炼金自由能扩展

单独建结果目录，用 gmx_MMPBSA 上游 CHARMM 可溶蛋白–小分子例先验证环境兼容性。用匹配 TPR 对全系统 XTC 做周期性边界修复和抽样，核对 receptor（受体）和配体的组编号，使用相应的展开 CHARMM topology（拓扑）。GB 分支按安装版本核对允许的半径及 GB 模型。PB 分支记录离子强度、半径、溶剂与溶质介电常数及抽样间隔。示例 0.15 M 表示体相盐浓度，显式体系的离子总数另计。从实际运行选组和时间窗，再核查转换日志和逐帧输出。<sup>[R8](#research-ref-8)</sup>

对 gmx_MMPBSA 1.7.0，可将以下起始设置保存为 `charmm_pbsa.in`。`PBRadii=7` 分配 CHARMM 专用半径，`radiopt=0` 让 PBSA 使用转换后的 topology（拓扑）中保存的半径。转换程序省略 CHARMM CMAP 项，解释定量端点能量前须评估这一限制。<sup>[R8](#research-ref-8)</sup>

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

运行前按已核对的索引设置两个组编号变量。[端点法教程](ANALYSIS.zh-CN.md#endpoint-energy)给出输入格式和环境方法。四帧设置用于说明软件兼容性核验。上游示例使用 `Protein` 与 `JZ4` 两组、`com.tpr`、`com_traj.xtc` 和带有 `toppar/` 配套文件的 `topol.top`。扩大分析窗前，先核对摘要与逐帧 CSV 对应的组和帧数。这里的设置已对照上游示例。本仓库尚无独立的 CHARMM 端点法实测结果。<sup>[R8](#research-ref-8)</sup>

相对炼金结合自由能适合定义明确、参数化一致并已确定原子映射的同系列配体。绝对结合自由能需要单独的约束和标准态方案。两种方案均需诊断状态重叠与收敛。AI 对接模型可用于补充候选 docking pose（对接位姿），并通过独立重对接和化学、几何核查验证。<sup>[R9](#research-ref-9)</sup>

<a name="research-references"></a>

## 参考文献与官方文档

- <a name="research-ref-1"></a> [Grossfield et al. Best Practices for Quantification of Uncertainty and Sampling Quality in Molecular Simulations](https://doi.org/10.33011/livecoms.1.1.5067)
- <a name="research-ref-2"></a> [GROMACS 2026.3 pdb2gmx](https://manual.gromacs.org/2026.3/onlinehelp/gmx-pdb2gmx.html)
- <a name="research-ref-3"></a> [MacKerell Lab CHARMM parameter sets and GROMACS ports](https://mackerell.umaryland.edu/charmm_ff.shtml) · [CGenFF tutorial](https://docs.silcsbio.com/2026/cgenff/usage.html)
- <a name="research-ref-4"></a> [OpenFF Interchange](https://github.com/openforcefield/openff-interchange)
- <a name="research-ref-5"></a> [LigParGen](https://doi.org/10.1093/nar/gkx312)
- <a name="research-ref-6"></a> [Salentin et al. PLIP: fully automated protein–ligand interaction profiler](https://doi.org/10.1093/nar/gkv315) · [PLIP GitHub](https://github.com/pharmai/plip)
- <a name="research-ref-7"></a> [Bouysset and Fiorucci. ProLIF: a library to encode molecular interactions as fingerprints](https://doi.org/10.1186/s13321-021-00548-6) · [ProLIF Documentation](https://prolif.readthedocs.io/)
- <a name="research-ref-8"></a> [gmx_MMPBSA 1.7.0 CHARMM protein–ligand example](https://valdes-tresanco-ms.github.io/gmx_MMPBSA/1.7.0/examples/Protein_ligand_CHARMMff/)
- <a name="research-ref-9"></a> [Mey et al. Best Practices for Alchemical Free Energy Calculations](https://doi.org/10.33011/livecoms.2.1.18378)
