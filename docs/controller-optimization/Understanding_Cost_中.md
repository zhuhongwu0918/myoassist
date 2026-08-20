# 理解代价函数（Understanding Cost Functions）

优化的目标函数就是它的「代价」（cost）。优化器试图最小化它。本框架使用一个多阶段的代价。各阶段引导 CMA-ES 优化器从随机参数走向一个能够以稳定且真实的方式行走的控制器。

## CMA-ES 简介

**协方差矩阵自适应进化策略（Covariance Matrix Adaptation Evolution Strategy, CMA-ES）**是一种随机优化算法，非常适用于梯度不可用的复杂非线性问题。其核心思想是：CMA-ES 从一个多元正态分布中迭代地采样一组「种群」（population）的候选解（在我们的场景中，即控制器参数集）。

<div style="text-align: center; display: flex; justify-content: center; gap: 20px;">
  <div style="flex: 1; max-width: 800px;">
    <img src="https://myoassist.neumove.org/assets/cmaes.png" alt="CMA-ES 概览" style="width: 100%; height: 400px; object-fit: contain;">
    <br>
    <i>CMA-ES 代价景观示例</i>
  </div>
</div>

每一代它执行三个关键步骤：
1.  **采样（Sampling）**：从一个由均值（当前最佳猜测）、步长（sigma）和协方差矩阵（分布的形状和方向）定义的高斯分布中生成新的解种群。
2.  **评估（Evaluation）**：通过运行仿真并观察其表现来计算每个解的「适应度」（fitness）或「代价」（cost）。
3.  **更新（Update）**：根据解的排名更新分布的参数（均值、步长和协方差）。均值向表现更好的解偏移，协方差矩阵被调整为与成功步进的方向更好对齐。

这一过程使 CMA-ES 能够高效地探索搜索空间并收敛到最优解。我们的代价函数结构至关重要，因为它创建了一个 CMA-ES 能够有效导航的「景观」。

## 分阶段代价评估

具有随机参数的控制器极不可能产生稳定的行走步态。大多数初始值和手工调整都会导致模型迟早摔倒。因此，我们提供一种反馈梯度，告诉优化器一个解*失败得有多严重*。

为实现这一目标，我们的框架使用三阶段代价评估系统。返回的代价被设计为在每个阶段相差数量级，为优化器创造一条清晰的路径。

### 仿真错误（代价 ≈ 1.2E6）

这是对未能完成的仿真的惩罚。以下错误会触发提前终止：
- 无效的物理状态（例如 `NaN` 值）。
- 未检测到地面反作用力（例如模型未正确接触地面，或传感器放置错误）。
- 无效的初始姿态（例如模型与地面相交）。

例如 `walk_cost.py`：
```python
        Myo_env.reset(params)
        pose_valid = Myo_env.check_pose_validity()
        
        if not pose_valid:
            return 120 * 10000
```

注意：该代价值的调试打印可在 `reflex_interface.py` 中找到。

如果在优化开始时触发了这些错误之一，它不太可能改变。CMA-ES 通常会因为停滞而终止。然而，这些代价值在整个优化过程中的种群内部是可能出现的。只要 1.2E6 不是某次迭代的最佳总体代价，CMA-ES 就不会终止。

### 阶段 1：提前终止（代价 ≈ 9.8E4）

≈ 9.8E4 的代价表示环境初始化成功，并且是在不带初始参数运行优化时，标准初始 CMA 输出代价值（如果一切正常）。然而，模型仍然在摔倒。这种代价结构奖励能够保持直立更久的控制器，即使它们没有完成整个仿真。

```python
def calculate_early_cost(cost_const: float, data_store: List[Dict], left_stance_foot: List[int], right_stance_foot: List[int], failure_mode: int = 99) -> float:
    """Calculate cost for early termination cases."""
    total_cost = (
        failure_mode * cost_const - 
        (data_store[len(data_store)-1]['obj_func_out']['pelvis_dist'][0]) - 
        (0.5 * (len(left_stance_foot) + len(right_stance_foot)))
    )
    return total_cost
```

### 阶段 2：约束违反（代价 ≈ 1.0E4）

仿真可能完整运行但仍然没有产生理想的行走步态。如果控制器未能满足额外的约束，此阶段会分配一个中等档次的惩罚。

主要约束是：
- **最小步数（Minimum Strides）**：模型必须完成最小数量的成功步数（例如 5 步）。
- **对称性（Symmetry）**：左右脚落地的时间必须在一个阈值内保持对称。
- **速度（Velocity）**：平均速度必须接近目标速度。
- **骨盆方向（Pelvis Orientation）**：骨盆必须保持合理直立（针对 3D 模型）。

这些阈值和目标值通过配置文件以及 `train.py`（**[运行优化](Running_Optimizations_zh.md)**）设置。

如果这些约束未满足，代价按如下方式计算：

**示例约束惩罚：**
- 速度惩罚：<code>100 × velocity_cost × (velocity_cost > 0.01)</code>
- 对称性惩罚：<code>100 × sym_cost × (sym_cost > tgt_sym)</code>

### 阶段 3：最终性能代价（代价 < 1.0E3）

如果控制器产生了通过所有约束的有效行走，则会用最终性能代价进行评估。该最终代价是多个指标的加权和，由所选的优化类型决定（例如 `-eff`、`-kine`、`-vel`）。不同的最终代价函数会产生不同的结果。

该代价在低得多的量级（通常在数百范围内，但随代价函数而异），向优化器发出信号：它已经找到了搜索空间的「好」区域，现在应专注于微调性能。

## 代价组成详解

最终性能代价由各个组件组合而成，每个组件量化步态的特定方面。

### 功耗代价（运输成本 Cost of Transport）

衡量步态的代谢能量效率。它被计算为评估期内肌肉激活平方和，按模型质量和行进距离归一化。

### 运动学代价（Kinematics Cost）

衡量模型的关节角度与一组参考运动学数据有多接近。控制器每个关节的步态周期被插值到 100 个点，并与参考数据比较。提供的参考数据是单个步态周期的归一化关节角度。

每个步幅的关节角度被插值到 100 个点并与参考比较。绝对误差在检测到的步幅上取平均。躯干项单独计算，并在包含运动学的最终代价中以权重 1 添加。

### 速度代价（Velocity Cost）

衡量平均步幅速度与目标之间的差异。考虑向前和侧向分量（在斜坡上，向前分量在 x-z 平面中计算）。

### 地面反作用力（GRF）代价

惩罚超过上限阈值的 GRF。我们将评估窗口内总垂直 GRF（左+右）的超额部分求和，并按时长归一化。

### 关节限位代价（疼痛代价 Pain Cost）

惩罚控制器依赖关节限位力矩，因为这些代表关节的被动韧带和结构，而非主动肌肉控制。

### EMG 分布代价（EMG Profile Cost）

与运动学代价类似，它衡量模型的肌肉激活模式与来自人类受试者的参考 EMG 数据之间的差异。

### 对称性代价（Symmetry Cost）

在检测到的左/右支撑事件处，使用膝盖和踝关节相对于骨盆的欧几里得差异计算，在请求的步数上取平均。

截肢者的步态本质上是不对称的，因为假肢腿不像健全腿那样运动。对称性代价和阶段 2 的对称性约束仍然适用，因此请结合该背景解读其数值。如果对称性约束对截肢者运行过于严格，请提高 `--tgt_sym_th`。参见[截肢与假肢控制](Amputee_Prosthetic_Control_zh.md)。
