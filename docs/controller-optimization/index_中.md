# 控制器优化（Controller Optimization）

**面向辅助设备的基于反射的控制器，通过参数优化实现**

<div style="text-align: center;">
  <img src="https://myoassist.neumove.org/assets/co_framework.png" alt="MyoAssist 控制器优化框架" style="width: 34rem; max-width: 100%; height: auto;">
</div>

MyoAssist 中的控制器优化用于调优基于反射的肌肉骨骼控制器以及外骨骼控制器。它采用 CMA-ES（协方差矩阵自适应进化策略）为各种性能目标生成控制器。

## 优化工作流

1. **搭建（Setup）**：配置你的肌肉骨骼模型和外骨骼控制器
2. **定义目标（Define Objectives）**：指定环境配置、代价函数和优化准则
3. **优化（Optimize）**：运行 CMA-ES 优化，寻找最优控制器参数
4. **监控进度（Monitor Progress）**：跟踪 CMA-ES 进度并输出代价数值
5. **分析结果（Analyze Results）**：评估结果并可视化性能

## 关键特性

- **反射控制优化**：使用 CMA-ES 优化基于反射的控制器
- **外骨骼控制测试**：为各种辅助设备设计、部署和优化控制器
- **结果分析**：内置处理和可视化优化结果的工具

### 关键脚本

- **`run_ctrl_minimal.py`**：使用随机参数进行简单的反射控制测试
- **`run_ctrl.py`**：完整的仿真，支持视频生成和参数加载
- **`run_optim.py`**：用于控制器调优的 CMA-ES 优化运行器
- **`run_eval.py`**：结果评估与分析

<div style="display: flex; gap: 20px; margin: 20px 0;">
  <div class="info-box" style="flex: 1; margin: 0;">
    <h4>快速入门</h4>
    <p>学习反射控制的基础知识并开始你的第一次优化</p>
    <ul>
      <li><a href="Running_Reflex_Control_zh.md">运行反射控制</a></li>
      <li><a href="Running_Optimizations_zh.md">运行优化</a></li>
      <li><a href="https://myoassist.neumove.org/evaluation/">评估</a></li>
    </ul>
  </div>
  <div class="info-box" style="flex: 1; margin: 0;">
    <h4>更多主题与工具</h4>
    <p>自定义代价函数并分析优化结果</p>
    <ul>
      <li><a href="Exoskeleton_Controllers_zh.md">外骨骼控制器</a></li>
      <li><a href="Amputee_Prosthetic_Control_zh.md">截肢与假肢控制</a></li>
      <li><a href="Understanding_Cost_zh.md">代价函数</a></li>
      <li><a href="Reflex_Control_Overview_zh.md">反射控制</a></li>
    </ul>
  </div>
</div>

<div style="text-align: center; margin: 20px 0;">
  <img src="https://myoassist.neumove.org/assets/exo_vis_r.gif" alt="控制器优化演示" style="max-width: 40%; height: auto;">
</div>

## 快速入门

### 代码库结构

```
ctrl_optim/
├── run_ctrl_minimal.py          # 快速测试脚本
├── run_ctrl.py                  # 主要仿真脚本
├── run_optim.py                 # 优化运行器
├── run_eval.py                  # 评估脚本
├── results/
│   ├── evaluation_outputs/      # 仿真视频与输出
│   ├── optim_results/           # 优化结果
│   └── preoptimized/            # 预优化控制器
├── ctrl/                        # 控制器实现
│   ├── reflex/                  # 反射控制器模块
│   ├── exo/                     # 外骨骼控制器模块
│   └── prosthetic/              # 假肢踝关节控制器
└── optim/                       # 优化框架
    ├── cost_functions/          # 代价函数实现
    ├── config/                  # 参数解析与环境代码
    └── training_configs/        # 训练配置
```

### 基本反射控制

从最简脚本开始运行反射控制：

```bash
cd ctrl_optim
python run_ctrl_minimal.py
```

该脚本：

- 创建 77 个随机控制参数（即 2D 反射参数总数；其他模式见[反射控制](Reflex_Control_Overview_zh.md)）
- 使用默认设置运行 5 秒仿真
- 报告行走时长
