# 训练配置文件说明

本目录存放强化学习（模仿学习）训练的全部配置。训练入口是 `rl_train/run_train.py`，通过
`--config_file_path` 指定本目录下的某个 JSON 配置运行：

```bash
python rl_train/run_train.py --config_file_path rl_train/train/train_configs/full_training.json
python rl_train/run_train.py --config_file_path rl_train/train/train_configs/full_training.json --flag_rendering
```

---

## 1. 目录内容速览

| 类型          | 文件                                                       | 用途                                                   |
| ------------- | ---------------------------------------------------------- | ------------------------------------------------------ |
| Python 配置类 | `config.py`                                              | 基类`TrainSessionConfigBase`，定义所有字段           |
| Python 配置类 | `config_imitation.py`                                    | 模仿学习配置类`ImitationTrainSessionConfig`          |
| Python 配置类 | `config_imiatation_exo.py`                               | 外骨骼模仿学习配置类`ExoImitationTrainSessionConfig` |
| 实验配置      | `test.json`                                              | 冒烟测试：验证代码能跑通 + 看渲染                      |
| 实验配置      | `test_single_env.json`                                   | 短程正式训练测试（GPU 版冒烟）                         |
| 实验配置      | `full_training.json`                                     | 正式训练基线                                           |
| 实验配置      | `imitation_tutorial_22_separated_net_partial_obs.json`   | 模仿学习默认配置（外骨骼只看踝关节，部分观测）         |
| 实验配置      | `imitation_tutorial_22_separated_net_full_obs.json`      | 同上，但外骨骼使用全部观测                             |
| 实验配置      | `imitation_tutorial_22_separated_net_exo_off.json`       | 对照实验：关闭外骨骼辅助，只看纯肌肉                   |
| 实验配置      | `imitation_tutorial_22_separated_net_speed_control.json` | 实验：让策略学会适应变速行走                           |
| 生成配置      | `device_sweep/`                                          | 8 个外骨骼设备的批量对比配置（由脚本生成）             |

### 三个 Python 配置类

JSON 文件只写字段值，运行时由 `EnvironmentHandler.get_config_type_from_session_id`
根据 `env_params.env_id` 决定套用哪个类：

| env_id                          | 配置类                             | 说明                                               |
| ------------------------------- | ---------------------------------- | -------------------------------------------------- |
| `myoAssistLeg-v0`             | `TrainSessionConfigBase`         | 纯肌肉控制，无模仿学习                             |
| `myoAssistLegImitation-v0`    | `ImitationTrainSessionConfig`    | 肌肉 + 模仿参考步态                                |
| `myoAssistLegImitationExo-v0` | `ExoImitationTrainSessionConfig` | 肌肉 + 外骨骼 + 模仿步态（本目录所有 JSON 都用它） |

### 配置类与 JSON 的配合方式

**一句话：`.py` 配置类定义「有哪些字段、默认值是什么、嵌套结构长什么样」；JSON 只负责「覆盖其中一部分值」；命令行 `--config.xxx.yyy` 再在最后覆盖一次。三者分工明确，没有 JSON 也能跑（全部走默认值），没有配置类则 JSON 无处安放。**

谁在调用 `.py` 配置类——两个函数都在 `rl_train/envs/environment_handler.py`：

```python
# ① 按 env_id 选配置类（environment_handler.py:223-237）
def get_config_type_from_session_id(session_id):
    if session_id == "myoAssistLeg-v0":
        return TrainSessionConfigBase          # 基类
    elif session_id in ["myoAssistLegImitation-v0"]:
        return ImitationTrainSessionConfig     # 加模仿奖励/参考数据字段
    elif session_id == "myoAssistLegImitationExo-v0":
        return ExoImitationTrainSessionConfig  # 再加 human/exo 索引字段
    raise ValueError(f"Invalid session id: {session_id}")

# ② 读 JSON 字典，递归填充进配置类实例（environment_handler.py:239-246）
def get_session_config_from_path(config_path, class_type):
    config_dict = json.load(open(config_path, "r", encoding="utf-8"))
    return DictionableDataclass.create(class_type, config_dict)  # 按字段名逐层填入
```

`DictionableDataclass`（`rl_train/utils/data_types.py`）是这套机制的核心：`create(cls, json_dict)`
按字段名把 JSON 键递归塞进（嵌套的）dataclass 实例；`add_arguments` 把所有字段注册成
`--config.env_params.env_id` 这种形式的 argparse 参数；`set_from_args` 把命令行里出现的
覆盖值写回实例。因此 JSON 里某个键没写，用的就是配置类里的默认值。

**完整调用链**（`rl_train/run_train.py` 第 127-136 行）：

```python
# ① 先用基类预加载 JSON，唯一目的是拿到 env_id（基类字段最少、能覆盖所有 JSON）
default_config = EnvironmentHandler.get_session_config_from_path(
    args.config_file_path, myoassist_config.TrainSessionConfigBase
)
# ② 把基类全部字段注册为 --config.xxx.yyy 命令行参数，并重新解析
DictionableDataclass.add_arguments(default_config, parser, prefix="config.")
args = parser.parse_args()

# ③ 用拿到的 env_id 选出「真实」配置类（本目录 JSON 都是 ExoImitationTrainSessionConfig）
config_type = EnvironmentHandler.get_config_type_from_session_id(default_config.env_params.env_id)
# ④ 用真实配置类重新加载 JSON，字段更全（含模仿奖励、外骨骼索引等）
config = EnvironmentHandler.get_session_config_from_path(args.config_file_path, config_type)

# ⑤ 最后用命令行覆盖值（--config.xxx.yyy）盖掉 JSON 里的值，优先级最高
DictionableDataclass.set_from_args(config, args, prefix="config.")
```

即：**CLI 给 JSON 路径 → 基类预解析拿 env_id → 选真实配置类 → 重载 JSON → 命令行覆盖**。
三步「先预载、再换类、再覆盖」是必须的，因为 env_id 只能从 JSON 内容里读出来，
而它又决定了用哪个类去完整解析同一份 JSON。

优先级（高 → 低）：**命令行 `--config.xxx.yyy` > JSON 文件值 > 配置类默认值**。
想改某个参数临时验证时，无需动 JSON：

```bash
python rl_train/run_train.py --config_file_path rl_train/train/train_configs/full_training.json \
  --config.ppo_params.total_timesteps 10000 --config.env_params.num_envs 4
```

---

## 2. 什么时候用哪个配置（速查）

| 目标                                                     | 用哪个文件                                                 |
| -------------------------------------------------------- | ---------------------------------------------------------- |
| 改完代码想确认能跑通、能出渲染画面                       | `test.json`                                              |
| 想用 GPU 快速看训练曲线是否正常上升                      | `test_single_env.json`                                   |
| 正式训练（标准基线）                                     | `full_training.json`                                     |
| 正式模仿学习训练，外骨骼只观察踝关节（默认、最快的配置） | `imitation_tutorial_22_separated_net_partial_obs.json`   |
| 研究外骨骼观测信息是否越全越好                           | `imitation_tutorial_22_separated_net_full_obs.json`      |
| 对照实验：外骨骼完全不辅助时纯肌肉能走多远               | `imitation_tutorial_22_separated_net_exo_off.json`       |
| 研究策略能否跟随变化的行走速度                           | `imitation_tutorial_22_separated_net_speed_control.json` |
| 对比不同外骨骼设备（踝 vs 髋）对步态的影响               | `device_sweep/imitation_22_<设备名>_....json`            |

---

## 3. 各配置的主要不同点

所有 JSON 共享同一套基础：`env_id=myoAssistLegImitationExo-v0`、`msk_key=myolegs22`（22 块
肌肉）、`device_key=Tutorial_L1`（默认踝关节外骨骼）、参考步态
`rl_train/reference_data/short_reference_gait.npz`。差异体现在下面几处。

### 3.1 训练规模与设备

| 配置                     | total_timesteps | num_envs | device   | n_steps/batch | 备注                                     |
| ------------------------ | --------------- | -------- | -------- | ------------- | ---------------------------------------- |
| `test.json`            | 1000            | 1        | cpu      | 256 / 256     | 每 1 步就评估、记录；开渲染              |
| `test_single_env.json` | 1e6             | 16       | cuda     | 512 / 8192    | 名字带 "single" 是历史遗留，实际 16 envs |
| `full_training.json`   | 5e6             | 16       | cuda     | 1024 / 8192   | 标准正式训练规模                         |
| `imitation_*`（4 个）  | 3e7 ~ 1e8       | 16~32    | cpu/cuda | 512 / 8192    | 长时间训练                               |
| `device_sweep/*`       | 3e7             | 32       | cpu      | 512 / 8192    | 批量扫描                                 |

### 3.2 四个 `imitation_tutorial_22_separated_net_*` 的差异（同一个基线的四个变体）

它们共用网络结构 `human_actor [64,64]` + `common_critic [64,64]`，外骨骼子网络 `exo_actor`
不同，是四组对照实验：

| 配置              | exo_actor 网络 | 外骨骼观测                             | 模仿奖励权重                                                                         | 关键字段                                                                  |
| ----------------- | -------------- | -------------------------------------- | ------------------------------------------------------------------------------------ | ------------------------------------------------------------------------- |
| `partial_obs`   | [8,8]          | 仅踝角度[0,2] + 踝角速度[8,10]（4 维） | 标准                                                                                 | 默认对照                                                                  |
| `full_obs`      | [64,64]        | 全部 44 维观测                         | 标准                                                                                 | 外骨骼信息量更大                                                          |
| `exo_off`       | [8,8]          | 同 partial                             | 更平均（各 0.2~0.4，`forward_reward=0.2`，`joint_constraint_force_penalty=0.0`） | **外骨骼动作被覆盖为常数 1.0**（`"type":"constant"`），即关闭辅助 |
| `speed_control` | 同上结构       | 同 partial                             | **模仿奖励全 0**（qpos/qvel 全 0），`forward_reward=0.5`                     | 速度 0.5~2.7 正弦变化；`out_of_trajectory_threshold=100`（几乎不截断）  |

要点：

- `partial_obs` 和 `full_obs` 对比的是**外骨骼观测范围**对训练的影响。
- `exo_off` 的机制是让外骨骼动作**输出常数**，等于把外骨骼"卸载"掉，用来回答
  "外骨骼到底贡献了多少"。
- `speed_control` 不模仿参考步态（模仿权重全 0），只给 `forward_reward`，让策略学会
  在目标速度不断变化（SINUSOIDAL，0.5~2.7 m/s）时自己调整步态。

### 3.3 `device_sweep/` —— 外骨骼设备批量对比

#### 逻辑关系：一份模板 → 8 份副本（派生关系）

`device_sweep/` 下的 8 个 JSON **全部是从目录外的
`imitation_tutorial_22_separated_net_partial_obs.json` 复制出来再改设备的**——它是唯一母本
（模板），8 份是它的派生副本。这是「一份模板 → 8 份变体」的**派生/复制关系**：不是包含关系
（JSON 不嵌套），也不是重叠关系（每份都是独立完整的文件）。

```
imitation_tutorial_22_separated_net_partial_obs.json   ← 唯一母本（模板）
        │   tools/make_device_sweep_configs.py 复制 + 按设备改写
        ▼
device_sweep/
  imitation_22_DephyExoBoot_L1_h128_e32_sidenet_mirror0p1_actpen10.json
  imitation_22_Hippo_L1_h128_e32_sidenet_mirror0p1_actpen10.json
  ... 共 8 份
```

设计上，8 份之间**只差设备**：`device_key` 不同，外加外骨骼子策略读取的关节观测切片按设备
重排；其余（`env_id`、动作空间、奖励骨架、超参等）与模板完全一致。因此训练结果的差异可以
干净地归因于设备——这正是 sweep 可解释性的前提。

与目录外其他配置（`full_obs`、`exo_off`、`speed_control`、`test`、`full_training` 等）是
**并列关系**：共享同一套字段结构，内容完全独立、互不包含；只有 `partial_obs` 一份与 `sweep`
存在母子关系。注意：**修改模板不会自动同步到 8 份副本**，需重新运行生成器。

（已部署的 8 份在生成时还用 CLI 参数叠加了网络/奖励变体——网络宽度、共享侧网络、镜像惩罚、
激活惩罚，见下文文件名表；这些变体参数对 8 份一致，因此设备间对比依然公平。）

文件名即参数：

```
imitation_22_{设备名}_h128_e32_sidenet_mirror0p1_actpen10.json
```

| 文件名片段    | 含义                                                          |
| ------------- | ------------------------------------------------------------- |
| `h128`      | human_actor 网络宽度改为 [128,128]（模板是 64）               |
| `e32`       | exo_actor 宽度 [32,32]                                        |
| `sidenet`   | 外骨骼左右腿共享一个网络（`exo_actor_r` / `exo_actor_l`） |
| `mirror0p1` | `mirror_coef=0.1`，启用 MirrorPPO 左右镜像对称惩罚          |
| `actpen10`  | `muscle_activation_penalty=10`（肌肉激活惩罚大幅提高）      |

设备清单与辅助关节：

| 设备                                                                                                    | 辅助关节 |
| ------------------------------------------------------------------------------------------------------- | -------- |
| `DephyExoBoot_L1`、`Humotech_L1`、`OpenExo_L1`、`Tutorial_L1`、`STRIDE_L2`、`UTAnkleExo_L2` | 踝关节   |
| `Hippo_L1`、`HMEDI_L1`                                                                              | 髋关节   |

想生成自己的变体（换设备、改网络宽度、调镜像惩罚等）：

```bash
python tools/make_device_sweep_configs.py --help
```

#### 直接可运行的指令示例

**① 跑单个已部署的配置**（8 选 1，直接训练）：

```bash
python rl_train/run_train.py \
  --config_file_path rl_train/train/train_configs/device_sweep/imitation_22_DephyExoBoot_L1_h128_e32_sidenet_mirror0p1_actpen10.json
```

**② 批量跑完 8 个设备**（逐个顺序训练，结果都在各自 session 目录）：

```bash
for cfg in rl_train/train/train_configs/device_sweep/imitation_22_*.json; do
  echo "=== $cfg ==="
  python rl_train/run_train.py --config_file_path "$cfg"
done
```

**③ 重新生成 8 个设备的配置**（默认参数，等价于已部署的那批）：

```bash
python tools/make_device_sweep_configs.py
```

**④ 只扫髋关节设备**（对比髋 vs 踝时常用）：

```bash
python tools/make_device_sweep_configs.py --devices Hippo_L1 HMEDI_L1
```

**⑤ 换网络宽度 + 关镜像惩罚**（看网络容量/对称惩罚的影响）：

```bash
python tools/make_device_sweep_configs.py --human-net 256 --exo-net 64 --mirror-coef 0
```

**⑥ 调奖励权重**（文件名自动带上 `_actpen10` `_exopen0p1` 后缀）：

```bash
python tools/make_device_sweep_configs.py --muscle-activation-penalty 10 --exo-activation-penalty 0.1
```

**⑦ 生成到临时目录做一次性实验**（推荐，避免覆盖已部署的配置）：

```bash
python tools/make_device_sweep_configs.py --out-dir /tmp/sweep_variants \
  --devices DephyExoBoot_L1 --mirror-coef 0.2
```

生成后去对应目录找 `imitation_22_{设备名}{后缀}.json`，再按 **①** 的方式运行即可。

> **覆盖警告**：③④⑤⑥ 默认写到 `device_sweep/`，会**覆盖同名文件**。若机器上是 cpu 版配置
> （`num_envs=32`），做临时实验请用 ⑦ 的 `--out-dir` 指到别处，别把已部署的基线盖掉。

---

## 4. 常用字段速查（改配置时看哪里）

| 字段（`env_params.` 下）                        | 作用                                                                                                                           |
| ------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| `env_id`                                        | 环境类型，决定套用哪个配置类                                                                                                   |
| `device_key`                                    | 外骨骼设备型号                                                                                                                 |
| `msk_key`                                       | 肌肉模型（`myolegs22` = 22 肌肉）                                                                                            |
| `num_envs`                                      | 并行环境数（SubprocVecEnv）                                                                                                    |
| `safe_height` / `out_of_trajectory_threshold` | 摔倒/偏离轨迹判定的阈值；调大可放宽约束                                                                                        |
| `reward_keys_and_weights`                       | 奖励权重：`qpos/qvel_imitation_rewards`（模仿步态）、`forward_reward`（前进）、`muscle_activation_penalty`（肌肉代价）等 |
| `min/max_target_velocity`                       | 目标速度范围；两者相等 = 匀速，不等 = 变速                                                                                     |
| `custom_max_episode_steps`                      | 每个回合最大步数（环境自管理截断）                                                                                             |

| 字段（`ppo_params.` 下）                                      | 作用                                                          |
| --------------------------------------------------------------- | ------------------------------------------------------------- |
| `total_timesteps`                                             | 训练总步数                                                    |
| `device`                                                      | cpu / cuda                                                    |
| `learning_rate` / `n_steps` / `batch_size` / `n_epochs` | PPO 超参数                                                    |
| `mirror_coef`                                                 | >0 时走`MirrorPPO`（左右镜像对称惩罚），0 或缺失 = 普通 PPO |

| 字段（`policy_params.custom_policy_params.` 下） | 作用                                                                                                         |
| -------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| `net_arch`                                       | 三个子网络的宽度：`human_actor`（肌肉）、`exo_actor`（外骨骼）、`common_critic`                        |
| `net_indexing_info`                              | 每个子网络读取观测/输出动作的索引切片（`range` = 连续段，`index` = 自定义顺序，`constant` = 固定输出） |

---

## 5. 建议流程

1. 代码改动后先跑 `test.json`（1 千步 + 渲染，几秒完成）确认无报错。
2. 再用 `test_single_env.json` 在 GPU 上跑 1e6 步，看 loss/奖励曲线是否正常上升。
3. 进入正式实验：`full_training.json` 或 `imitation_tutorial_22_separated_net_partial_obs.json`。
4. 需要对照/研究时，在 4 个 `imitation_*` 变体或 `device_sweep/` 中选择对应配置。
