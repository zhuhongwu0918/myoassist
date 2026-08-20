# MyoAssist

## 快速指令参考

### 环境准备（每次新终端）

```bash
cd /home/gdp/github/myoassist
source .venv/bin/activate
```

---

### 强化学习（RL）训练

基于 PPO 算法，训练 Dephy 外骨骼辅助行走策略。

```bash
# 启动 Dephy 外骨骼强化学习训练
cd /home/gdp/github/myoassist
bash run_dephy_train.sh

# 启动 TensorBoard 监控训练曲线（训练时另开一个终端运行）
/home/gdp/anaconda3/envs/myoassist/bin/tensorboard \
  --logdir /home/gdp/github/myoassist/rl_train/results \
  --port 6006
# 然后浏览器打开 http://localhost:6006

# 关闭后台运行的 TensorBoard
pkill -f tensorboard
```

---

### 反射控制器（Reflex Control）复现

基于 Song & Geyer 2015 脊髓反射回路模型，使用 CMA-ES 优化参数。
官方已提供预优化参数（`tutorial_example`），可直接复现，无需重新训练。
与 RL 训练完全独立，**可同时运行**。

#### 方案一：无头模式（推荐，无需界面，服务器可用）

跑 5 秒仿真，自动生成 MP4 视频，不弹任何窗口：

```bash
PYTHONPATH=/home/gdp/github/myoassist \
  /home/gdp/anaconda3/envs/myoassist/bin/python -c "
import os, sys, runpy
os.chdir('/home/gdp/github/myoassist/ctrl_optim')
sys.path.insert(0, '/home/gdp/github/myoassist')
runpy.run_path('run_ctrl.py', run_name='__main__')
"
```

视频输出路径：`ctrl_optim/results/evaluation_outputs/run_ctrl_<时间戳>/simulation_regular.mp4`

#### 方案二：带 GUI 界面

弹出图形化选择窗口，可交互配置参数文件和仿真设置：

```bash
cd /home/gdp/github/myoassist/ctrl_optim/results/evaluation
PYTHONPATH=/home/gdp/github/myoassist:/home/gdp/github/myoassist/ctrl_optim \
  /home/gdp/anaconda3/envs/myoassist/bin/python eval.py
```

界面操作步骤：

1. **点击 "Add Folder(s)"**，导航到并选中：

   ```text
   /home/gdp/github/myoassist/ctrl_optim/results/optim_results/tutorial_example
   ```

   程序会自动读取 `tutorial_0811_1439.bat`，自动填充环境配置（Model=tutorial, ExoOn=勾选, Max Torque=100, use_4param_spline=勾选）
2. **在 "Select Parameter Files" 区域**勾选 `BestLast`
3. **确认设置**：Evaluation Mode 选 `Short (5s)`，Output Directory 保持默认
4. **点击 "Evaluate"** 开始仿真，结果保存至 `ctrl_optim/results/evaluation_outputs/`

> 如果 Add Folder(s) 后环境配置未自动填充，需手动设置：Model=`tutorial`，Mode=`2D`，ExoOn=勾选，Max Torque=`100`，use_4param_spline=勾选

---




**用于在神经力学仿真中模拟与优化辅助设备的开源 Python 工具包**

MyoAssist 是 [**MyoSuite**](https://sites.google.com/view/myosuite) 中的一个包。MyoSuite 是构建于 [**MuJoCo**](https://mujoco.org/) 之上、面向强化学习与控制研究的一组肌肉骨骼环境集合，由美国东北大学的 [**NeuMove Lab**](https://neumove.org/) 开发和维护。我们致力于融合神经科学、生物力学、机器人学与机器学习，以推进辅助设备的设计，并加深对人类运动的理解。

MyoAssist 由三大组件构成，共同支撑人机交互的仿真、训练与分析：

## 1. 仿真环境（Simulation Environments）

将肌肉骨骼模型与辅助设备相结合的正向仿真。

- **当前可用**：下肢外骨骼与机器人假肢腿
- **规划新增**：上半身可穿戴设备（假肢手臂、背部矫形器）、非穿戴式辅助设备（轮椅、外部驱动支撑装置）
- 包含常见辅助场景的基线控制器

## 2. 训练框架（Training Frameworks）

用于在仿真中生成控制策略或优化行为的工具。

- **强化学习（Reinforcement Learning, RL）**（`rl_train/`）
  - 基于 [Stable-Baselines3](https://stable-baselines3.readthedocs.io/en/master/) 与 [PyTorch](https://pytorch.org/) 构建
  - 支持标准 RL、模仿学习与迁移学习
  - 模块化多智能体网络，可分别控制人体与外骨骼
- **控制器优化（Controller Optimization, CO）**（`ctrl_optim/`）
  - 基于反射的控制模型
  - 使用 CMA-ES 进行参数调优

## 3. 运动数据库（Motion Library，规划中）

一个精选的人类运动数据集，涵盖真实与仿真数据。

## 组合式架构（Composed Architecture）

自 1.0 版本起，MyoAssist 不再内置模型 XML。环境在构建时由三个兄弟包**组合**而成，并通过一个精简的 `{msk, device, terrain}` 规格来描述：

| 组件                             | 来源包                                                                    | 示例                                                                                                    |
| ------------------------------------- | ------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| 人体肌肉骨骼模型（`msk`） | [`myo_sim`](https://github.com/MyoHub/myo_sim)                           | `myolegs22`（22 块肌肉的 2D 模型）、`myolegs26`（26 块肌肉的 3D 模型）、`myolegs`、`myofullbody` |
| 辅助设备（`device`）         | [`assist_sim`](https://github.com/neumovelab/assist_sim)                 | `DephyExoBoot_L1`、`HMEDI_L1`、`Humotech_L1`、`OpenSourceLeg_KA_L1`、`NEUankle_L1` 等（共 13 种） |
| 地形（`terrain`）                 | [`myoassist.terrains`](https://github.com/neumovelab/myoassist.terrains) | `flat`、`slope`、`rough`、`sinusoidal` 及组合赛道 |

`myoassist_utils/compose.py` 将人体 MSK、设备与地形组装为单个 MuJoCo 模型，而
`myoassist_utils/env_spec.py`（`EnvSpec`）是 RL 与 CO 两条流程共用的经过验证的统一入口。
如需列出所有有效的 `msk`/`device` 组合，可运行：

```bash
python -m assist_sim list
```

更多内容请参阅 [`docs/getting-started/defining-an-environment.md`](docs/getting-started/defining-an-environment.md)
以及 [`docs/examples/`](docs/examples/) 中开箱即用的规格示例。

## 安装（Installation）

### 环境要求（Prerequisites）

- Python 3.11+
- Git
- [uv](https://docs.astral.sh/uv/)（安装工具；第 3 步将说明原因）
- MuJoCo ≥ 3.4（作为依赖自动安装）

### 安装步骤（Setup）

1. **克隆本仓库：**

   ```bash
   git clone https://github.com/neumovelab/myoassist.git
   cd myoassist
   ```
2. **创建虚拟环境（推荐）：**

   ```bash
   # Linux/macOS
   python3.11 -m venv .my_venv
   source .my_venv/bin/activate

   # Windows
   py -3.11 -m venv .my_venv
   .my_venv\Scripts\activate
   ```
3. **安装 uv，然后安装本包：**

   ```bash
   pip install uv
   uv pip install -e .
   ```

   MyoAssist 使用 `uv` 而非普通的 `pip` 安装。MyoSuite 2.8.4 在其元数据中固定了较旧版本的 MuJoCo，
   但本框架需要 MuJoCo 3.4 以支持兄弟包（`myo-sim`、`assist-sim`、`myoassist-terrains`）。
   `pyproject.toml` 中的 `[tool.uv]` 覆盖配置放宽了该版本限制，因此 `uv` 可以用一条命令解析整个依赖栈。
   普通的 `pip` 无法做到这一点，会因依赖解析错误而中止。进行多仓库开发的贡献者可以克隆三个兄弟包，
   并分别运行 `uv pip install -e`，以便本地修改能够被及时应用。
4. **验证安装：**

   ```bash
   python test_setup.py
   ```

## 快速上手（Quick Start）

- **定义环境**：[定义环境](docs/getting-started/defining-an-environment.md)
- **强化学习**：
  ```bash
  python rl_train/run_train.py --config_file_path rl_train/train/train_configs/<config>.json
  ```

  参见 [RL 指南](docs/reinforcement-learning/index.md)。
- **控制器优化**：
  ```bash
  # 运行 ctrl_optim/optim/training_configs/ 中预定义的优化配置
  python ctrl_optim/run_optim.py tutorial

  # 或使用自定义环境直接调用优化器
  python -m ctrl_optim.optim.train --msk myolegs22 --device DephyExoBoot_L1
  ```

  参见 [控制器优化指南](docs/controller-optimization/index.md)。

完整文档存放于仓库内 [`docs/`](docs/) 目录下；含图表与教程的完整版请访问官网：
[https://myoassist.neumove.org](https://myoassist.neumove.org)。

## 项目结构（Project Structure）

```
myoassist/
├── ctrl_optim/          # 反射控制器优化（CMA-ES）
│   ├── run_optim.py     #   优化入口
│   ├── run_ctrl.py      #   运行 / 回放控制器
│   ├── run_eval.py      #   核心步态评估流程
│   ├── ctrl/            #   反射 + 外骨骼控制器
│   ├── optim/           #   优化器、代价函数、配置
│   └── eval/            #   步态评估器 + 评估配置
├── rl_train/            # 强化学习
│   ├── run_train.py     #   训练入口
│   ├── envs/            #   组合式 RL 环境
│   ├── train/           #   策略、训练配置、命令
│   └── analyzer/        #   步态 / 训练日志分析
├── myoassist_utils/     # 共享的组合式 + 环境规格流程
│   ├── compose.py       #   MSK + 设备 + 地形 -> MuJoCo 模型
│   └── env_spec.py      #   EnvSpec：经过验证的 {msk, device, terrain}
├── docs/                # 仓库内轻量文档 + 示例
├── setup.py             # 包配置
├── pyproject.toml       # 构建后端 + uv 依赖覆盖
├── requirements.txt     # 依赖（PyPI 兄弟包）
└── test_setup.py        # 安装验证
```

## 文档（Documentation）

仓库内文档（轻量、可全文搜索的文本）：

- [快速入门](docs/getting-started/index.md) — 安装与[定义环境](docs/getting-started/defining-an-environment.md)
- [强化学习](docs/reinforcement-learning/index.md) — 配置、地形类型、网络处理器、代码结构
- [控制器优化](docs/controller-optimization/index.md) — 运行优化、反射控制、代价函数、结果评估
- [环境示例](docs/examples/) — 开箱即用的 `{msk, device, terrain}` 规格

含图表与教程的完整站点：[https://myoassist.neumove.org](https://myoassist.neumove.org)。

## 贡献（Contributing）

我们欢迎各种形式的贡献！

- 如果您希望将公司或实验室的设备纳入 MyoAssist，请联系我们。
- 有关 RL 的问题，请联系 Hyoungseo Son：son.hyo@northeastern.edu
- 有关反射或建模的问题，请联系 Calder Robbins：robbins.cal@northeastern.edu

## 许可证（License）

本项目采用 Apache License 2.0 许可 — 详情请参阅 [LICENSE](LICENSE)。

## 相关项目（Related Projects）

- [**MyoSuite**](https://sites.google.com/view/myosuite) — 基础肌肉骨骼仿真框架
- [**MuJoCo**](https://mujoco.org/) — 物理仿真引擎
- [**myo_sim**](https://github.com/MyoHub/myo_sim) · [**assist_sim**](https://github.com/neumovelab/assist_sim) · [**myoassist.terrains**](https://github.com/neumovelab/myoassist.terrains) — 组合式架构的兄弟包

---

如有问题或需要支持，请在项目仓库中提交 issue。
