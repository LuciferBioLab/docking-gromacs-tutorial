# 常见问题

[English](FAQ.md) · **简体中文**

中英文同步于 2026-11-29。[已验证的工作流提交](https://github.com/LuciferBioLab/docking-gromacs-tutorial/commit/d139618900e79f0dc186d3bb64fbe5be4cc25914)。

[仓库首页](../README.zh-CN.md#contents)

<a name="faq"></a>

## 从哪里开始？

制备输入或复跑公开示例，请走[只做对接](QUICKSTART.zh-CN.md#dock)。已有审核过的位姿或建系文件，走[只做 MD](QUICKSTART.zh-CN.md#existing-pose)。已有轨迹或制图数据，走[分析或出图](QUICKSTART.zh-CN.md#existing-trajectory)。

## 先查哪一步？

找出第一个尚未完成的阶段，读最早的报错，再按工具版本、输入哈希、输出文件的顺序核对。运行对应的 `check_01.sh` 到 `check_12.sh`。见[报错索引](TROUBLESHOOTING.zh-CN.md#triage)。

## Meeko 为什么拒绝上游 PDB？

公开的 1IEP 输入有一条原子记录错位。Meeko 0.8.0 实际报错如下。

```text
ValueError: interrupted residues in PDB: {'A:438'}
```

示例仅对固定 receptor（受体）按原子序号恢复记录顺序，保持坐标不变，另存修复后的 PDB。其他含断链、替代构象或多模型的文件须独立审核。[输入来源](../examples/1iep/PROVENANCE.md)

## 配体为什么是 +1 电荷？

固定的上游 SDF 已指定质子化配体。先用 Open Babel 将 MOL2 往返回 SDF，再用 RDKit 查化学图和坐标。开发时 RDKit 直接读这份 MOL2 的实际报错如下。往返检验确认了目标阳离子。

```text
Explicit valence for atom # 16 N, 4, is greater than permitted
```

把核验后的电荷交给 ACPYPE。教程中的通用中性配体命令需根据实际体系调整。

## WSL2、引号和权限有哪些坑？

将 Linux 工作目录和活跃轨迹放在 WSL 文件系统。Windows 挂载盘会增加跨文件系统 I/O 开销，权限语义也可能不同。在 Bash 或 PowerShell 中给含空格的路径加引号。老版原生 Windows 工具解析路径失败时，先用短的 ASCII 路径隔离问题。Shell 脚本和文本配置用 LF、命令用普通 ASCII 引号；仓库已规定脚本行尾。容器和集群内用可写 scratch，并尽量以普通用户运行。[Microsoft WSL file-system guidance](https://learn.microsoft.com/windows/wsl/filesystems)

## 可以放过警告或从失败处继续吗？

GROMACS 预处理默认遇到警告便停止。先核对缺参、topology（拓扑）错配和无效限制。示例每次创建新目录；对于已验证的生产检查点，请使用[检查点续跑说明](SIMULATION.zh-CN.md#server-handoff)。归档原始输入、topology（拓扑）、MDP、TPR、CPT、抽样轨迹和日志，核验归档后再清理临时文件。

[提交可复现的问题](https://github.com/LuciferBioLab/docking-gromacs-tutorial/issues/new/choose)
