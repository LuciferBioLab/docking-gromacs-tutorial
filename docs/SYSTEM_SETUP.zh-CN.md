# 力场与体系准备

[English](SYSTEM_SETUP.md) · **简体中文**

中英文同步于 2026-11-28。[已验证的工作流提交](https://github.com/LuciferBioLab/docking-gromacs-tutorial/commit/d139618900e79f0dc186d3bb64fbe5be4cc25914)。

[仓库首页](../README.zh-CN.md#contents)

<a name="topology"></a>

## 06. force field（力场）选择与配体参数化

- **输入** 已核查的配体和所选 force field（力场）
- **输出** 输出配体 GRO/ITP
- **失败时的操作** 排查缺参和电荷错误

| 路线 | 蛋白 force field（力场） | 小分子 force field（力场）与电荷 | 水和非键合参数 |
| --- | --- | --- | --- |
| A · AMBER | AMBER99SB-ILDN | GAFF2，AM1-BCC，经 AmberTools / ACPYPE | AMBER 端口的 TIP3P 与匹配离子，PME，示例 1.0 nm 截断 |
| B · CHARMM | MacKerell Lab GROMACS 端口的 CHARMM36m | 版本匹配的 CGenFF 类型、电荷和键合参数 | CHARMM TIP3P 与匹配离子，PME，普通截断端口用 1.0–1.2 nm 的 LJ 力切换 |

常规可溶蛋白和结构明确的有机配体可采用 A。实验室已有 CHARMM 体系、需与既有 CHARMM 模型对照，或采用 CHARMM36m 的理由明确且可获得质量合格的配体参数时，可用 B。两套 force field（力场）比较时固定化学状态和起始 docking pose（对接位姿），各自使用匹配的水、离子和非键合参数，并独立平衡。 [Amber manuals](https://ambermd.org/Manuals.php) · [GROMACS force-field notes](https://manual.gromacs.org/2026.3/user-guide/force-fields.html) · [MacKerell force-field ports](https://mackerell.umaryland.edu/charmm_ff.shtml)

### 路线 A · GAFF2 + AM1-BCC 配体

Open Babel 在这里仅做格式转换，保持已有 3D 几何。示例的 `-n 0` 适用于已确认的中性配体。根据配体实际整数净电荷改为 `-n -1`、`-n 1` 等。 [AmberTools](https://ambermd.org/AmberTools.php) · [ACPYPE quick start](https://acpype.readthedocs.io/en/latest/)

**环境：** `ligandtools`。**预期文件或核查依据：** 终端输出或下方命令指定的文件。耗时和磁盘规划见快速入门的分阶段表。

```bash
conda activate ligandtools
obabel lig_pose.sdf -O lig_pose.mol2
obabel lig_pose.mol2 -O lig_pose_roundtrip.sdf
obabel lig_pose.sdf -ocan
obabel lig_pose_roundtrip.sdf -ocan
obrms lig_pose.sdf lig_pose_roundtrip.sdf
```

先对照两份 SDF 的化学图、净电荷和手性，再看原位 heavy atom（重原子） RMSD 是否符合格式写出精度。`obrms` 在这里仅用于几何检查。核对通过后，运行 ACPYPE。

**环境：** `docking-gromacs`。**预期文件或核查依据：** 终端输出或下方命令指定的文件。耗时和磁盘规划见快速入门的分阶段表。

```bash
acpype -i lig_pose.mol2 -b LIG -a gaff2 -c bcc -n 0

ls -lh LIG.acpype
cp LIG.acpype/LIG_GMX.gro ligand.gro
cp LIG.acpype/LIG_GMX.itp ligand.itp
```

这条命令由 ACPYPE 调用 AmberTools。`antechamber` 分配 GAFF2 原子类型，`sqm` 参与 AM1-BCC 电荷流程，`parmchk2` 查找并补充缺失参数，`tleap` 生成 Amber topology（拓扑），ACPYPE 导出 GROMACS 坐标和 topology（拓扑）。<sup>[11](REFERENCES.zh-CN.md#ref-11),[12](REFERENCES.zh-CN.md#ref-12),[13](REFERENCES.zh-CN.md#ref-13),[14](REFERENCES.zh-CN.md#ref-14)</sup> [Amber manuals](https://ambermd.org/Manuals.php) · [ACPYPE source](https://github.com/alanwilter/acpype)

输出名以实际 ACPYPE 版本生成的文件为准。查阅 Antechamber、SQM、parmchk2 日志，审核原子类型和关键参数。在 `[ atoms ]` 中核对 partial charge（部分电荷）之和、原子顺序、名称和质量，并按映射比较 `ligand.gro` 与对接 SDF 的 heavy atom（重原子）坐标。SDF 通常用 Å，GRO 用 nm，且写出精度不同。坐标不符或映射不清时暂停建系。

### 路线 B · CGenFF 配体

**先选定一套相容的参数。** 在独立的路线 B 重复目录中操作。蛋白采用所选 GROMACS 移植包中的 CHARMM36m 定义，小分子采用已核验化学状态的 CGenFF stream，水和离子采用同一移植包的 CHARMM-modified TIP3P 与离子参数。归档原始 SDF、对接输出、提交给 CGenFF 的 MOL2 和返回的 stream。普通截断移植包使用第 08 节的截断 MDP 设置。CHARMM36 LJ-PME 移植包按其版本规定设置。 [MacKerell Lab CHARMM force-field releases](https://mackerell.umaryland.edu/charmm_ff.shtml)

1. 在当前 CHARMM 重复目录准备单个配体的 MOL2，保留明确的 bond order（键级）、手性、净电荷、显式氢和对接 heavy atom（重原子）位置。对照原 SDF 检查转换结果。<sup>[15](REFERENCES.zh-CN.md#ref-15),[16](REFERENCES.zh-CN.md#ref-16)</sup>

**环境：** `docktools`。**预期文件或核查依据：** 终端输出或下方命令指定的文件。耗时和磁盘规划见快速入门的分阶段表。

```bash
conda activate docktools
obabel lig_pose.sdf -O lig_pose.mol2 --title LIG
obabel lig_pose.sdf -ocan
obabel lig_pose.mol2 -ocan
```

2. 向 [CGenFF Service](https://cgenff.silcsbio.com/) 提交该 MOL2，保存包含配体 topology（拓扑）和附加参数的 CHARMM stream 文件为 `lig_pose.str`。记录 CGenFF 参数**版本**、`RESI` 名称、整数电荷与罚分。下例的 `LIG` 以 `RESI` 行的实际名称为准。高罚分提示类比参数需要复核，SilcsBio 指南中通常建议对大于 50 的条目进一步优化。 [CGenFF stream format and penalties](https://docs.silcsbio.com/2026/cgenff/usage.html)

**环境：** `Bash`。**预期文件或核查依据：** 终端输出或下方命令指定的文件。耗时和磁盘规划见快速入门的分阶段表。

```bash
grep -iE 'cgenff version|force field|^[[:space:]]*RESI[[:space:]]|penalty' lig_pose.str | head -30
```

3. 从 MacKerell 实验室获取与 stream **版本匹配**的 GROMACS 移植包。这里举例选择 2026 年 2 月、CGenFF 5.0 的普通截断版本，下面的 force field（力场）目录名使用同一个版本。如果 stream 来自 CGenFF 4.6，则按官网下载对应 4.6 包并在后续命令统一替换目录名。 [MacKerell lab force-field downloads](https://mackerell.umaryland.edu/charmm_ff.shtml)

**环境：** `Bash`。**预期文件或核查依据：** 终端输出或下方命令指定的文件。耗时和磁盘规划见快速入门的分阶段表。

```bash
curl --fail --location  'https://mackerell.umaryland.edu/download.php?filename=CHARMM_ff_params_files%2Fcharmm36-feb2026_cgenff-5.0.ff.tgz'  -o charmm36-feb2026_cgenff-5.0.ff.tgz
tar -tzf charmm36-feb2026_cgenff-5.0.ff.tgz | head -20
tar -xzf charmm36-feb2026_cgenff-5.0.ff.tgz
test -f charmm36-feb2026_cgenff-5.0.ff/forcefield.itp
sha256sum charmm36-feb2026_cgenff-5.0.ff.tgz
```

4. 安装 Lemkul Lab 转换工具，首次装一次。保存工具提交号及所用 force field（力场）压缩包的哈希。下面调用实验室提供的转换工具。 [Lemkul Lab converter](https://github.com/Lemkul-Lab/cgenff_charmm2gmx)

**环境：** `cgenff-tools`。**预期文件或核查依据：** 终端输出或下方命令指定的文件。耗时和磁盘规划见快速入门的分阶段表。

```bash
conda create -n cgenff-tools --override-channels -c conda-forge python=3.13 networkx numpy
mkdir -p "$HOME/tools"
git clone https://github.com/Lemkul-Lab/cgenff_charmm2gmx.git "$HOME/tools/cgenff_charmm2gmx"
git -C "$HOME/tools/cgenff_charmm2gmx" rev-parse HEAD > cgenff_converter_commit.txt
conda activate cgenff-tools
python "$HOME/tools/cgenff_charmm2gmx/cgenff_charmm2gmx.py"  LIG lig_pose.mol2 lig_pose.str charmm36-feb2026_cgenff-5.0.ff
ls -lh lig.itp lig.prm lig_ini.pdb
```

5. 用任一 GROMACS 构建把配体坐标转为 GRO，并核查 `lig.itp` 的原子顺序、电荷和配体质量。使用转换器生成的 `lig.prm` 保存全局参数。核对 `lig_ini.pdb` 和 `ligand.gro` 的原位坐标。转换器生成的单配体 TOP 可用于审查，其 `[ defaults ]`、`[ system ]` 和 `[ molecules ]` 由最终系统 TOP 统一管理。

**环境：** `gmx-cpu`。**预期文件或核查依据：** `ligand.gro`。耗时和磁盘规划见快速入门的分阶段表。

```bash
conda activate gmx-cpu
gmx editconf -f lig_ini.pdb -o ligand.gro
cp lig.itp ligand.itp
head -n 2 ligand.gro
```

#### 路线 B 复合物组装前验收

记录转换器提交号、GROMACS force field（力场）包校验值、CGenFF 参数版本、配体 `RESI` 名称、已核验的整数净电荷，以及高罚分条目的处理依据。提交和转换使用同一份 MOL2。若改动 MOL2，先核对原子名称及顺序与 stream 一致，再运行转换器。CGenFF 罚分反映类比赋参的不确定性。核查受影响的条目，并在需要时按 CGenFF 指南优化。 [CGenFF Usage and Penalties](https://docs.silcsbio.com/2026/cgenff/usage.html)

| 检查项 | 验收条件 |
| --- | --- |
| 化学与坐标 | 对照已核验的 SDF 检查提交的 MOL2 的 bond order（键级）、stereochemistry（立体化学）和 formal charge（形式电荷）。利用核实的 atom mapping（原子映射），在不叠合的情况下比较 `lig_ini.pdb` 与 `ligand.gro` 的 heavy atom（重原子）坐标，考虑 Å、nm 和文件写出精度。 |
| 局部 topology（拓扑） | 核对 `ligand.gro` 原子名称和顺序与 `ligand.itp` 的 `[ atoms ]` 一致。partial charge（部分电荷）之和应与核验的配体整数净电荷相符。若含虚拟位点，另行核对其映射。 |
| 体系 topology（拓扑） | 将 `lig.prm` 放在 CHARMM force field（力场） include 之后、首个 `[ moleculetype ]` 之前。加入 `ligand.itp`，并在 `[ molecules ]` 填入该配体的实际分子类型。平衡前检查 `grompp -pp` 展开的 topology（拓扑）。 [复合物组装](#complex-assembly) |
| 模拟设置 | 归档移植包的实际水和离子 include。对普通截断示例，在预处理后 MDP 核对 1.0–1.2 nm 的 LJ 力切换。 [运行参数](#simulation) |

下方命令核对单配体 GRO 和 ITP 的原子顺序及电荷和。若配体带电，把命令中的 `0` 换成已独立核验的整数净电荷。电荷容差是文件核验的示例设置。

**环境：** `docking-gromacs`。**预期文件或核查依据：** 终端输出或下方命令指定的文件。耗时和磁盘规划见快速入门的分阶段表。

```bash
python - 0 <<'PYTHON'
from math import fsum, isfinite
from pathlib import Path
import re
import sys

expected_charge = int(sys.argv[1])
gro = Path("ligand.gro").read_text().splitlines()
count = int(gro[1].strip())
if count < 1 or len(gro) != count + 3:
    raise SystemExit("Expected a nonempty single-frame ligand GRO file.")
observed_names = [line[10:15].strip() for line in gro[2 : 2 + count]]

section = None
atom_names = []
charges = []
for line in Path("ligand.itp").read_text().splitlines():
    row = line.partition(";")[0].strip()
    heading = re.fullmatch(r"\[\s*(\w+)\s*\]", row)
    if heading:
        section = heading[1].lower()
        continue
    if section != "atoms" or not row:
        continue
    if row.startswith("#"):
        raise SystemExit("Inspect the preprocessed topology for conditional atom rows.")
    fields = row.split()
    if len(fields) < 7 or int(fields[0]) != len(atom_names) + 1:
        raise SystemExit("Check [ atoms ] numbering and record fields.")
    atom_names.append(fields[4])
    charges.append(float(fields[6]))

if not charges or not all(map(isfinite, charges)):
    raise SystemExit("Missing or nonfinite partial charges.")
if observed_names != atom_names:
    raise SystemExit("GRO and ITP atom count, names, or order differ.")
charge_sum = fsum(charges)
if abs(charge_sum - expected_charge) > 0.01:
    raise SystemExit(f"Charge sum {charge_sum:.6f} differs from {expected_charge:+d}.")
print(f"Matched {count} atoms; total partial charge {charge_sum:.6f} e.")
PYTHON
```

**两条路线的配体检查** 将 `[ atoms ]` 的 partial charge（部分电荷）求和，与已确认的整数净电荷比较。对照原始坐标与参数输出，确认 heavy atom（重原子）映射、Å 到 nm 的单位转换，以及 GRO 行与 topology（拓扑）顺序。若参数化软件增加了虚拟粒子，核对其 topology（拓扑）定义与坐标顺序。

**环境：** `Bash`。**预期文件或核查依据：** 终端输出或下方命令指定的文件。耗时和磁盘规划见快速入门的分阶段表。

```bash
awk '/^[[:space:]]*\[[[:space:]]*atoms[[:space:]]*\]/{in_atoms=1;next}
     /^[[:space:]]*\[/{in_atoms=0}
     in_atoms && $1 ~ /^[0-9]+$/ {total+=$7; atoms++}
     END{if (!atoms) exit 1; printf "Atoms: %d; charge sum: %.6f\n", atoms,total}' ligand.itp
```

<a name="complex-assembly"></a>

## 07. 蛋白 topology（拓扑）、位置限制与原位组装

- **输入** 蛋白及配体坐标和 topology（拓扑）
- **输出** 输出组装复合物
- **失败时的操作** 错配时核对分子数量和顺序

在某一 force field（力场）的重复目录中准备蛋白 topology（拓扑）。按计划启用一个 GROMACS 构建。CHARMM 预处理和 AMBER 预处理均可使用 CPU 或 CUDA 构建提供的同一套命令。<sup>[17](REFERENCES.zh-CN.md#ref-17)</sup>

**CPU 版**

**环境：** `gmx-cpu`。**预期文件或核查依据：** 终端输出或下方命令指定的文件。耗时和磁盘规划见快速入门的分阶段表。

```bash
conda activate gmx-cpu
gmx --version
```

**CUDA 版**

**环境：** `docking-gromacs`。**预期文件或核查依据：** 终端输出或下方命令指定的文件。耗时和磁盘规划见快速入门的分阶段表。

```bash
source "$HOME/opt/gromacs-2026.3-cuda/bin/GMXRC"
gmx --version
```

**路线 A**

**环境：** `docking-gromacs`。**预期文件或核查依据：** `protein.gro`, `topol.top`。耗时和磁盘规划见快速入门的分阶段表。

```bash
gmx pdb2gmx -f protein.pdb -o protein.gro -p topol.top -i posre.itp  -ff amber99sb-ildn -water tip3p -ignh
cp topol.top topol_protein.top
```

**路线 B**

**环境：** `docking-gromacs`。**预期文件或核查依据：** `protein.gro`, `topol.top`。耗时和磁盘规划见快速入门的分阶段表。

```bash
gmx pdb2gmx -f protein.pdb -o protein.gro -p topol.top -i posre.itp  -ff charmm36-feb2026_cgenff-5.0 -water tip3p -ignh
cp topol.top topol_protein.top
```

两条路线均应核对末端、His、二硫键、链连接和 TIP3P 实际 include。需要显式指定 His 时检查当前 force field（力场）与 `pdb2gmx -h`。AMBER 特殊端基按该 force field（力场）的命名规则处理。 [pdb2gmx reference](https://manual.gromacs.org/current/onlinehelp/gmx-pdb2gmx.html)

`pdb2gmx -ignh` 会按所选残基状态重建氢。检查生成的所有蛋白链 topology（拓扑）及位置限制文件，并核对蛋白 heavy atom（重原子）的绝对位置。若有缺失 heavy atom（重原子），应在结构准备阶段处理。

**路线 A 的 topology（拓扑）编辑** 从 `ligand.itp` 把 `[ atomtypes ]` 及必要的全局类型定义移到 `ligand_atomtypes.itp`。核对 ACPYPE 和蛋白 force field（力场）的 `[ defaults ]`、组合规则及 1–4 缩放；系统只保留一套全局默认定义。如有同名类型或参数冲突，先解决再继续。蛋白 topology（拓扑）和水、离子 include 保留原样，以下是插入位置示意。若配体全局类型均已正确定义，省略相应 include。

```ini
#include "amber99sb-ildn.ff/forcefield.itp"
#include "ligand_atomtypes.itp"
; Existing protein molecule definitions and protein restraint includes
#include "ligand.itp"
; Existing water and ion includes

[ system ]
Protein-ligand complex

[ molecules ]
; Existing protein molecule names and counts, in their original order
LIG  1
```

**路线 B 的 topology（拓扑）编辑** 将转换器生成的 `lig.prm` 放在 CHARMM force field（力场）主 include 之后、首个 `[ moleculetype ]` 之前。保留蛋白链、水、离子及位置限制相关 include。按以下位置插入内容。

```ini
#include "charmm36-feb2026_cgenff-5.0.ff/forcefield.itp"
#include "lig.prm"
; Existing protein molecule definitions and protein restraint includes
#include "ligand.itp"
; Existing CHARMM TIP3P and ion includes

[ system ]
Protein-ligand complex

[ molecules ]
; Existing protein molecule names and counts, in their original order
LIG  1
```

两条路线的 `[ molecules ]` 都按“蛋白分子、配体分子、水、离子”与实际坐标对应。 [GROMACS topology formats](https://manual.gromacs.org/2026.3/reference-manual/topologies/topology-file-formats.html)

`LIG` 一行使用 `ligand.itp` 里 `[ moleculetype ]` 的**实际名称**。在 `ligand.gro` 上生成配体局部索引和 heavy atom（重原子）位置限制。GRO 的质量选择可能依赖名称推断，逐原子与 ITP 的质量列核对后，在 `gmx genrestr` 提示中选 `Ligand_heavy_local`。

**环境：** `docking-gromacs`。**预期文件或核查依据：** `ligand.gro`, `ligand_heavy_local.ndx`, `posre_ligand.itp`。耗时和磁盘规划见快速入门的分阶段表。

```bash
gmx select -s ligand.gro -select '"Ligand_heavy_local" mass > 2.5' -on ligand_heavy_local.ndx
gmx genrestr -f ligand.gro -n ligand_heavy_local.ndx -o posre_ligand.itp -fc 1000 1000 1000
```

在 `ligand.itp` 的配体分子定义末尾加入以下条件块。若已存在配体限制块，检查后使用唯一一套文件。配体限制编号为配体分子内部的编号。

```ini
#ifdef POSRES_LIG
#include "posre_ligand.itp"
#endif
```

下列命令按“蛋白所有原子 → 配体所有原子”保留原始坐标行。先确认两份文件各为单帧 GRO，第二行为原子数，文件总行数为原子数加 3。把合并结果与 `[ molecules ]` 顺序逐项对应。

**环境：** `Bash`。**预期文件或核查依据：** 终端输出或下方命令指定的文件。耗时和磁盘规划见快速入门的分阶段表。

```bash
head -n 2 protein.gro ligand.gro
wc -l protein.gro ligand.gro

protein_atoms=$(sed -n '2p' protein.gro | tr -d '[:space:]')
ligand_atoms=$(sed -n '2p' ligand.gro | tr -d '[:space:]')
solute_atoms=$((protein_atoms + ligand_atoms))

printf 'Protein-ligand complex\n%5d\n' "$solute_atoms" > complex_raw.gro
sed -n "3,$((protein_atoms + 2))p" protein.gro >> complex_raw.gro
sed -n "3,$((ligand_atoms + 2))p" ligand.gro >> complex_raw.gro
tail -n 1 protein.gro >> complex_raw.gro
wc -l complex_raw.gro
```

**验收** 合并后叠加检查配体仍在选定口袋。核对坐标顺序、原子数、电荷与 topology（拓扑）一致。盒子在下一阶段对整个复合物一起移动。

<a name="simulation"></a>

## 08. GROMACS 运行参数

- **输入** 相容参数体系和模拟目标
- **输出** 输出各阶段 MDP
- **失败时的操作** 排查无法识别或不相容的键

以下示例为 300 K、1 bar、0.15 M NaCl、PME 和 2 fs 时间步长的教学起点。先按给出的 AMBER 基线保存各文件，使用 CHARMM 时再按本节末尾更新非键合参数。按研究目的选择模拟长度和重复数，并记录所有改动。 [Versioned MDP options](https://manual.gromacs.org/2026.3/user-guide/mdp-options.html)

**温压耦合** 本节的 V-rescale 温控与 C-rescale 压控分别有原始方法论文。参数以所用版本的 MDP 手册为准。<sup>[18](REFERENCES.zh-CN.md#ref-18),[19](REFERENCES.zh-CN.md#ref-19)</sup> [V-rescale](https://doi.org/10.1063/1.2408420) · [C-rescale](https://doi.org/10.1063/5.0020514) · [GROMACS MDP reference](https://manual.gromacs.org/2026.3/user-guide/mdp-options.html)

### `ions.mdp` · 加离子预处理

此文件仅生成 `genion` 所需的 TPR。

```ini
integrator      = steep
nsteps          = 500
emtol           = 1000
emstep          = 0.01
cutoff-scheme   = Verlet
coulombtype     = Cut-off
rcoulomb        = 1.0
vdwtype         = Cut-off
rvdw            = 1.0
pbc             = xyz
constraints     = none
```

### `em.mdp` · 能量最小化

```ini
integrator      = steep
nsteps          = 50000
emtol           = 1000
emstep          = 0.01
cutoff-scheme   = Verlet
coulombtype     = PME
rcoulomb        = 1.0
vdwtype         = Cut-off
rvdw            = 1.0
DispCorr        = EnerPres
pbc             = xyz
constraints     = none
nstenergy       = 100
nstlog          = 100
```

### `nvt.mdp` · 控温平衡

```ini
define                  = -DPOSRES -DPOSRES_LIG
integrator              = md
dt                      = 0.002
nsteps                  = 50000
continuation            = no
constraints             = h-bonds
constraint-algorithm    = lincs
cutoff-scheme           = Verlet
nstlist                 = 20
coulombtype             = PME
rcoulomb                = 1.0
vdwtype                 = Cut-off
rvdw                    = 1.0
DispCorr                = EnerPres
pme-order               = 4
fourierspacing          = 0.12
pbc                     = xyz
tcoupl                  = V-rescale
tc-grps                 = Complex Water_and_ions
tau-t                   = 1.0 1.0
ref-t                   = 300 300
pcoupl                  = no
gen-vel                 = yes
gen-temp                = 300
gen-seed                = 202601
nstxout                 = 0
nstvout                 = 0
nstfout                 = 0
nstenergy               = 500
nstlog                  = 500
nstxout-compressed      = 500
```

### `npt.mdp` · 恒压平衡

复制 `nvt.mdp`，替换同名键并加入新的压力设置。删除 `gen-temp` 和 `gen-seed`，保留 `define`。

**环境：** `Bash`。**预期文件或核查依据：** 终端输出或下方命令指定的文件。耗时和磁盘规划见快速入门的分阶段表。

```bash
cp nvt.mdp npt.mdp
```

```ini
nsteps                  = 500000
continuation            = yes
gen-vel                 = no
pcoupl                  = C-rescale
pcoupltype              = isotropic
tau-p                   = 5.0
ref-p                   = 1.0
compressibility         = 4.5e-5
refcoord-scaling        = com
```

### `smoke.mdp`、`pilot.mdp`、`md.mdp` · 试跑和生产

从 `npt.mdp` 复制 `md.mdp`，选做短试跑时再准备 `smoke.mdp` 和 `pilot.mdp`。这些无位置限制阶段删除 `define` 和 `refcoord-scaling`，仍按 `constraints = h-bonds` 约束含氢共价键。按表修改已有键，每个键只出现一次。

**环境：** `Bash`。**预期文件或核查依据：** 终端输出或下方命令指定的文件。耗时和磁盘规划见快速入门的分阶段表。

```bash
cp npt.mdp md.mdp

# Optional smoke test and pilot
cp npt.mdp smoke.mdp
cp npt.mdp pilot.mdp
```

| 文件 | `nsteps` | 时长 | `nstenergy`, `nstlog`, `nstxout-compressed` |
| --- | ---: | ---: | ---: |
| `nvt.mdp` | 50,000 | 100 ps | 500 |
| `npt.mdp` | 500,000 | 1 ns | 500 |
| `smoke.mdp` | 10,000 | 20 ps | 500 |
| `pilot.mdp` | 500,000 | 1 ns | 500 |
| `md.mdp` | 50,000,000 | 100 ns | 5,000 |

MDP 中的整数直接写成 `50000000`，表中逗号仅用于阅读。100 ns 是命令示例。在积分步长为 2 fs 时，每 5,000 步输出一次，对应 10 ps 的帧间隔，按拟分析的时间尺度调整。

**轨迹保存间隔** 保存间隔由 `dt × nstxout-compressed` 决定。在 2 fs 下，`5000` 对应 10 ps，`15000` 对应 30 ps。根据拟分析的时间尺度、存储空间和实测写出大小选取。能量、日志和坐标的输出周期可分别设置。

本教程的后处理命令使用包含全体系原子的 XTC。若要使用相同流程，在生产 MDP 明确设置 `compressed-x-grps = System`，并用实际使用的索引核对该组包含全部原子。选择溶质子集输出时，配套导出同一原子顺序的结构或 topology（拓扑），并调整轨迹处理命令。 [GROMACS output control](https://manual.gromacs.org/documentation/current/user-guide/mdp-options.html)

### CHARMM36m + CGenFF 普通截断 MDP 设置

若选择路线 B 的普通截断 force field（力场）包，从上面的教学模板新建该路线自己的七个 MDP。将下面的键应用到 `ions.mdp`、`em.mdp`、`nvt.mdp`、`npt.mdp`、`smoke.mdp`、`pilot.mdp` 和 `md.mdp`。逐键替换已有值并添加缺失键。各阶段原有积分器、温压耦合、步数及位置限制设置分别保留。`ions.mdp` 只生成加离子 TPR，保留 `coulombtype = Cut-off`。其余六个文件保留 `coulombtype = PME`。 [GROMACS recommended CHARMM settings](https://manual.gromacs.org/2026.3/user-guide/force-fields.html)

```ini
rcoulomb       = 1.2
vdwtype        = Cut-off
vdw-modifier   = Force-switch
rvdw-switch    = 1.0
rvdw           = 1.2
DispCorr       = no
```

按当前 force field（力场）目录与 MDP 核对。LJ-PME 移植包须使用其自身设置。 [MacKerell port notes](https://mackerell.umaryland.edu/charmm_ff.shtml)

## 两套力场参数核查表

| 设置 | 路线 A | 路线 B，普通截断移植包 |
| --- | --- | --- |
| 蛋白 / 配体 | AMBER99SB-ILDN / GAFF2 + AM1-BCC | CHARMM36m / 版本相容的 CGenFF stream |
| 水与离子 | AMBER 移植包的 TIP3P 及配套离子 | CHARMM-modified TIP3P 及配套离子 |
| 教学设定值 | 300 K、1 bar、外加 0.15 M NaCl | 300 K、1 bar、外加 0.15 M NaCl |
| 溶剂化动力学步长 | 2 fs，采用适当含氢键约束 | 2 fs，采用适当含氢键约束 |
| PME 截断及 LJ | 1.0 nm 静电与 LJ 截断，按基准设置色散修正 | 1.2 nm 静电，LJ 1.0–1.2 nm 力切换，关闭解析色散修正 |
| 生产段示例输出 | 每 5,000 步，即 10 ps | 每 5,000 步，即 10 ps |

| 文件 | 路线 B 非键设置改动 | 按阶段核对的设置 |
| --- | --- | --- |
| ions.mdp | 替换上方六键，保持静电 Cut-off | 离子放置预处理与盒 |
| em.mdp | 替换上方六键，保留 PME | 最大力目标 |
| nvt.mdp | 替换上方六键，保留 PME | 位置限制、温控组、速度种子 |
| npt.mdp | 替换上方六键，保留 PME | 位置限制、压力、体积及续算 |
| smoke.mdp | 替换上方六键，保留 PME | 短时诊断与完整输出 |
| pilot.mdp | 替换上方六键，保留 PME | 无位置限制稳定性和资源测量 |
| md.mdp | 替换上方六键，保留 PME | 采样时长、输出步幅与检查点 |

LJ-PME 移植包调整色散算法与配套参数方案。使用适配的移植包及其说明，并核查处理后的 MDP。见[研究验证设计](RESEARCH.zh-CN.md#alternative-parameters)。
