# MyoAssist 工程架构分析

## 一、项目定位

MyoAssist 是由东北大学 **NeuMove Lab** 开发的开源Python工具包，建立在 MuJoCo 物理引擎之上，用于**仿真和优化辅助设备**（外骨骼、假肢）在神经肌肉骨骼模型中的控制策略。

对应的核心理论论文：
- **Song & Geyer (2015)** — *"A neural circuitry that emphasizes spinal feedback generates diverse behaviours of human locomotion"*, J. Physiology — 这是整个反射控制器的理论基础
- **Poggesnsee & Collins (2021)** — *DOI: 10.1126/scirobotics.abf1078* — 外骨骼4参数样条控制器的初始参数设置依据

---

## 二、整体工程结构

```
myoassist/
├── myosuite/          # 底层：MuJoCo 肌骨仿真环境（来自 MyoSuite 项目）
├── models/            # MuJoCo XML 模型文件（肌骨 + 外骨骼）
├── ctrl_optim/        # 模块一：反射控制器 + CMA-ES 参数优化
├── rl_train/          # 模块二：强化学习训练框架
├── myoassist_utils/   # 共享工具（地形生成等）
└── docs/              # 文档网站（Jekyll）
```

---

## 三、各模块详解

### 3.1 `myosuite/` — 底层仿真引擎

这是 MyoSuite 的子集，提供 MuJoCo 环境的基础封装：

- `envs/env_base.py`：所有环境的基类，封装 MuJoCo `dm_control` 接口
- `physics/`：物理仿真工具
- `renderer/`：可视化渲染
- `utils/`：gym 接口适配

**关键概念**：MyoAssist 的所有环境都继承自这里的 `MujocoEnv`。

---

### 3.2 `models/` — 肌骨 + 外骨骼 XML 模型

| 模型类型 | 文件夹 | 说明 |
|---------|--------|------|
| **22肌肉 2D** | `22muscle_2D/` | 矢状面简化模型，计算最快，用于快速优化 |
| **26肌肉 3D** | `26muscle_3D/` | 完整三维模型，含内收/旋转自由度 |
| **80肌肉 3D** | `80muscle/` | 全身肌肉精细模型（myoLegs），最真实 |
| **网格资产** | `mesh/` | 骨骼/关节/外骨骼的 STL 文件 |

支持外骨骼平台：**Dephy、HMEDI、Humotech、OSL（踝关节/膝踝假肢）**

---

### 3.3 `ctrl_optim/` — 反射控制器优化（核心模块一）

这是理论深度最高的模块，直接对应 Song & Geyer 2015 论文。

#### 3.3.1 `ctrl/reflex/reflex_ctrl.py` — 神经肌肉反射控制器

**理论来源**：Song & Geyer 2015，脊髓反射回路模型

```python
# MyoLocoCtrl 类：对应论文中的10个反射模块（Module 1-10）
cp_keys = [
    'theta_tgt', 'alpha_0', 'alpha_delta', 'C_d', 'C_v',  # 躯干姿态控制参数
    'Tr_St_sup', 'Tr_Sw',                                   # 支撑/摆动相转换阈值
    'knee_tgt', 'knee_sw_tgt', 'knee_off_st', ...          # 关节目标角度
    '1_GLU_FG', '1_VAS_FG', '1_SOL_FG', ...               # Module 1: 支撑相负荷反射
    '2_HAM_FG', '2_VAS_BFSH_PG', ...                       # Module 2: 膝关节屈曲抑制
    '3_HFL_Th', '3_HFL_d_Th', '3_GLU_Th', ...             # Module 3: 躯干角度反射
    '4_HFL_C_GLU_PG', ...                                   # Module 4: 髋关节互抑制
    '5_TA_PG', '5_TA_SOL_FG', ...                          # Module 5: 踝背屈控制
    '6_HFL_RF_PG', ...                                      # Module 6: 摆动相髋屈曲
    '7_BFSH_RF_VG', ...                                     # Module 7: 膝关节制动
    '8_RF_VG', ...                                          # Module 8: 摆动相膝伸展
    '9_HAM_PG', ...                                         # Module 9: 摆动末期制动
    '10_HFL_PG', '10_GLU_PG', '10_VAS_PG',                # Module 10: 速度/位置控制
]
# 2D模型: 51个控制参数; 3D模型: 额外添加内收/旋转模块 → 63个参数
```

**参数命名规则**：
- `X_MUS_FG`：肌肉力反馈增益（Force Gain）
- `X_MUS_PG`：肌肉长度/位置反馈增益（Position Gain）
- `X_MUS_VG`：肌肉速度反馈增益（Velocity Gain）
- `X_MUS_SG`：突触增益（Synaptic Gain）
- `Th` / `d_Th`：触发阈值 / 阈值变化率

#### 3.3.2 `ctrl/reflex/reflex_interface.py` — 反射控制器与仿真环境的接口

```python
# myoLeg_reflex 类负责：
# 1. 将 MuJoCo 仿真状态提取为反射控制器所需的感觉信号
# 2. 调用 MyoLocoCtrl 计算肌肉激活命令
# 3. 将外骨骼控制器（ExoCtrl）输出的扭矩注入到仿真

legDatalist = [
    'load_ipsi',           # 同侧肢体负荷（用于支撑相检测）
    'phi_hip', 'phi_knee', 'phi_ankle',   # 关节角度（感觉输入）
    'dphi_hip', 'dphi_knee', 'alpha',     # 关节角速度
    'F_GLU', 'F_VAS', 'F_SOL', ...       # 肌肉力（Golgi腱器官信号）
]
```

#### 3.3.3 `ctrl/exo/` — 外骨骼控制器

**对应 Poggesnsee & Collins 2021** 的踝关节外骨骼控制策略——基于步态周期百分比的样条扭矩曲线。

```python
# fourparam_spline_ctrl.py — FourParamSplineController
# 4参数控制：peak_torque, rise_time, peak_time, fall_time
# 用 PCHIP 样条插值生成站立相扭矩轮廓
# 初始值取自 Poggesnsee & Collins 2021: rise=0.467, peak=0.90, fall=0.075

# npoint_spline_ctrl.py — NPointSplineController
# N点样条控制：n个扭矩幅值 + n个时间节点（更灵活）
# 每个时间点被归一化到其所在的等分区间内（防止点排序混乱）
# 状态机 FSM: SWING ↔ STANCE（基于垂直地反力阈值 vGRF > 0.1）
# 用滑动窗口（最近3步）动态估计当前站立相持续时间
```

#### 3.3.4 `optim/` — CMA-ES 参数优化主流程

优化流程：
```
参数向量 params → func_Walk_FitCost() → MuJoCo仿真 → evaluateCost() → 代价值
                                              ↑
                                    CMA-ES (协方差矩阵自适应进化策略)
                                    并行评估 (EvalParallel2, 多进程)
```

**参数向量结构（22/26肌肉模型，有外骨骼）**：

| 索引范围 | 内容 |
|---------|------|
| `[0:51]` | 反射控制增益（Module 1-10，2D=51参，3D=63参） |
| `[51:77]` | 初始姿态参数（关节角度 + 骨盆速度） |
| `[77:95]` | 肌肉长度缩放（左右各9块肌肉，共18个） |
| `[95:]` | 外骨骼样条参数（4参或 2N参） |

**代价函数（evaluate_cost.py）**：

| 代价项 | 物理意义 |
|--------|---------|
| 运动学代价 | 与参考步态（ref_kinematics_radians.csv）的关节角误差 |
| 努力代价 | `Σ(肌肉激活²) / (质量 × 行走距离)` — 代谢能耗代理 |
| EMG匹配代价 | 与参考肌电信号（ref_EMG.csv）的差异 |
| 速度代价 | 实际行走速度与目标速度的偏差 |
| 对称性代价 | 左右步态的对称性指标 |
| 关节限位代价 | 关节到达极限时的惩罚扭矩 |
| 早期终止惩罚 | 模型跌倒则返回 `120 × 10000` 大惩罚 |

**Bootstrapping 机制**（N点样条的冷启动）：从已优化的低分辨率样条（如4点）重建PCHIP曲线，在新分辨率（如8点）下重新采样，保留峰值特征，作为更高分辨率优化的初始解。

---

### 3.4 `rl_train/` — 强化学习训练框架（核心模块二）

```
rl_train/
├── envs/
│   ├── myoassist_leg_base.py      # RL基础环境（继承MujocoEnv）
│   └── myoassist_leg_imitation.py # 模仿学习环境（跟踪参考运动）
├── train/
│   ├── policies/                   # 多智能体网络结构
│   │   ├── rl_agent_human.py       # 人体肌肉控制网络
│   │   ├── rl_agent_exo.py         # 外骨骼控制网络
│   │   └── network_index_handler.py# 观测/动作索引分配
│   └── train_configs/              # JSON格式训练配置
├── analyzer/                       # 步态分析工具
└── reference_data/                 # 参考运动数据（步态捕捉）
```

#### 关键设计：双智能体分离网络

```python
# network_index_handler.py
# 核心思想：人体肌肉 和 外骨骼 由独立的神经网络分别控制
# 通过索引映射将完整观测空间分割，各子网络只看自己相关的观测
# 各子网络输出映射回全局动作空间（肌肉激活命令）
# 优势：可以冻结人体网络，单独优化外骨骼网络（迁移学习）
```

#### 模仿学习环境（myoassist_leg_imitation.py）

奖励设计：
- 位置模仿奖励：`dt × exp(-8 × Δq²)` — 指数衰减，偏差越大奖励急剧下降
- 速度模仿奖励：`dt × exp(-8 × Δdq²)`
- 速度缩放：参考数据速度按当前目标速度等比缩放（支持变速行走）
- 超出轨迹阈值时提前终止（`out_of_trajectory_threshold`）

#### 训练配置（JSON驱动）

配置文件（如 `imitation_tutorial_22_separated_net_exo_off.json`）控制：
- 环境参数：地形类型、速度范围、物理帧率（1200Hz）vs 控制帧率（50Hz）
- 奖励权重：前进速度、肌肉激活惩罚、步态对称等
- 网络结构：每个子网络的层数/宽度
- 观测分配：哪些关节角度给人体网络，哪些给外骨骼网络

---

### 3.5 `myoassist_utils/` — 共享工具

```python
# hfield_manager.py — 地形高度场管理器
# 支持：flat（平地）、sinusoidal（正弦地形）、uphill/downhill（坡道）
# 动态修改 MuJoCo 的 heightfield 数据，实现地形变化训练
```

---

## 四、两条技术路线对比

| 对比维度 | 反射控制优化（ctrl_optim） | 强化学习（rl_train） |
|---------|--------------------------|-------------------|
| **理论基础** | 神经科学（脊髓反射回路） | 最优控制（PPO） |
| **参数数量** | ~77-100个手工设计参数 | 神经网络数百万参数 |
| **优化算法** | CMA-ES（进化策略） | PPO（策略梯度） |
| **可解释性** | 高（每个参数有生理意义） | 低（黑盒） |
| **泛化能力** | 较弱（需针对地形重优化） | 强（可适应地形变化） |
| **训练速度** | 慢（需大量仿真rollout） | 可并行加速 |
| **适用场景** | 机制研究、外骨骼设计 | 自适应控制、迁移学习 |

---

## 五、数据流总览

```
MuJoCo XML模型
      ↓ 物理仿真 (1200Hz)
感觉信号提取（关节角/肌肉力/GRF）
      ↓
  [分叉点]
  ┌────────────────┬────────────────────┐
  │  反射控制路线   │    RL控制路线       │
  │ reflex_ctrl.py │ myoassist_leg_*.py  │
  │ 10个反射模块   │ PPO Actor-Critic    │
  │ CMA-ES优化     │ 模仿学习奖励        │
  └────────────────┴────────────────────┘
      ↓                    ↓
  肌肉激活命令 + 外骨骼扭矩
      ↓
  评估代价 / 累积奖励
      ↓
  参数更新（进化/梯度）
```

---

## 六、关键参考文献

1. **Song & Geyer (2015)**. "A neural circuitry that emphasizes spinal feedback generates diverse behaviours of human locomotion." *The Journal of Physiology*. — 反射控制器（`reflex_ctrl.py`）的理论来源
2. **Poggesnsee & Collins (2021)**. DOI: 10.1126/scirobotics.abf1078 — 外骨骼4参数样条控制器初始参数的实验依据
3. **MyoSuite** — 底层肌骨仿真框架，`myosuite/` 目录的上游项目
4. **MuJoCo** — 物理引擎，所有仿真的底层支撑
5. **CMA-ES / pycma** — https://github.com/CMA-ES/pycma — 协方差矩阵自适应进化策略库
