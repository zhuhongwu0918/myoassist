# RL 训练代码结构（RL Training Code Structure）

本页概述 `rl_train` 包内的目录布局以及每个模块的主要职责。当你需要修改、调试或扩展训练流程时，可将其作为快速参考。

---

## 入口点（Entry Points）

| 脚本 | 用途 |
|--------|---------|
| `run_sim_minimal.py` | 快速启动一个环境并执行**随机动作**，用于对仿真进行冒烟测试（smoke-testing）。 |
| `run_train.py` | 主要的**训练启动器**。读取 JSON 配置，构建环境，并启动 Stable-Baselines3 PPO 训练。 |
| `run_policy_eval.py` | 以评估模式回放**已训练的策略**，并生成分析产物。 |

`run_train.py` 和 `run_policy_eval.py` 接受命令行标志，因此大多数超参数可以在不编辑 JSON 配置文件的情况下被覆盖。`run_sim_minimal.py` 不接受任何参数。

---

## 目录布局（Directory Layout）

```text
rl_train/
├── envs/                # Gym / MuJoCo 环境定义
│   ├── myoassist_leg_base.py
│   ├── myoassist_leg_imitation.py
│   ├── myoassist_leg_imitation_exo.py
│   └── environment_handler.py
│
├── train/               # 训练流程（配置、命令、策略）
│   ├── train_configs/   # 完整指定一次训练会话的 JSON 文件
│   ├── train_commands/  # 记录完整训练调用的 Windows .bat 文件
│   └── policies/        # 自定义策略网络
│
├── utils/               # 训练 / 分析中使用的通用工具
│   └── learning_callback.py  # 用于日志记录与检查点的自定义 SB3 回调
│
├── analyzer/            # 训练后分析与可视化
│   ├── gait_analyze.py
│   ├── gait_evaluate.py
│   └── train_analyzer.py
│
├── reference_data/      # 用于模仿或评估的人体动作捕捉数据
│   ├── segmented.npz
│   └── short_reference_gait.npz
│
└── results/             # 自动生成的输出（检查点、日志、视频）
```

### `envs/`
*所有基于 MuJoCo 的 Gym 环境的所在地*

| 文件 | 关键类 | 说明 |
|------|-----------|-------|
| `myoassist_leg_base.py` | `MyoAssistLegBase` | 基类，负责连接内部仿真逻辑、观测构建和奖励项。 |
| `myoassist_leg_imitation.py` | `MyoAssistLegImitation` | 用于**肌肉驱动模仿学习**（仅人体）的环境。 |
| `myoassist_leg_imitation_exo.py` | `MyoAssistLegImitationExo` | 增加**外骨骼驱动**的变体。 |
| `environment_handler.py` | `EnvironmentHandler` | 工厂，根据 JSON 配置实例化并向量化环境。 |

### `train/`
*启动、配置和扩展 PPO 训练*

* **`train_configs/`**：数十个现成的 JSON 预设。文件名通常描述实验内容（`imitation_tutorial_22_separated_net_partial_obs.json`）。
* **`train_commands/`**：记录完整训练调用的 Windows `.bat` 文件，因此长实验可以被逐字复现。
* **`policies/`**：自定义网络架构。始终使用自定义策略。

### `utils/`
*共享辅助工具。内部不包含训练逻辑。*

| 文件 | 作用 |
|------|--------------|
| `learning_callback.py` | 每 `logger_params.logging_frequency` 次 rollout 保存一个检查点并写入 `train_log.json`；每 `logger_params.evaluate_frequency` 次 rollout 在工作进程中运行分析器。 |
| `train_log_handler.py` | 围绕 **loguru** 的小型封装，用于统一各脚本的日志输出。 |
| `numpy_utils.py` | 用于快速数组运算的杂项辅助函数。 |
| `data_types.py` | `DictionableDataclass`：dataclass ↔ dict 转换，以及生成 `--config.*` 命令行覆盖。 |

### `analyzer/`
*事后评估与可视化*

分析流程是模块化的。`TrainAnalyzer` 没有命令行入口：训练回调在工作进程中调用它，写入 `rl_train/results/train_session_*/analyze_results_<timesteps>_<NN>/`。

### `reference_data/`
包含用于模仿或计算生物力学指标的参考步态轨迹（例如 **NPZ** 文件）。`segmented.npz` 通过相对路径加载，因此 `run_policy_eval.py` 必须从仓库根目录运行。

---

## 典型数据流（Typical Data Flow）

1. **`run_train.py`** 加载 JSON 配置 → 构建一个 `EnvironmentHandler`。
2. 处理器创建环境实例（默认外骨骼环境为 **`MyoAssistLegImitationExo`**）。仅当 `num_envs > 1` 且渲染关闭时，它才用 SB3 的 `SubprocVecEnv` 包装它们。否则使用单个普通 gym 环境。
3. 初始化自定义 PPO 策略并开始学习。
4. 每 *k* 步，`LearningCallback` 保存：
   - `trained_models/model_<steps>.zip`
   - `train_log.json`
   - 预览视频（由分析器渲染，受 `logger_params.evaluate_frequency` 控制）
5. 训练后，运行 **`run_policy_eval.py`** 回放检查点；它直接驱动 `TrainLogAnalyzer`、`GaitAnalyzer` 和 `ImitationGaitEvaluator`（而非 `TrainAnalyzer`）。

---

## 扩展流程（Extending the Pipeline）

1. **添加新地形**：将 `env_params.terrain` 设置为地形配置（[地形](https://myoassist.neumove.org/modeling/terrains/)）。使用 JSON 路径或内联配置。参见[定义环境](../getting-started/defining-an-environment_zh.md)。
2. **自定义奖励**：继承 `MyoAssistLegBase` 并覆盖 `get_reward_dict()`、`_calculate_base_reward()` 或 `_calculate_reward_per_step()`。
3. **不同算法**：算法在 `EnvironmentHandler.get_stable_baselines3_model()` 中选择，当 `ppo_params.mirror_coef > 0` 时它已经会切换到 `MirrorPPO`。在那里添加更多 SB3 算法，而不要在 `run_train.py` 中添加，后者不导入任何算法。
4. **新图表**：在 `analyzer/gait_analyze.py` 中添加一个函数，并从 `train_analyzer.py` 调用它。

---
