# 网络索引处理器（Network Index Handler）

网络索引处理器可在多 actor 强化学习系统中，为不同网络实现**选择性观测输入**和**定向动作输出映射**。该系统允许特定网络只接收完整观测中与其相关的部分，并将其输出映射到动作空间中的特定索引。

## 概述（Overview）

在以下场景中，网络索引（Network Indexing）至关重要：

- **选择性观测输入**：网络只需要完整观测中的特定部分
- **定向动作映射**：网络的输出应映射到特定的动作索引
- **多 actor 协调**：不同的 actor 控制动作空间的不同部分

<p align="center">
  <img src="https://myoassist.neumove.org/assets/multiple_actor_observation.png" alt="多 actor 结构" width="70%">
</p>

> **注意：**
观测向量的顺序可以在 gym 环境的 `DEFAULT_OBS_KEYS` 中查看（[rl_train/envs/](https://github.com/neumovelab/myoassist/tree/main/rl_train/envs/)）。
其中，`qpos`（关节位置）、`qvel`（关节速度）以及关节/传感器键的顺序可以在配置文件（例如 `observation_joint_pos_keys`、`observation_joint_vel_keys`、`observation_joint_sensor_keys`）中找到。
每个观测分量会被拼接起来，因此你可以确定每个元素在完整观测向量中的索引。
激活数（activations）与肌肉数量对应。

## 核心概念（Core Concepts）

### 观测索引（Observation Indexing）

**目的**：为单个网络提取特定的观测范围

**使用场景**：
- 不同网络需要不同的观测分量
- 减少专用网络的输入复杂度
- 在网络之间高效共享观测数据

**示例**：
```json
{
  "type": "range", 
  "range": [0, 8], 
  "comment": "为此网络提取关节位置数据"
}
```

### 动作映射（Action Mapping）

**目的**：将网络输出映射到特定的动作空间索引

**使用场景**：
- 网络只控制特定的动作分量
- 多个网络对动作空间的不同部分做出贡献
- 协调人体与外骨骼的动作

**示例**：
```json
{
  "type": "range_mapping",
  "range_net": [0, 11], 
  "range_action": [0, 11], 
  "comment": "将网络输出映射到右腿肌肉动作"
}
```

## 多 Actor 架构（Multi-Actor Architecture）

### 人体 Actor 网络

**目的**：控制人体肌肉激活

**观测**：
- 接收全面的状态信息
- 处理完整观测以进行协调的肌肉控制

**动作**：
- 输出肌肉激活命令
- 映射到动作空间中的肌肉动作索引

### 外骨骼 Actor 网络

**目的**：控制外骨骼辅助

**观测**：
- 只接收必要的信息（例如踝关节数据）
- 使用最小观测进行专注控制

**动作**：
- 输出外骨骼辅助命令
- 映射到动作空间中的外骨骼动作索引

### 每侧外骨骼网络（Per-Side Exo Networks）

用 `exo_actor_r` 和 `exo_actor_l` 代替 `exo_actor` 声明，会构建**一个**网络，并将其应用于每条腿（以该腿自身的输入优先），因此 `Exo_L(s) == Exo_R(mirror(s))` 在构造上成立。两个名称都指向同一个模块，因此优化器只看到一份权重。

配置必须满足以下约束，其中每一项都会被断言（assert）：

- 同时声明两个名称，或都不声明。
- 不要与它们一起声明 `exo_actor`，否则外骨骼动作槽位会被写入两次。
- 两侧必须读取相同的观测索引集。这里的检查会比较排序后的索引集是否相等。镜像顺序（因此 `Exo_L(s) == Exo_R(mirror(s))`）由配置生成器安排，而非此检查。这就是 `index` 类型存在的原因：`range` 无法重新排序。
- 两侧必须输出相同数量的命令，并且如果两者都出现在 `net_arch` 中，则宽度必须相等。

所有八个 `device_sweep/` 配置都使用此形式。

### 共享 Critic 网络

**目的**：评估整体系统性能

**观测**：
- 接收完整的状态信息
- 评估完整的系统状态

**动作**：
- 无动作输出（仅 critic）
- 专注于状态评估

## 配置结构（Configuration Structure）

网络索引配置遵循以下结构：

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

### Actor 网络

Actor 网络需要同时进行观测索引和动作索引，因为它们将观测映射到动作。每个 actor 网络都基于自身的观测子集输出动作。

**示例 Actor 配置**：
```json
"human_actor": {
  "observation": [
    {
      "type": "range",
      "range": [0, 8],
      "comment": "关节位置数据"
    },
    {
      "type": "range", 
      "range": [8, 17],
      "comment": "关节速度数据"
    }
  ],
  "action": [
    {
      "type": "range_mapping",
      "range_net": [0, 11],
      "range_action": [0, 11],
      "comment": "右腿肌肉"
    },
    {
      "type": "range_mapping",
      "range_net": [11, 22],
      "range_action": [11, 22],
      "comment": "左腿肌肉"
    }
  ]
}
```

### Critic 网络

Critic 网络只预测一个值（价值函数），不输出动作。因此，它们只需要观测索引来指定它们评估状态的哪些部分。

**示例 Critic 配置**：
```json
"common_critic": {
  "observation": [
    {
      "type": "range",
      "range": [0, 44],
      "comment": "完整状态评估"
    }
  ]
}
```

## 索引类型（Indexing Types）

### 范围索引（Range Indexing）

**类型**：`"range"`

**目的**：从完整状态中提取特定的观测范围

**使用场景**：
- 为不同网络提供不同的观测分量
- 减少专用网络的输入复杂度
- 网络之间高效的数据共享

**参数**：
- `range`：`[起始（含）, 结束（不含）]` - 要提取的半开区间索引
- `comment`：所提取数据的描述

**示例**：
```json
{
  "type": "range",
  "range": [0, 2],
  "comment": "踝关节角度数据"
}
```

### 范围映射（Range Mapping）

**类型**：`"range_mapping"`

**目的**：将网络输出范围映射到特定的动作空间索引

**使用场景**：
- 在动作空间中协调多个网络
- 确保每个网络控制特定的动作分量
- 防止不同 actor 之间的冲突

**参数**：
- `range_net`：`[起始（含）, 结束（不含）]` - 网络输出范围
- `range_action`：`[起始（含）, 结束（不含）]` - 要映射到的动作空间范围
- `comment`：动作映射的描述

**示例**：
```json
{
  "type": "range_mapping",
  "range_net": [0, 2],
  "range_action": [22, 24],
  "comment": "外骨骼左、右执行器"
}
```

### 索引（Index）

**类型**：`"index"`

**目的**：按列出的顺序读取列出的观测索引

**使用场景**：
- 向网络提供非连续（non-contiguous）的观测分量
- 重新排序输入，`range` 无法做到这一点，因为它按现有顺序取连续的块

**参数**：
- `index`：观测索引，按给定顺序读取
- `comment`：所提取数据的描述

**示例**（`device_sweep/imitation_22_Hippo_L1_h128_e32_sidenet_mirror0p1_actpen10.json`）：
```json
{
  "type": "index",
  "index": [3, 2, 11, 10, 39, 40, 41, 42],
  "comment": "髋屈曲角度、角速度和足部接触，先右腿后对侧腿"
}
```

### 索引映射（Index Mapping）

**类型**：`"index_mapping"`

**目的**：将网络输出写入列出的索引所对应的动作索引

**参数**：
- `index`：索引，同时用于网络输出和动作槽位
- `comment`：动作映射的描述

一个列表同时索引两侧，因此网络输出必须至少与最大索引一样宽。当网络输出范围与动作范围不同时，请使用 `range_mapping`。

### 常量（Constant）

**类型**：`"constant"`

**目的**：将动作范围固定为某个值

不消耗任何网络输出，因此 `constant` 条目不会增加该网络的动作尺寸。

**参数**：
- `range_action`：`[起始（含）, 结束（不含）]` - 要固定的动作范围
- `default_value`：写入该范围每个槽位的值
- `comment`：描述

**示例**（`imitation_tutorial_22_separated_net_exo_off.json`，将外骨骼保持在恒定命令）：
```json
{
  "type": "constant",
  "range_action": [22, 24],
  "default_value": 1.0,
  "comment": "覆盖外骨骼"
}
```

该配置保留了同一范围的 `range_mapping` 条目。动作条目按顺序应用，因此 `constant` 最后写入并覆盖它。

## 示例（Example）

下面是一个完整的外骨骼 actor 索引示例：

**配置文件**：`imitation_tutorial_22_separated_net_partial_obs.json`
<p align="center">
  <img src="https://myoassist.neumove.org/assets/exo_network_indexing_example.png" alt="外骨骼网络索引示例" width="90%">
</p>

```json
"exo_actor": {
  "observation": [
    {
      "type": "range",
      "range": [0, 2],
      "comment": "8 个 qpos 中不含 lumbar_extension 的 2 个踝关节角度"
    },
    {
      "type": "range",
      "range": [8, 10],
      "comment": "9 个 qvel 中不含 lumbar_extension 的 2 个踝关节角速度"
    }
  ],
  "action": [
    {
      "type": "range_mapping",
      "range_net": [0, 2],
      "range_action": [22, 24],
      "comment": "外骨骼左、右的 2 个执行器"
    }
  ]
}
```
