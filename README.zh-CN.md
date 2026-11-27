# 分子对接与 GROMACS 分子动力学

[English](README.md) · **简体中文**

面向可溶性蛋白–配体体系的可复现分子对接与分子动力学工作流。膜体系、共价配体、必需金属或辅因子、非标准残基需采用专用建模方案。公开 1IEP 示例采用已确定的 **+1** 配体微观状态。

[常见问题](docs/FAQ.zh-CN.md) · [版本矩阵](docs/QUICKSTART.zh-CN.md#version-matrix) · [验证范围](docs/QUICKSTART.zh-CN.md#validation-boundary)

**验证记录：** 2026-11-28，公开 1IEP 数据，Linux x86-64 CPU 路线。文档与可执行命令对应同一源码提交。

<a name="contact"></a>

## 联系

- [问题反馈](https://github.com/LuciferBioLab/docking-gromacs-tutorial/issues/new/choose)
- [lucifer.qsq@gmail.com](mailto:lucifer.qsq@gmail.com)
- [3069326069@qq.com](mailto:3069326069@qq.com)

![从分子对接到分子动力学](assets/workflow-cover.zh-CN.webp)

**核验 docking pose（对接位姿）交接。** 保留原始配体化学身份，通过 Meeko 元数据或 RDKit 显式原子映射回填对接坐标。[两套交接路线](docs/DOCKING.zh-CN.md#pose-handoff) · [Chem3D/PyMOL 对照](docs/TROUBLESHOOTING.zh-CN.md#chem3d-pymol-topology)。

<a name="start-here"></a>

## 从这里开始

1. **只做对接：** 使用 SHA-256 校验过的 1IEP 输入完成 01–05。[快速入门](docs/QUICKSTART.zh-CN.md#dock)。
2. **只做 MD：** 使用已核验的 docking pose（对接位姿）或已建系输入。[体系准备](docs/SYSTEM_SETUP.zh-CN.md#topology) · [快速入门](docs/QUICKSTART.zh-CN.md#quickstart-md)。
3. **只想出图：** 准备相互匹配的轨迹、topology（拓扑）和索引。[分析](docs/ANALYSIS.zh-CN.md#analysis)。

<a name="overview"></a>

![三条入门路线](assets/entry-map.zh-CN.png)

<a name="contents"></a>

## 目录

- [快速入门](docs/QUICKSTART.zh-CN.md)
- [文件地图与运行核查表](docs/WORKFLOW.zh-CN.md)
- [01–02 环境与重对接](docs/ENVIRONMENT.zh-CN.md)
- [03–05 制备与对接](docs/DOCKING.zh-CN.md)
- [06–08 力场与建系](docs/SYSTEM_SETUP.zh-CN.md)
- [09–10 平衡与生产](docs/SIMULATION.zh-CN.md)
- [11–12 分析与复现记录](docs/ANALYSIS.zh-CN.md)
- [术语与命令参数](docs/GLOSSARY.zh-CN.md)
- [研究扩展与验证](docs/RESEARCH.zh-CN.md)
- [多阶段对接验证](docs/DOCKING_VALIDATION.zh-CN.md)
- [排错与教程纠错](docs/TROUBLESHOOTING.zh-CN.md)
- [参考文献与引用](docs/REFERENCES.zh-CN.md)

1. [环境](docs/ENVIRONMENT.zh-CN.md#setup)
2. [参考重对接](docs/ENVIRONMENT.zh-CN.md#benchmark)
3. [结构制备](docs/DOCKING.zh-CN.md#docking)
4. [批量对接](docs/DOCKING.zh-CN.md#batch-docking)
5. [位姿交接](docs/DOCKING.zh-CN.md#pose-handoff)
6. [力场](docs/SYSTEM_SETUP.zh-CN.md#topology)
7. [复合物组装](docs/SYSTEM_SETUP.zh-CN.md#complex-assembly)
8. [运行参数](docs/SYSTEM_SETUP.zh-CN.md#simulation)
9. [平衡](docs/SIMULATION.zh-CN.md#equilibration)
10. [生产模拟](docs/SIMULATION.zh-CN.md#production)
11. [分析](docs/ANALYSIS.zh-CN.md#analysis)
12. [复现记录](docs/ANALYSIS.zh-CN.md#reproducibility)

[许可](LICENSE) · [CITATION.cff](CITATION.cff) · [更新记录](CHANGELOG.md) · [贡献规则](CONTRIBUTING.md)

<details>
<summary>旧版章节跳转</summary>

<a name="acknowledgments"></a>
- [acknowledgments](docs/REFERENCES.zh-CN.md#acknowledgments)
<a name="agent-workflow"></a>
- [agent-workflow](docs/ANALYSIS.zh-CN.md#agent-workflow)
<a name="analysis"></a>
- [analysis](docs/ANALYSIS.zh-CN.md#analysis)
<a name="batch-docking"></a>
- [batch-docking](docs/DOCKING.zh-CN.md#batch-docking)
<a name="benchmark"></a>
- [benchmark](docs/ENVIRONMENT.zh-CN.md#benchmark)
<a name="chem3d-pymol-topology"></a>
- [chem3d-pymol-topology](docs/TROUBLESHOOTING.zh-CN.md#chem3d-pymol-topology)
<a name="complex-assembly"></a>
- [complex-assembly](docs/SYSTEM_SETUP.zh-CN.md#complex-assembly)
<a name="complex-systems"></a>
- [complex-systems](docs/TROUBLESHOOTING.zh-CN.md#complex-systems)
<a name="conformer-preparation"></a>
- [conformer-preparation](docs/DOCKING_VALIDATION.zh-CN.md#conformer-preparation)
<a name="disclaimer"></a>
- [disclaimer](docs/REFERENCES.zh-CN.md#disclaimer)
<a name="docking"></a>
- [docking](docs/DOCKING.zh-CN.md#docking)
<a name="docking-errors"></a>
- [docking-errors](docs/TROUBLESHOOTING.zh-CN.md#docking-errors)
<a name="endpoint-energy"></a>
- [endpoint-energy](docs/ANALYSIS.zh-CN.md#endpoint-energy)
<a name="equilibration"></a>
- [equilibration](docs/SIMULATION.zh-CN.md#equilibration)
<a name="figure-layout"></a>
- [figure-layout](docs/ANALYSIS.zh-CN.md#figure-layout)
<a name="interaction-review"></a>
- [interaction-review](docs/DOCKING_VALIDATION.zh-CN.md#interaction-review)
<a name="legacy-adt-handoff"></a>
- [legacy-adt-handoff](docs/DOCKING.zh-CN.md#legacy-adt-handoff)
<a name="local-inputs"></a>
- [local-inputs](docs/DOCKING.zh-CN.md#local-inputs)
<a name="method-evidence"></a>
- [method-evidence](docs/REFERENCES.zh-CN.md#method-evidence)
<a name="pose-handoff"></a>
- [pose-handoff](docs/DOCKING.zh-CN.md#pose-handoff)
<a name="pose-validation"></a>
- [pose-validation](docs/DOCKING_VALIDATION.zh-CN.md#pose-validation)
<a name="production"></a>
- [production](docs/SIMULATION.zh-CN.md#production)
<a name="publication-figures"></a>
- [publication-figures](docs/ANALYSIS.zh-CN.md#publication-figures)
<a name="pymol-image-export"></a>
- [pymol-image-export](docs/ANALYSIS.zh-CN.md#pymol-image-export)
<a name="receptor-repair"></a>
- [receptor-repair](docs/DOCKING_VALIDATION.zh-CN.md#receptor-repair)
<a name="references"></a>
- [references](docs/REFERENCES.zh-CN.md#references)
<a name="reproducibility"></a>
- [reproducibility](docs/ANALYSIS.zh-CN.md#reproducibility)
<a name="server-errors"></a>
- [server-errors](docs/TROUBLESHOOTING.zh-CN.md#server-errors)
<a name="server-handoff"></a>
- [server-handoff](docs/SIMULATION.zh-CN.md#server-handoff)
<a name="setup"></a>
- [setup](docs/ENVIRONMENT.zh-CN.md#setup)
<a name="simulation"></a>
- [simulation](docs/SYSTEM_SETUP.zh-CN.md#simulation)
<a name="simulation-errors"></a>
- [simulation-errors](docs/TROUBLESHOOTING.zh-CN.md#simulation-errors)
<a name="sources"></a>
- [sources](docs/REFERENCES.zh-CN.md#sources)
<a name="tiled-search"></a>
- [tiled-search](docs/DOCKING_VALIDATION.zh-CN.md#tiled-search)
<a name="toolchain"></a>
- [toolchain](docs/WORKFLOW.zh-CN.md#toolchain)
<a name="topology"></a>
- [topology](docs/SYSTEM_SETUP.zh-CN.md#topology)
<a name="topology-errors"></a>
- [topology-errors](docs/TROUBLESHOOTING.zh-CN.md#topology-errors)
<a name="triage"></a>
- [triage](docs/TROUBLESHOOTING.zh-CN.md#triage)
<a name="troubleshooting-contents"></a>
- [troubleshooting-contents](docs/TROUBLESHOOTING.zh-CN.md#troubleshooting-contents)
<a name="tutorial-error-flow"></a>
- [tutorial-error-flow](docs/TROUBLESHOOTING.zh-CN.md#tutorial-error-flow)
<a name="validation-references"></a>
- [validation-references](docs/DOCKING_VALIDATION.zh-CN.md#validation-references)
<a name="validation-triage"></a>
- [validation-triage](docs/DOCKING_VALIDATION.zh-CN.md#validation-triage)
<a name="tutorial-error-flow"></a>
- [tutorial-error-flow](docs/TROUBLESHOOTING.zh-CN.md#tutorial-error-flow)
<a name="chem3d-pymol-topology"></a>
- [chem3d-pymol-topology](docs/TROUBLESHOOTING.zh-CN.md#chem3d-pymol-topology)

</details>
