# 外骨骼控制器（Exoskeleton Controllers）

本文档详细介绍 MyoAssist 反射框架中提供的外骨骼控制器的架构、实现与优化。

## 概述

每个外骨骼的力矩分布由两个基于样条的控制器的其中一个控制，该控制器在步态周期的支撑相（stance phase）内起作用。这些控制器的参数由 CMA-ES 算法与神经肌肉反射参数一起被优化（**[运行优化](Running_Optimizations_zh.md)**）。

## 1. 执行器定义

**设备**（environment spec 中的 device）提供外骨骼。它是一个 assist_sim 设备，例如 `Tutorial_L1`。框架将其与人体 MSK 和地形一起组合进 MuJoCo 模型（参见 **[定义环境](../getting-started/defining-an-environment_zh.md)**）。设备提供外骨骼执行器。你无需手工编辑捆绑的 `.xml` 文件。

关于假肢与截肢设备，以及截肢者反射模式，请参阅 **[截肢与假肢控制](Amputee_Prosthetic_Control_zh.md)**。

每个外骨骼都是该组合 MuJoCo 模型中的一个执行器。MuJoCo 中有多种可用的执行器类型（**[仿真环境](https://myoassist.neumove.org/modeling/)**）。正是这个执行器让框架能够向模型施加力矩。

执行器看起来是这样的：
```xml
<general biasprm="0 0 0" gainprm="100 0 0" dynprm="1 0 0" biastype="none" gaintype="fixed" dyntype="none" joint="ankle_angle_r" name="Exo_R" gear="1.0" ctrlrange="-1 0" ctrllimited="true"/>
<general biasprm="0 0 0" gainprm="100 0 0" dynprm="1 0 0" biastype="none" gaintype="fixed" dyntype="none" joint="ankle_angle_l" name="Exo_L" gear="1.0" ctrlrange="-1 0" ctrllimited="true"/>
```
两个关键属性是：
-   **`joint`**：指定执行器作用的关节（例如 `ankle_angle_r`）。
-   **`name`**：为执行器提供唯一标识符（例如 `Exo_R`）。

`reflex_interface.py` 脚本使用执行器的名称来识别它，并将计算出的力矩应用到仿真控制向量（`env.sim.data.ctrl`）中的正确条目。

## 2. 控制器架构

两个提供的控制器共享一个共同架构：
- **有限状态机（FSM）**：一个简单的 FSM 根据垂直地面反作用力（vGRF）阈值判断腿处于「支撑」（STANCE）还是「摆动」（SWING）状态。
- **支撑相跟踪**：当腿处于「支撑」状态时，控制器跟踪经过的时间。
- **力矩样条**：力矩分布由 PCHIP（分段三次 Hermite 插值多项式）样条定义。样条的输入是当前支撑相百分比（0-100%），输出是要施加的力矩。
- **支撑时长平均**：为了归一化支撑相百分比，控制器维护最近三次支撑时长的运行平均值。

### 控制器 A：4 参数样条（`fourparam_spline_ctrl.py`）

这是一个广泛使用的控制器的变体，由描述单个力矩脉冲形状的四个参数定义。

- **参数**：
    1.  `peak_torque`：力矩脉冲的幅值（归一化 0-1，然后乘以 `max_torque` 缩放）。
    2.  `rise_time`：上升到峰值力矩所需的时间（占支撑相的 %）。
    3.  `peak_time`：峰值力矩在支撑相中出现的位置（占支撑相的 %）。
    4.  `fall_time`：峰值过后下降到零力矩所需的时间（占支撑相的 %）。

- **固定控制器（`--fixed_exo`）**：该命令行选项将 4 参数控制器固定在预定义的初始参数集，而不是优化它们。这适用于评估已知的静态辅助分布。它只适用于 4 参数控制器。对 n 点样条没有任何作用。

<p align="center">
  <img src="https://myoassist.neumove.org/assets/4param.png" alt="4 参数控制器示意图" width="350"/>
  <br>
  <i>4 参数基于相位的样条控制</i>
</p>

### 控制器 B：N 点样条（`npoint_spline_ctrl.py`）

这是一个更灵活的控制器，使用可变数量的控制点定义力矩分布。

- **参数**：控制器由 `2 * n` 个参数定义，其中 `n` 是点数（`--n_points`）。
    - `n` 个力矩参数：每个控制点的力矩值（归一化 0-1）。
    - `n` 个时间参数：每个控制点的时间位置（归一化 0-1）。

<p align="center">
  <img src="https://myoassist.neumove.org/assets/npoint.png" alt="NPoint 控制器示意图" width="350"/>
  <br>
  <i>n 参数样条控制</i>
</p>

## 3. 集成与优化

### 参数边界与初始化
- **边界（`bounds.py`）**：所有外骨骼参数（力矩和时间）的优化边界都被归一化到 `[0, 1]` 范围。这为 CMA-ES 优化器提供了统一且表现良好的搜索空间。
- **初始参数（`train.py`）**：当开始*新的*优化时（即不是从 `--param_path` 开始），初始外骨骼参数设置为预定义默认值：
    - **4 参数控制器**：初始形状基于先前研究中的人机在环实验（Poggesnsee & Collins 2021），为优化提供了良好的起点。
        - `peak_torque`：0.5
        - `rise_time`：0.467
        - `peak_time`：0.90
        - `fall_time`：0.075
    - **N 点控制器**：初始化使用两种关键策略：
        - **力矩值**（`optim/optim_utils/npoint_torque.py`）：初始值遵循几何衰减模式，峰值力矩（0.5 x peak_torque）放置在中间点或稍后位置。周围点根据与峰值的距离按 2 的幂次递减（例如 4 个点：`[0.125, 0.25, 0.5, 0.25]`）。
        - **时间值**：使用分段归一化方法：将支撑相分成 `n` 个等分段（例如 `n=4` 时为 `[0-25%], [25-50%], [50-75%], [75-100%]`），每个时间参数在其段内归一化到 `[0, 1]`。这种分段或「分箱」方法可防止参数聚集和 CMA-ES 不稳定。

### 仿真接口
- **接口（`reflex_interface.py`）**：`myoLeg_reflex` 类是核心集成器。它根据命令行参数实例化选定的外骨骼控制器（`FourParamSplineController` 或 `NPointSplineController`）。
- **力矩应用**：在仿真的每一步中，接口调用控制器的 `.update()` 方法获取当前力矩值，并将其应用到正确的踝关节执行器。
- **样条有效性检查**：接口包含安全检查 `check_spline_validity()`。它在代价评估之前运行。对于 n 点控制器，它检查每个力矩值是否在 `[0.01, 1]` 范围内，每个时间值是否在 `[0, 1]` 范围内；分箱和排序保证时间保持有序。对于 4 参数控制器，它检查峰值、上升和下降边界。如果检查失败，仿真将获得高惩罚代价。这使优化器远离不稳定区域。

## 4. 持续优化与引导初始化（Bootstrapping）

框架为继续或改进先前的优化提供了两个选项，并为 n 点控制器增加了一些额外逻辑。这通过 `train.py` 中的 `--param_path` 参数处理（**[运行优化](Running_Optimizations_zh.md)**）。

### 标准持续优化
如果你将 `--param_path` 指向一个使用了与你新优化*相同*数量的外骨骼参数的优化结果，框架会直接加载参数并从该点继续优化。对于 `4param 控制器` 这*总是*成立，而对于 `npoint 控制器` 只有在传入相同 npoints 值时*才*成立。同样的逻辑适用于：为新优化加载仅含人体参数的结果，而新优化带有外骨骼；框架会用默认值初始化指定数量的外骨骼参数并追加到末尾。

### N 点引导逻辑
框架中一个更复杂的选项是用于持续 `npoint` 优化的**引导初始化（bootstrapping）**能力。它*仅*在你使用 `--param_path` 加载一个与你新优化指定的 `--n_points` 值*不同*的 n 点数的结果时触发。这允许你例如先用 3 点控制器找到一个好的通用力矩形状，然后用更高 n 点的控制器进行细化，而无需从头开始。

- **过程**：
    1. 脚本加载人体参数和旧的 `n-point` 外骨骼参数。
    2. 从加载的参数重建旧的 PCHIP 样条。
    3. 找到旧样条的绝对峰值。
    4. 生成一组新的 `n` 个时间参数，相应间隔分布。
    5. 在这些新的时间点上评估旧样条，获得对应的初始力矩值。
    6. **关键地**，它用旧峰值的*精确*时间和力矩值替换最接近旧峰值的新时间/力矩点。这确保了曲线（可以说）最重要的特征得以保留。
    7. 新的「引导」后的 `2 * n` 个外骨骼参数与人体参数结合，优化开始。

<p align="center">
  <img src="https://myoassist.neumove.org/assets/bootstrap.png" alt="引导示意图" width="600"/>
  <br>
  <i>n 参数样条引导初始化逻辑</i>
</p>

这种引导方法提供了一种干净的方式，在增加或减少外骨骼控制器复杂度的同时，转移先前优化运行的知识。
