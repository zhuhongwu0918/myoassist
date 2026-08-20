# 截肢与假肢控制（Amputee and Prosthetic Control）

本页面展示如何在佩戴假肢设备的截肢模型上优化反射控制器。它涵盖两个特性：截肢者反射模式（`--reflex_mode amp`）和假肢踝关节刚度优化（`--optimize_stiffness`）。

## 截肢模型

截肢模型是一个标准的腿部 MSK 与一个假肢设备组合而成。该设备执行截肢操作。它会移除截肢部位以下的肌肉和骨骼，重塑残肢，并连接假肢。你不需要单独构建截肢 MSK 模型。

框架内置了四种假肢设备：

| 设备 | 类型 | 截肢 |
|--------|------|------------|
| `KFoot_L1` | 被动足 | 胫骨截肢（膝盖以下），右侧 |
| `NEUankle_L1` | 动力踝 | 胫骨截肢（膝盖以下），右侧 |
| `OpenSourceLeg_A_L1` | 动力踝（开源腿） | 胫骨截肢（膝盖以下），右侧 |
| `OpenSourceLeg_KA_L1` | 动力膝和踝（开源腿） | 股骨截肢（膝盖以上），右侧 |

胫骨截肢设备会移除膝盖以下的腿部并连接到残余胫骨。股骨截肢的 `OpenSourceLeg_KA_L1` 会移除髋部以下的腿部并连接到残余股骨。

与其他环境一样组合截肢环境即可。给定一个腿部 MSK 键和一个假肢设备键：

```json
{ "msk": "myolegs22", "device": "KFoot_L1" }
```

运行 `python -m assist_sim list` 可查看有效键。参见[定义环境](../getting-started/defining-an-environment_zh.md)。

## 截肢者反射模式

标准反射控制器用一套肌肉驱动两条腿。截肢模型在假肢一侧的肌肉较少，因此标准控制器无法在其上运行。截肢者反射模式解决了这个问题。

设置 `--reflex_mode amp` 以在截肢模型上运行反射控制器。此模式做两件事：

1. 它使用双侧布局。每条腿拥有自己的反射参数块。布局参见[反射控制](Reflex_Control_Overview_zh.md)。
2. 它容忍假肢一侧。它跳过被截肢移除的肌肉的反射项。它将假肢踝关节读取为其背屈与跖屈关节之和。它还处理缺失的足趾关节和假肢足部放置。

只对截肢设备使用 `amp`。对于完整模型，对独立双腿使用 `bilat`，或使用默认的对称模式。

`amp_kfoot` 示例在被动 K-Foot 上运行 22 肌肉模型：

```bash
cd ctrl_optim
python run_optim.py amp_kfoot
```

## 假肢踝关节刚度优化

被动假肢足具有弹簧踝。`KFoot_L1` 足在一个轴上使用两个弹簧关节。`df_ankle_angle_r` 承载背屈。`pf_ankle_angle_r` 承载跖屈。每个关节都有自己的刚度。

设置 `--optimize_stiffness` 将这两个刚度加入搜索。该标志向 CMA-ES 向量追加两个参数：一个用于跖屈，然后一个用于背屈。优化器与反射控制器一起调优它们。

工作原理：

- 两个参数归一化到 `[0, 1]`。
- 每次重置时，框架将其反归一化，并为两个踝关节写入 `model.jnt_stiffness`。它编辑实时模型，不会重新编译。
- 刚度范围为跖屈 30 至 300 Nm/rad，背屈 100 至 1000 Nm/rad。
- 这两个参数是参数向量的最后两个条目。

只有被动的 `KFoot_L1` 足具有两个弹簧踝关节，因此 `--optimize_stiffness` 适用于它。动力踝（`NEUankle_L1`、`OpenSourceLeg_A_L1`、`OpenSourceLeg_KA_L1`）驱动电机而非弹簧，因此该标志不适用于它们。

`kfoot_stiffness` 示例为截肢者反射增加了刚度优化：

```bash
cd ctrl_optim
python run_optim.py kfoot_stiffness
```

## 注意事项

- 截肢者模式已在 K-Foot 上的 2D 模型验证。3D 系（`myolegs26`）也可以组合并运行。
- 截肢者的步态本质上是不对称的。对称性代价仍然适用，因此请结合该背景解读其数值。参见[代价函数](Understanding_Cost_zh.md)。
- 假肢足在其自身支撑相期间承载负荷。在 `walk_left` 起始姿态下，假肢（右侧）腿在后，因此该瞬间其地面反作用力读数接近零。
