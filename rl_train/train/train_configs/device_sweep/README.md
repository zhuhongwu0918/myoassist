# 设备扫描（Device sweep）—— 模仿训练，每个双侧外骨骼设备一份配置

共 8 份配置，每份对应一个双侧动力设备。它们之间只有 `device_key` 和外骨骼子策略观测的关节不同，
因此任何结果差异都可归因于设备本身。

## 训练

```bash
python rl_train/run_train.py \
  --config_file_path rl_train/train/train_configs/device_sweep/imitation_22_Tutorial_L1_h128_e32_sidenet_mirror0p1_actpen10.json \
  --config.total_timesteps 30000000 \
  --config.env_params.num_envs 32
```

## 评估

```bash
python -m rl_train.run_policy_eval rl_train/results/<train_session_...> --no-show --steps 1000 --regen
python tools/score_exo_policy.py     rl_train/results/<train_session_...>/analyze_results_00
python tools/plot_kinematics_exo.py  rl_train/results/<train_session_...>/analyze_results_00 -o out.png
```

使用 `--steps 1000`（约 30 个步态周期）。默认的 200 步约为 5 个周期，对于「外骨骼在一个周期内
何时达到峰值」这类分阶段指标来说太短。

## 重新生成配置

这些配置是生成出来的，不是手写的：

```bash
python tools/make_device_sweep_configs.py --exo-shared-side-net --mirror-coef 0.1 \
  --human-net 128 --exo-net 32 --muscle-activation-penalty 10
```

`--out-dir` 可指定输出到其他目录。`python tools/make_device_sweep_configs.py --help` 列出了其他选项。

## 八个设备

| 设备 | 传动方式 | 辅助关节 | 外骨骼观测（qpos / qvel） |
|---|---|---|---|
| `Tutorial_L1` | 关节直驱 | 踝 | `[0,2]` / `[8,10]` |
| `DephyExoBoot_L1` | 关节直驱 | 踝 | `[0,2]` / `[8,10]` |
| `Humotech_L1` | 关节直驱 | 踝 | `[0,2]` / `[8,10]` |
| `OpenExo_L1` | 关节直驱 | 踝 | `[0,2]` / `[8,10]` |
| `STRIDE_L2` | 肌腱 + 连杆 | 踝 | `[0,2]` / `[8,10]` |
| `UTAnkleExo_L2` | 肌腱 + 连杆 | 踝 | `[0,2]` / `[8,10]` |
| `Hippo_L1` | 关节直驱 | **髋** | `[2,4]` / `[10,12]` |
| `HMEDI_L1` | 肌腱 | **髋** | `[2,4]` / `[10,12]` |

`python -m assist_sim list` 为 `myolegs22` 提供 13 种设备。其余五种属于不同的类别：
`Anatomics_L1` 和 `KFoot_L1` 没有任何设备执行器；`NEUankle_L1`、`OpenSourceLeg_A_L1` 和
`OpenSourceLeg_KA_L1` 是肌肉集被截断的单侧假肢，因此它们需要自己的动作布局，无法使用镜像惩罚
或逐侧共享网络。

## 配置说明

* **权值共享的逐侧外骨骼网络**（`exo_actor_r` / `exo_actor_l`）—— 同一个网络分别应用到每条腿，
  该腿自身输入排在前面，因此 `Exo_L(s) = Exo_R(mirror(s))` 在结构上天然成立。
  出自 Abdolhosseini 等 2019，*On Learning Symmetric Locomotion* 的 `NET` 分支。
* **`mirror_coef 0.1`** —— Yu 等 2018 年提出的策略镜像惩罚（`rl_train/train/mirror_ppo.py`）。
* **`muscle_activation_penalty 10`**，取平方，且设备无代价。

用 `tools/score_exo_policy.py` 而不是 `mirror_loss` 来排序候选策略：策略可以通过把两个外骨骼输出
都压向 0 来降低镜像损失。
