# 强化学习（Reinforcement Learning）

MyoAssist 的强化学习（RL）流程使用 **[Stable-Baselines3 (SB3) PPO](https://stable-baselines3.readthedocs.io/en/master/index.html)** 和自定义的 **[MuJoCo](https://mujoco.org/)** 环境。这些环境模拟人机交互。本页概述各部分如何组合在一起，以及在哪里可以找到更多信息。

<p align="center">
  <img src="https://myoassist.neumove.org/assets/rl_framework.png" alt="MyoAssist 强化学习框架" style="width: 34rem; max-width: 100%; height: auto;">
</p>

强化学习（RL）是一种机器学习方法。智能体学习做出决策。它与环境交互并接收奖励作为反馈。在 MyoAssist 中，RL 在 MuJoCo 仿真环境中训练人机系统的控制策略。

**观测空间（Observation Space）：**
在我们的环境中，智能体接收的观测包括：
- 关节角度
- 关节速度
- 肌肉激活
- 传感器数据（如地面接触、力传感器等）
- 目标速度（最后一个观测分量）

**动作空间（Action Space）：**
智能体输出控制以下内容的动作：
- 肌肉激活（用于人体 actor 网络）
- 外骨骼控制值（用于外骨骼 actor 网络）

## 训练工作流

1. **定义配置**：从现有的 JSON 预设开始，或从头创建。
2. **启动训练**
   ```bash
   python rl_train/run_train.py --config_file_path rl_train/train/train_configs/my_config.json
   ```
3. **监控进度**：日志和结果输出到 `rl_train/results/train_session_*`。
4. **评估策略**：
   ```bash
   python rl_train/run_policy_eval.py rl_train/results/train_session_<timestamp>
   ```
5. **分析结果**：参见[评估](https://myoassist.neumove.org/evaluation/)以了解共享的评估输出。

---

## 关键特性

- **多 Actor 支持**：为人体肌肉和外骨骼执行器提供独立的网络（参见[网络索引处理器](04_network-index-handler_zh.md)）。
- **可变地形**：在平地、斜坡、粗糙或平铺地形上训练，由[地形](https://myoassist.neumove.org/modeling/terrains/)定义。
- **参考运动模仿**：使用地面真实步态轨迹的可选模仿奖励。
- **实时评估**：使用 `--flag_realtime_evaluate` 实时运行策略。

<div style="display: flex; justify-content: center; align-items: center; gap: 24px;">
  <div style="flex: 1; text-align: center;">
    <img src="https://myoassist.neumove.org/assets/partial_flat_short.gif" alt="平地回放" style="max-width: 100%; height: auto;">
  </div>
  <div style="flex: 1; text-align: center;">
    <img src="https://myoassist.neumove.org/assets/rough_short.gif" alt="粗糙地形回放" style="max-width: 100%; height: auto;">
  </div>
  <div style="flex: 1; text-align: center;">
    <img src="https://myoassist.neumove.org/assets/speed_control_shortest.gif" alt="速度控制回放" style="max-width: 100%; height: auto;">
  </div>
</div>

---

# 快速入门（Getting Started）

本指南向你展示在 MyoAssist RL 系统中测试 RL 系统和运行训练的最快方式。

## RL 训练入口点

以下是 [`rl_train`](https://github.com/neumovelab/myoassist/tree/main/rl_train/) 文件夹中主要入口点脚本的快速概览：

| 文件 | 用途 |
|------|---------|
| [`run_sim_minimal.py`](https://github.com/neumovelab/myoassist/blob/main/rl_train/run_sim_minimal.py) | 创建和测试 MyoAssist RL 环境的最简单方法。不进行训练，仅创建环境并执行随机动作。 |
| [`run_train.py`](https://github.com/neumovelab/myoassist/blob/main/rl_train/run_train.py) | 运行 RL 训练会话的主要入口点。加载配置、设置环境并开始训练。 |
| [`run_policy_eval.py`](https://github.com/neumovelab/myoassist/blob/main/rl_train/run_policy_eval.py) | 评估和分析已训练策略的入口点。用于测试策略性能并生成分析结果。 |

## 快速测试命令

### 1. 环境创建示例

查看如何创建仿真环境并运行 150 帧（5 秒）：

```bash
python rl_train/run_sim_minimal.py
```

- mac：
```bash
mjpython rl_train/run_sim_minimal.py
```
> **注意：**
如果你在 macOS 上需要 MuJoCo 可视化器，只需用 `mjpython` 代替 `python` 运行脚本。
你不需要安装任何额外的东西。只需更改命令：

> **注意：**
如果你看到错误消息 `ModuleNotFoundError: No module named 'flatten_dict'`，只需再次运行该命令。这通常会自动解决问题。

<!-- ![run_sim_minimal.py 的结果](https://myoassist.neumove.org/assets/rl_random_action_tutorial_env.png)-->

<p align="center">
  <img src="https://myoassist.neumove.org/assets/rl_random_action_tutorial_env.png" alt="run_sim_minimal.py 的结果" width="50%">
</p>

**作用：**
- 展示创建一个 Gym 包装的 MuJoCo 仿真环境的示例
- 不进行实际训练 - 仅环境创建示例

> 终止（Terminated）与截断（Truncated）[Gymnasium 的 Env.step API 中 terminated 和 truncated 值的深入解释](https://farama.org/Gymnasium-Terminated-Truncated-Step-API)

### 2. 快速训练测试

运行一个最小训练会话以验证一切正常：
```bash
python rl_train/run_train.py --config_file_path rl_train/train/train_configs/test.json --flag_rendering
```
<!-- ```bash
python rl_train/run_train.py --config_file_path rl_train/train/train_configs/imitation_tutorial_22_separated_net_partial_obs.json --config.total_timesteps 12 --config.env_params.num_envs 1 --config.ppo_params.n_steps 4 --config.ppo_params.batch_size 4 --config.logger_params.logging_frequency 1 --config.logger_params.evaluate_frequency 1 --flag_rendering
``` -->

**作用：**
- 运行实际的强化学习训练
- 只训练很少的时间步
- 使用 1 个环境（资源占用最小）
- 启用渲染以查看仿真
- 每次 rollout 后（256 步，`test.json`）记录结果以获得即时反馈

### 3. 查看结果

训练后，查看结果文件夹：

```bash
# 结果位置
rl_train/results/train_session_[date-time]/
```
<p align="center">
  <img src="https://myoassist.neumove.org/assets/train_session_result.png" alt="训练会话结果示例" width="50%">
</p>

并发运行永远不会共享目录。训练会占用 `train_session_[date-time]`，当秒级时间戳已被占用时，会依次使用 `train_session_[date-time]_1`、`_2` 等。

**你会找到的内容：**
- `analyze_results_[timesteps]_[evaluate_number]`：训练期间写入的分析结果，由学习回调每 `logger_params.evaluate_frequency` 次 rollout 运行的分析器生成
- `session_config.json`：本次训练使用的配置
- `train_log.json`：训练日志数据
- `trained_models/`：每个日志间隔保存的已训练模型（`.zip`）- 可用于评估或迁移学习

`run_policy_eval.py` 改为写入 `analyze_results_[NN]`，没有时间步前缀。

## 完整训练（准备就绪后）

首先开启模型缓存。每个 `num_envs` 工作进程都会组合自己的模型，因此不开启缓存时训练会慢得多：

```bash
export MYOASSIST_CACHE_DIR=~/.cache/myoassist
```

该变量同时涵盖 RL 和控制器优化。参见[缓存](https://myoassist.neumove.org/modeling/devices/exporting-and-loading/#caching)。

一旦你验证了一切正常，即可运行完整训练：

```bash
python rl_train/run_train.py --config_file_path rl_train/train/train_configs/imitation_tutorial_22_separated_net_partial_obs.json
```

这是我们提供的默认示例配置文件。
更多详情，请参见[RL 配置](02_configuration_zh.md)部分。

> **注意：**
> 提供的配置将 `num_envs` 设置为 32。
> 根据你 PC 的性能，请尝试将其降低到 4、8 或 16。
> 你也应该相应调整 `n_steps`。
> 例如，如果你使用 `num_envs=16`（32 的一半），你应该将 `n_steps` 加倍以保持总批次大小相同。

## 策略评估

测试已训练的模型：

```bash
python rl_train/run_policy_eval.py [path/to/trainsession/folder]
```

> 将 `run_policy_eval.py` 指向你生成的任何 `train_session_*` 目录。

| 标志 | 含义 |
|------|---------|
| `--steps N` | 覆盖每次 rollout 的 `num_timesteps`。配置默认为 200 步，约 5 个步幅。适用于已训练的会话。 |
| `--regen` | 即使评估步态数据已存在也重新生成。 |
| `--no-show` | 跳过弹出式合成窗口。 |
| `--varying` | 将 `evaluate_param_list` 替换为单个 SINUSOIDAL 0.8-1.4 m/s 的 rollout，并生成速度跟踪合成图。 |
| `--cmap {rainbow,teal,bluered}` | 变速合成图的速度颜色映射。 |
| `--legacy-plots` | 同时写入旧版逐面板 PNG。 |

训练后，你的 `train_session` 目录内会创建一个 `analyze_results` 文件夹。
该文件夹包含可视化智能体性能的各种图表和视频。

- **在哪里找到：**
  ```
  rl_train/results/train_session_[date-time]/analyze_results_[NN]/
  ```
- **里面有什么：**
  - `composite.png`（和 `.svg`）、`replay.mp4` 和 `gait_evaluated_data.json`
  - 参见[评估](https://myoassist.neumove.org/evaluation/)以了解这些输出的完整描述。

用于评估和分析的参数（例如生成哪些图表/视频）由 `session_config.json` 文件中的 `evaluate_param_list` 控制。

有关如何自定义这些参数的更多详情，请参见[RL 配置](02_configuration_zh.md)部分。

## 迁移学习
<img src="https://myoassist.neumove.org/assets/transfer_learning_explanation.png" alt="迁移学习" style="max-width: 100%; height: auto;">

```bash
python rl_train/run_train.py --config_file_path [path/to/transfer_learning/config.json] --config.env_params.prev_trained_policy_path [path/to/pretrained_model]
```

或者你也可以在配置（.json）文件中指定 `env_params.prev_trained_policy_path`。

> **注意：** `[path/to/pretrained_model]` 应指向一个 `.zip` 文件，但路径中不要包含 `.zip` 扩展名。

## 实时策略运行
你可以在实时仿真中运行训练好的策略：
<p align="center">
  <img src="https://myoassist.neumove.org/assets/realtime_eval_flat_tutorial.gif" alt="run_sim_minimal.py 的结果" width="50%">
</p>

- windows：
```bash
python rl_train/run_train.py --config_file_path [path/to/config.json] --config.env_params.prev_trained_policy_path [path/to/model_file] --flag_realtime_evaluate
```

- mac：
```bash
mjpython rl_train/run_train.py --config_file_path [path/to/config.json] --config.env_params.prev_trained_policy_path [path/to/model_file] --flag_realtime_evaluate
```

**参数：**
- `[path/to/config.json]`：train_session 文件夹中 JSON 文件的路径
- `[path/to/model_file]`：模型文件（.zip）的路径，不带扩展名。它位于 train_models 文件夹中
<p align="center">
  <img src="https://myoassist.neumove.org/assets/train_models.png" alt="已训练模型" width="50%">
</p>

> 使用你生成的 `train_session_*` 目录中的 `session_config.json` 和 `model_<steps>` 文件。
