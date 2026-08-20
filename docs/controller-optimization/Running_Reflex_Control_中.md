# 运行反射控制（Running Reflex Control）

本指南介绍如何使用仿真脚本运行反射控制。

## 快速开始

### 1. 基础脚本

使用 `run_ctrl_minimal.py` 快速验证仿真是否正常工作：

```bash
cd ctrl_optim
python run_ctrl_minimal.py
```

该脚本创建随机反射参数并运行 5 秒仿真，报告行走时长。

### 2. 完整仿真脚本

`run_ctrl.py` 是运行反射控制的完整脚本。它的用法如下：

```bash
cd ctrl_optim
python run_ctrl.py --mode <sim_mode> [options]
```

### 3. 优化后参数

在 `results/preoptimized/` 目录中查找预优化参数。你也可以在优化运行后，从 `results/optim_results/` 目录中获取参数（带有 `*_BestLast.txt` 后缀的文件）。

要使用预优化的反射参数运行：

```bash
python run_ctrl.py --mode exo --param_path results/preoptimized/myolegs22_ReflexUni_MyoExo_KFoot_Marquardt.txt
```

这将运行一个 30 秒的仿真，使用预优化的反射参数，同时开启外骨骼（-ExoOn）和假肢踝关节（-KFootOn）。

## 仿真模式

使用 `--mode` 标志在 `run_ctrl.py` 中指定仿真类型：

- **`sim`**：标准仿真模式，提供姿势和生物力学数据
- **`exo`**：外骨骼仿真模式，包括外骨骼关节角速度等外骨骼特定信息
- **`gait`**：步态分析模式，专门用于步态分析（步长、步幅等）
- **`video`**：用于生成仿真的 3D 可视化视频，功能与 `sim` 相同，但包含视频生成

## 关键参数

`run_ctrl.py` 支持以下关键参数：

- **`--sim_time`**：仿真时长（秒）。例如：`--sim_time 10`（默认值见配置文件）
- **`--mode`**：仿真模式（`sim`、`exo`、`gait`、`video`）
- **`--param_path`**：控制参数的路径（来自优化或预优化文件）
- **`--ExoOn`**：外骨骼开关（`--ExoOn 1` 开启，`--ExoOn 0` 关闭）
- **`--KFootOn`**：假肢 K-Foot 开关
- **`--save_output`**：保存仿真输出（`1`/`0`）
- **`--viz`**：启用 MuJoCo 可视化（`1`/`0`）

## 输出

运行仿真后，输出将保存在 `results/evaluation_outputs/` 目录中。输出包括仿真视频、姿势数据和生物力学测量值。

## 视频生成

要在仿真中生成视频，请在运行仿真时添加 `--mode video`：

```bash
python run_ctrl.py --mode video --sim_time 10
```

脚本将生成仿真视频，并保存到 `results/evaluation_outputs/` 目录中。
