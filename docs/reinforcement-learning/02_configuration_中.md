# RL 配置（Configuration）

本页介绍 `rl_train/train/train_configs/` 中 JSON 配置文件的格式，以及如何在训练时覆盖任何设置。

## 配置文件概览

**配置文件（.json）** 定义了训练会话的**所有**方面，包括环境设置、PPO 超参数、奖励设计和评估参数。它是运行训练的唯一必填参数。

## 如何配置

由于运行了 `run_train.py --config_file_path <path/to/config.json>`，配置文件是主要输入。如果你只提供配置文件路径，所有参数都从该文件读取，你将得到一个（可能）可复现的训练运行。

### 默认配置文件

开箱即用的完整示例配置：

```
rl_train/train/train_configs/imitation_tutorial_22_separated_net_partial_obs.json
```

### 基本示例

```json
{
  "env_params": {
    "prev_trained_policy_path": "",
    "num_envs": 32,
    "flag_rendering": true,
    "msk_key": "myolegs22",
    "device_key": "Tutorial_L1",
    "terrain": null,
    "flag_imitation": true,
    "reference_data_path": "rl_train/reference_data/short_reference_gait.npz",
    "record_video_interval": 2000,
    "record_video_length": 200,
    "randomization": {
      "enabled": false,
      "uniform_interval": [0.5, 1.5]
    }
  },
  "ppo_params": {
    "n_steps": 2048,
    "batch_size": 512,
    "learning_rate": 3e-4,
    "n_epochs": 10,
    "gamma": 0.99,
    "gae_lambda": 0.95,
    "clip_range": 0.2,
    "ent_coef": 0.0,
    "vf_coef": 0.5,
    "max_grad_norm": 0.5,
    "mirror_coef": 0.0
  },
  "reward_params": {
    "velocity_reward_weight": 0.5,
    "ankle_exo_reward_weight": 0.2,
    ...
  },
  "logger_params": {
    "logging_frequency": 20,
    "evaluate_frequency": 20,
    "flag_logging": true,
    "save_video": true
  },
  "train_parameters": {
    "total_timesteps": 2000000
  },
  "net_arch": {
    ...
  },
  "net_indexing_info": {
    ...
  }
}
```

### 配置组

配置文件的顶层字段被分组为**三个组**。每个组处理训练会话的一个特定方面：

| 组 | 键 | 描述 |
|-----|-----|-------------|
| 环境参数 | `env_params` | 环境创建和仿真参数 |
| 学习参数 | `ppo_params` | PPO 学习算法参数 |
| 记录参数 | `logger_params` | 训练期间的记录和评估参数 |

其他顶层字段包括 `train_parameters`、`reward_params`、`net_arch` 和 `net_indexing_info`。

## 环境参数（`env_params`）

环境创建和仿真的参数。这些定义环境的行为方式。

### 基本环境参数

| 参数 | 默认值 | 描述 |
|--------|---------|-------------|
| `num_envs` | 32 | 并行环境数量 |
| `flag_rendering` | false | 在训练中启用仿真渲染（仅用于调试，会显著降低训练速度） |
| `msk_key` | `"myolegs22"` | 人体 MSK 模型的注册表键 |
| `device_key` | `"Tutorial_L1"` | 辅助设备的注册表键 |
| `terrain` | `null` | 地形定义（`null` 为平地，或内联配置/JSON 路径） |

**地形（Terrain）**：请参阅[定义环境](../getting-started/defining-an-environment_zh.md)了解如何指定地形。平地（地面）、斜坡、粗糙、正弦波和平铺赛道是常见选项。

**模型键（Model Keys）**：请参阅[定义环境](../getting-started/defining-an-environment_zh.md)了解有效的 MSK 和设备键。使用 `python -m assist_sim list` 查看已安装的键。

### 仿真参数

| 参数 | 默认值 | 描述 |
|--------|---------|-------------|
| `randomization` | 见右侧 | 每次重置时随机化初始条件。请参阅下文**随机化**部分。 |
| `ctrl_dt` | 自动 | 控制周期（秒）。每个环境的默认值取决于模型（2D/3D）。 |

### 动作/观测大小

观测和动作大小由环境自动决定。要查看环境中可用的观测键，请参阅 [网络索引处理器](04_network-index-handler_zh.md)。

### 模仿（Imitation）

| 参数 | 默认值 | 描述 |
|--------|---------|-------------|
| `flag_imitation` | false | 启用模仿奖励，以跟踪参考步态轨迹 |
| `reference_data_path` | `"rl_train/reference_data/short_reference_gait.npz"` | 包含参考步态轨迹的 NPZ 文件路径（相对仓库根目录） |

### 视频记录

| 参数 | 默认值 | 描述 |
|--------|---------|-------------|
| `record_video_interval` | 2000 | 训练中记录视频的时间步间隔 |
| `record_video_length` | 200 | 每个视频的帧数 |

### 迁移学习

| 参数 | 默认值 | 描述 |
|--------|---------|-------------|
| `prev_trained_policy_path` | `""` | 先前训练模型的路径（不带 `.zip` 扩展名），用于迁移学习 |

### 随机化（Randomization）

`env_params.randomization` 控制每次重置时的初始条件变化。

| 参数 | 默认值 | 描述 |
|--------|---------|-------------|
| `enabled` | `false` | 启用或禁用随机化 |
| `uniform_interval` | `[0.5, 1.5]` | 随机化量的均匀区间。乘以目标速度。 |

**示例：**
```json
"randomization": {
  "enabled": true,
  "uniform_interval": [0.5, 1.5]
}
```

## 学习参数（`ppo_params`）

使用 PPO 学习算法的超参数。

### 核心 PPO 参数

| 参数 | 默认值 | 描述 |
|--------|---------|-------------|
| `n_steps` | 2048 | 每次 PPO 更新的时间步数（通常 × `num_envs`） |
| `batch_size` | 512 | 每个小批次的样本数量 |
| `learning_rate` | 3e-4 | 学习率 |
| `n_epochs` | 10 | 每次更新遍历数据的轮数 |
| `gamma` | 0.99 | 折扣因子 |
| `gae_lambda` | 0.95 | GAE 平滑因子 |
| `clip_range` | 0.2 | PPO 裁剪范围 |
| `ent_coef` | 0.0 | 熵奖励系数 |
| `vf_coef` | 0.5 | 价值函数损失系数 |
| `max_grad_norm` | 0.5 | 梯度裁剪 |
| `mirror_coef` | 0.0 | 镜像对称奖励系数（使用 `MirrorPPO`） |

### 镜像 PPO

**镜像 PPO** 是带有**镜像对称奖励**的 PPO 的变体（`mirror_coef`）。

镜像对称性是一种用于行为克隆的属性。其思想是，对于行走，左右腿之间的对称性是一个非常有用的先验。通过镜像 PPO，我们向奖励添加了一个镜像项，以鼓励策略输出对称行为。

`mirror_coef` 的典型值是 `0.1`。为镜像 PPO 训练的模型可以在**非对称任务**上微调（`mirror_coef=0.0`），例如在特定一侧使用外骨骼进行训练。

## 奖励参数（`reward_params`）

奖励权重和系数。这些定义策略优化的奖励目标。

**示例：**
```json
"reward_params": {
  "velocity_reward_weight": 0.5,
  "ankle_exo_reward_weight": 0.2,
  "penalty": {
    "velocity_penalty": -0.1,
    "exo_penalty": -0.01
  }
}
```

具体奖励项取决于环境实现。请参阅 `rl_train/envs/` 中的 `MyoAssistLegBase` 类以获取完整列表。

## 记录参数（`logger_params`）

训练期间记录和评估的参数。

| 参数 | 默认值 | 描述 |
|--------|---------|-------------|
| `logging_frequency` | 20 | 记录训练日志的 rollout 次数 |
| `evaluate_frequency` | 20 | 运行评估（分析器）的 rollout 次数 |
| `flag_logging` | true | 启用或禁用日志记录 |
| `save_video` | true | 在评估期间保存视频 |

## 训练参数（`train_parameters`）

| 参数 | 默认值 | 描述 |
|--------|---------|-------------|
| `total_timesteps` | 2000000 | 要训练的总时间步数 |

## 网络架构（`net_arch`）

网络架构由 `net_arch` 字典配置。**始终使用自定义策略**。它定义了 actor 网络、critic 网络和常见结构的网络架构。

```json
"net_arch": {
  "human_actor": {...},
  "exo_actor": {...},
  "common_critic": {...}
}
```

具体架构取决于网络数量（`num_networks`）。请参阅[网络索引处理器](04_network-index-handler_zh.md)了解如何为多 actor 系统配置网络。

## 网络索引信息（`net_indexing_info`）

`net_indexing_info` 字典定义了每个网络的观测输入和动作输出索引。

```json
"net_indexing_info": {
  "human_actor": {
    "observation": [...],
    "action": [...]
  },
  "exo_actor": {
    "observation": [...],
    "action": [...]
  },
  "common_critic": {
    "observation": [...]
  }
}
```

请参阅[网络索引处理器](04_network-index-handler_zh.md)了解完整的 `net_indexing_info` 文档。

## 命令行覆盖

**每个**配置参数都可以使用 `--config.<param> <value>` 语法从命令行覆盖：

```bash
python rl_train/run_train.py --config_file_path <path/to/config.json> \
  --config.env_params.num_envs 4 \
  --config.ppo_params.n_steps 2048 \
  --config.train_parameters.total_timesteps 1000000
```

这允许你使用单个配置文件作为基础，并针对特定实验进行调整，而无需编辑文件。

## 其他训练标志

| 标志 | 描述 |
|--------|-------------|
| `--flag_rendering` | 覆盖 `env_params.flag_rendering` 为 true |
| `--flag_realtime_evaluate` | 在训练器中以实时仿真评估策略 |

## 示例配置文件

请参阅 `rl_train/train/train_configs/` 中的示例配置：

- `test.json`：最小测试配置
- `imitation_tutorial_22_separated_net_partial_obs.json`：完整教程配置，带有分离的网络和部分观测
- `imitation_tutorial_22_separated_net_exo_off.json`：外骨骼保持恒定命令（由 `net_indexing_info` 中的 `constant` 条目实现）

每个配置都是一个完整的 JSON 文件，你可以复制并修改。
