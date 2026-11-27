# 环境与共晶重对接

[English](ENVIRONMENT.md) · **简体中文**

[仓库首页](../README.zh-CN.md#contents)

<a name="setup"></a>

## 01. 环境与安装

- **输入** Linux/WSL2 环境
- **输出** 生成已注明版本的软件环境
- **失败时的操作** 有解算报错时先排查再制备结构

### Linux 服务器

从 [Miniforge Releases](https://github.com/conda-forge/miniforge/releases) 选择与系统和架构匹配的安装包，并按发布页提供的信息校验。下文使用 Bash，默认在项目根目录操作，遇到报错时先检查该步。软件示例使用 Vina 1.2.7、Uni-Dock 1.2.0 和 GROMACS 2026.3 的命令语法。已安装 Miniforge 时直接创建环境。

Linux x86-64 安装示例如下，其他架构请替换安装包名。

**环境：** `Bash`。**预期文件或核查依据：** 终端输出或下方命令指定的文件。耗时和磁盘规划见快速入门的分阶段表。

```bash
bash Miniforge3-Linux-x86_64.sh -b -p "$HOME/miniforge3"
source "$HOME/miniforge3/etc/profile.d/conda.sh"
```

**环境：** `docktools, ligandtools, gmx-cpu`。**预期文件或核查依据：** 终端输出或下方命令指定的文件。耗时和磁盘规划见快速入门的分阶段表。

```bash
conda create -n docktools --override-channels -c conda-forge python=3.11 vina=1.2.7 meeko rdkit gemmi openbabel
conda create -n ligandtools --override-channels -c conda-forge ambertools acpype openbabel
conda create -n gmx-cpu --override-channels -c conda-forge gromacs=2026.3

conda activate docktools
vina --version
mk_prepare_receptor.py --help
mk_prepare_ligand.py --help
mk_export.py --help

conda activate ligandtools
command -v antechamber parmchk2 tleap sqm acpype obabel
acpype -h

conda activate gmx-cpu
gmx --version
```

如需枚举配体的质子化与互变异构状态，在 `docktools` 环境安装 Molscrub，运行 `scrub.py --help` 和 `python -m pip check` 核对依赖。遇到平台或版本求解问题，按各项目安装文档选择兼容版本并记录。 [Molscrub installation](https://github.com/forlilab/molscrub) · [Vina releases](https://github.com/forlilab/AutoDock-Vina/releases) · [conda-forge GROMACS](https://anaconda.org/conda-forge/gromacs)

**环境：** `docktools`。**预期文件或核查依据：** 终端输出或下方命令指定的文件。耗时和磁盘规划见快速入门的分阶段表。

```bash
conda activate docktools
python -m pip install molscrub
python -m pip check
scrub.py --help
```

### NVIDIA CUDA 对接环境

在 Linux GPU 节点执行下面命令。Windows 用户先完成本节末尾的 WSL2 设置，再从 WSL Bash 执行同样命令。示例使用 conda-forge 的 Linux x86-64 Uni-Dock 1.2.0 包。先确认驱动能运行实际选用的 CUDA runtime。预编译包会安装所需的运行时依赖，`nvcc` 用于源码编译。 [Uni-Dock release notes](https://github.com/dptech-corp/Uni-Dock/releases) · [conda-forge builds](https://anaconda.org/conda-forge/unidock/files) · [NVIDIA CUDA compatibility](https://docs.nvidia.com/deploy/cuda-compatibility/latest/minor-version-compatibility.html)

**环境：** `dockgpu`。**预期文件或核查依据：** 终端输出或下方命令指定的文件。耗时和磁盘规划见快速入门的分阶段表。

```bash
nvidia-smi
conda create -n dockgpu --override-channels -c conda-forge 'unidock=1.2.0'
conda activate dockgpu
command -v unidock
unidock --help
conda list --show-channel-urls unidock
```

`nvidia-smi` 标题中的 CUDA Version 表示驱动支持的 CUDA 版本，Toolkit 安装可另用 `nvcc --version` 核实。若解算或运行报 CUDA 兼容错误，请查看实际包的 CUDA 构建号和 GPU 节点驱动，选择两者兼容的版本。命令帮助可验证软件安装，步骤 02 的对接运行用于验证 GPU。 [NVIDIA nvidia-smi documentation](https://docs.nvidia.com/deploy/nvidia-smi/)

### GROMACS CUDA 构建

在允许使用 GPU 的计算节点检查 `nvidia-smi`。如需自行编译，选择 GROMACS 安装手册支持的 CUDA Toolkit、C/C++ 编译器和 CMake。使用上游源码压缩包解压后的目录执行以下命令。已有集群软件模块时，可直接加载并核对版本及 GPU 后端。 [GROMACS website](https://www.gromacs.org/) · [2026.3 build guide](https://manual.gromacs.org/2026.3/install-guide/index.html) · [GPU performance guide](https://manual.gromacs.org/documentation/current/user-guide/mdrun-performance.html)

**环境：** `docking-gromacs`。**预期文件或核查依据：** 终端输出或下方命令指定的文件。耗时和磁盘规划见快速入门的分阶段表。

```bash
nvidia-smi
nvcc --version
cmake --version
cmake -S . -B build-cuda -DGMX_GPU=CUDA -DGMX_BUILD_OWN_FFTW=ON  -DREGRESSIONTEST_DOWNLOAD=ON -DCMAKE_INSTALL_PREFIX="$HOME/opt/gromacs-2026.3-cuda"
cmake --build build-cuda --parallel 4
cmake --build build-cuda --target check
cmake --install build-cuda

source "$HOME/opt/gromacs-2026.3-cuda/bin/GMXRC"
gmx --version
```

切换到 MD 阶段时，选择一个 GROMACS 环境并用 `command -v gmx` 确认。集群上在调度器分配的计算节点运行，线程数以作业配额为准。 [Slurm documentation](https://slurm.schedmd.com/documentation.html)

### Windows + WSL2

从 PowerShell 检查 WSL。若尚未安装，可执行第二个代码块并按提示重启。此后在 Ubuntu 的 WSL Bash 中执行 Linux 步骤，项目与轨迹存放在 Linux 文件系统，例如 `~/docking-md-workshop`。 [Microsoft WSL installation](https://learn.microsoft.com/windows/wsl/install) · [WSL filesystems](https://learn.microsoft.com/windows/wsl/filesystems)

**环境：** `PowerShell`。**预期文件或核查依据：** 终端输出或下方命令指定的文件。耗时和磁盘规划见快速入门的分阶段表。

```powershell
wsl --status
wsl -l -v
```

**环境：** `PowerShell`。**预期文件或核查依据：** 终端输出或下方命令指定的文件。耗时和磁盘规划见快速入门的分阶段表。

```powershell
wsl --install -d Ubuntu
```

在 **Windows 宿主机**安装支持 WSL 的 NVIDIA 驱动，并在 WSL Bash 运行 `nvidia-smi`。通过后可按上面的命令装 Uni-Dock CUDA，或选择 CPU 路线。需要源码编译时按 NVIDIA 指引安装 WSL Toolkit，选用不捆绑 Linux 显卡驱动的包。原生 Windows 版 Vina 1.2.7 可走步骤 04A，CUDA 对接走步骤 04B。 [NVIDIA CUDA on WSL](https://docs.nvidia.com/cuda/wsl-user-guide/index.html) · [Vina batch syntax on Windows](https://autodock-vina.readthedocs.io/en/latest/docking_in_batch.html)

<a name="benchmark"></a>

## 02. 参考案例重对接

- **输入** 校验过的公开输入
- **输出** 输出重对接位姿与 RMSD
- **失败时的操作** 找不到参考位姿时核对化学身份和盒几何

先用 Scripps 官方示例复跑 c-Abl 与伊马替尼（PDB **1IEP**）。从官方示例目录下载 `1iep_receptorH.pdb` 和 `1iep_ligand.sdf` 到一个新目录，在该目录运行以下命令。此处的盒坐标只适用于该示例坐标系。<sup>[2](REFERENCES.zh-CN.md#ref-2),[3](REFERENCES.zh-CN.md#ref-3),[4](REFERENCES.zh-CN.md#ref-4)</sup> [Official walkthrough](https://autodock-vina.readthedocs.io/en/latest/docking_basic.html) · [Upstream example files](https://github.com/forlilab/AutoDock-Vina/tree/develop/example/basic_docking) · [RCSB 1IEP](https://www.rcsb.org/structure/1IEP)

**结构来源与验证依据** 记录 1IEP 的结构 DOI 和参考配体实例。报告重对接 RMSD 时，注明原子匹配与对称性处理方法。<sup>[5](REFERENCES.zh-CN.md#ref-5)</sup> [1IEP structure DOI](https://doi.org/10.2210/pdb1IEP/pdb) · [DockRMSD methodology](https://doi.org/10.1186/s13321-019-0362-7)

手工比较从仓库根目录运行。排序修复只用于已校验的固定示例。默认 CPU 设置请使用[实测的五条命令快速入门](QUICKSTART.zh-CN.md#dock)。

**环境：** `docktools`。**预期文件或核查依据：** `1iep_ligand.pdbqt`。耗时和磁盘规划见快速入门的分阶段表。

```bash
conda activate docktools
python scripts/example_io.py order-example examples/1iep/1iep_receptorH.pdb 1iep_receptor_ordered.pdb
mk_prepare_receptor.py --read_pdb 1iep_receptor_ordered.pdb -o 1iep_receptor -p -v  --box_size 20 20 20 --box_center 15.190 53.903 16.917
mk_prepare_ligand.py -i examples/1iep/1iep_ligand.sdf -o 1iep_ligand.pdbqt
```

**CPU：AutoDock Vina**

**环境：** `docking-gromacs`。**预期文件或核查依据：** `1iep_docked.pdbqt`, `1iep_docked.sdf`。耗时和磁盘规划见快速入门的分阶段表。

```bash
vina --receptor 1iep_receptor.pdbqt --ligand 1iep_ligand.pdbqt  --config 1iep_receptor.box.txt --scoring vina --cpu 4 --seed 202601  --exhaustiveness 32 --out 1iep_docked.pdbqt
mk_export.py 1iep_docked.pdbqt -s 1iep_docked.sdf
```

**GPU：Uni-Dock CUDA**

**环境：** `dockgpu`。**预期文件或核查依据：** 终端输出或下方命令指定的文件。耗时和磁盘规划见快速入门的分阶段表。

```bash
conda activate dockgpu
mkdir 1iep_gpu
unidock --receptor 1iep_receptor.pdbqt --gpu_batch 1iep_ligand.pdbqt  --config 1iep_receptor.box.txt --scoring vina --search_mode balance  --num_modes 20 --seed 202601 --dir 1iep_gpu > 1iep_gpu/unidock.log 2>&1
tail -25 1iep_gpu/unidock.log
find 1iep_gpu -maxdepth 1 -type f -name '*.pdbqt' -print
```

用步骤 05 的检查和导出方式处理 GPU 输出。对接命令成功退出后，用 docking pose（对接位姿）文件、日志和 GPU 观测共同核对。

**验收** 确认 PDBQT 有 Vina 分数和姿态，SDF 可以读取。分别用公开参考结果检查 CPU 和 GPU 的 docking pose（对接位姿）与关键接触。正式做共晶重对接时，先把参考与对接结构置于同一 receptor（受体）坐标系，比较带对称校正的 heavy atom（重原子） RMSD，保持配体在各自原位。约 2 Å 是常用参考值。可另用 BioExcel 的公开案例练习 MD 复合物建系。 [Scripps expected results](https://autodock-vina.readthedocs.io/en/latest/docking_basic.html#expected-results) · [BioExcel complex setup](https://github.com/bioexcel/biobb_wf_protein-complex_md_setup)

**定量重对接** 在 RCSB 1IEP 的 **Small Molecules → STI → Instance Coordinates** 下载对应链的 SDF，保存为 `1iep_crystal_ligand.sdf`。在结构查看器里确认其链/构象对应 receptor（受体），并把两者置于同一 receptor（受体）坐标系。先核对化学身份，再用 Open Babel 的 `obrms` 对每个对接姿态计算 heavy atom（重原子） RMSD（Å）。`obrms` 按 heavy atom（重原子）连接匹配并考虑等价映射，`-m` 会对配体再拟合，此处省略该选项。<sup>[6](REFERENCES.zh-CN.md#ref-6)</sup> [RCSB 1IEP](https://www.rcsb.org/structure/1IEP) · [Open Babel obrms](https://github.com/openbabel/openbabel/blob/master/tools/obrms.cpp)

**环境：** `docktools`。**预期文件或核查依据：** 终端输出或下方命令指定的文件。耗时和磁盘规划见快速入门的分阶段表。

```bash
conda activate docktools
obabel examples/regression/1iep/crystal_ligand.sdf -ocan
obabel 1iep_docked.sdf -ocan
obrms examples/regression/1iep/crystal_ligand.sdf 1iep_docked.sdf | tee 1iep_cpu_redocking_rmsd.txt
```

GPU 同样比较。把按步骤 05 恢复的 1IEP GPU 多 docking pose（对接位姿） SDF 保存为 `1iep_gpu_docked.sdf`，然后执行下列命令。记录排名第一的 docking pose（对接位姿）与前若干 docking pose（对接位姿）的排名、RMSD 与关键接触，便于区分采样到参考姿态与评分将其排在首位。

若最佳匹配 docking pose（对接位姿）已采样到但排位偏低，分别记录该 docking pose（对接位姿）的排名和重对接 RMSD，并复核口袋接触与配体状态。[重对接排错](TROUBLESHOOTING.zh-CN.md#docking-errors)

**环境：** `docking-gromacs`。**预期文件或核查依据：** 终端输出或下方命令指定的文件。耗时和磁盘规划见快速入门的分阶段表。

```bash
obabel 1iep_gpu_docked.sdf -ocan
obrms examples/regression/1iep/crystal_ligand.sdf 1iep_gpu_docked.sdf | tee 1iep_gpu_redocking_rmsd.txt
```

[返回目录](../README.zh-CN.md#contents)
