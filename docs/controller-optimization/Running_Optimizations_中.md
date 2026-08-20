# 运行优化（Running Optimizations）

本指南介绍如何使用 `run_optim.py` 脚本对反射控制器进行优化，涵盖基础与高级设置。

## 快速开始

优化框架采用统一的方式，以 `run_optim.py` 作为主要入口点。

在进行长时间运行之前，请先开启模型缓存。CMA-ES 会为每个候选解组合一个模型，因此在
`--popsize 32 --maxiter 1000` 下运行大约需要组合 32,000 个模型。如果不使用缓存，
每个模型的成本会高出 13 到 15 倍：

```bash
export MYOASSIST_CACHE_DIR=~/.cache/myoassist
```

参见[缓存](https://myoassist.neumove.org/modeling/devices/exporting-and-loading/#caching)。

### 使用 `run_optim.py`

`run_optim.py` 脚本提供了一种跨平台运行优化的方式：

```bash
# 进入 ctrl_optim 目录
cd ctrl_optim

# 使用配置名称运行优化
python run_optim.py <config_name>
```

例如，运行教程配置：

```bash
python run_optim.py tutorial
```

### 可用配置

`optim/training_configs/` 目录包含针对不同优化场景的配置文件。每个配置都有一个 Windows `.bat` 文件。其中有六个还提供 Unix `.sh` 文件：`tutorial`、`debug`、`amp_kfoot`、`kfoot_stiffness`、`reflex_bilat` 和 `anatomics_rom`。其余五个（`baseline`、`exo_4param`、`exo_4param_kine`、`exo_npoint` 和 `exo_npoint_cont`）仅提供 `.bat` 文件，因此无法在 Unix 上运行。`run_optim.py` 会根据你的操作系统选择相应的文件类型。下面是一些示例配置。

| 配置                   | 描述                                                                                     |
|-----------------------|---------------------------------------------------------------------------------------------------------|
| `baseline`            | 对不带外骨骼的 22 肌肉模型进行的标准优化。一个不错的起点。                                              |
| `debug`               | 迭代次数很少的小型快速运行，用于测试和调试优化流程。                                                   |
| `tutorial`            | 用于学习框架的教程配置。                                                                                 |
| `exo_4param`          | 使用 4 参数样条作为力矩曲线的外骨骼控制器优化。                                                   |
| `exo_4param_kine`     | 与 `exo_4param` 相同；两者都使用 `-kine` 代价。区别仅在于 `--save_path`。                          |
| `exo_npoint`          | 使用现代 n 点样条控制器进行外骨骼优化。                                                                 |
| `exo_npoint_cont`     | 延续优化示例，从先前运行的结果继续。                                                                      |
| `reflex_bilat`        | 在 3D 26 肌肉模型上进行双侧反射，每条腿拥有独立的参数块。                                                |
| `amp_kfoot`           | 被动 K-Foot 假肢上的截肢者反射（见[截肢与假肢控制](Amputee_Prosthetic_Control_zh.md)）。                  |
| `kfoot_stiffness`     | 截肢者反射加假肢踝关节刚度优化。                                                                         |
| `anatomics_rom`       | 使用 Anatomics 外骨骼进行踝关节活动范围研究。                                                          |

### 列出可用配置

要查看所有可用配置：

```bash
python run_optim.py
```

这将显示 `optim/training_configs/` 目录中所有可用配置文件。

## 配置文件结构

`optim/training_configs/` 中的配置文件保存了 `train.py` 脚本的命令行参数。`run_optim.py` 从 `ctrl_optim/optim/` 运行该文件。`.bat` 和 `.sh` 文件包含相同的参数，只是续行语法不同。

附带的 `tutorial` 配置是一次延续运行。它使用 `--param_path ../results/optim_results/tutorial_prep` 加载准备好的参数。

**示例 `tutorial.bat`：**
```batch
python train.py ^
    --msk myolegs22 ^
    --device Tutorial_L1 ^
    --sim_time 20 ^
    --pose_key walk_left ^
    --num_strides 5 ^
    --delayed 0 ^
    --optim_mode single ^
    --reflex_mode uni ^
    --tgt_vel 1.25 ^
    --trunk_err_type ref_diff ^
    --tgt_sym_th 0.1 ^
    --tgt_grf_th 1.5 ^
    -eff ^
    --ExoOn 1 ^
    --use_4param_spline ^
    --max_torque 100.0 ^
    --popsize 8 ^
    --maxiter 50 ^
    --threads 8 ^
    --sigma_gain 10 ^
    --param_path ../results/optim_results/tutorial_prep ^
    --save_path tutorial
```

**等效的 `tutorial.sh`：**
```bash
exec "$PYTHON_CMD" -m ctrl_optim.optim.train \
    --msk myolegs22 \
    --device Tutorial_L1 \
    --sim_time 20 \
    --pose_key walk_left \
    --num_strides 5 \
    --delayed 0 \
    --optim_mode single \
    --reflex_mode uni \
    --tgt_vel 1.25 \
    --trunk_err_type ref_diff \
    --tgt_sym_th 0.1 \
    --tgt_grf_th 1.5 \
    -eff \
    --ExoOn 1 \
    --use_4param_spline \
    --max_torque 100.0 \
    --popsize 8 \
    --maxiter 50 \
    --threads 8 \
    --sigma_gain 10 \
    --param_path ../results/optim_results/tutorial_prep \
    --save_path tutorial
```

### 创建自定义配置

你可以通过以下方式创建新配置：
1. 复制 `optim/training_configs/` 中现有的 `.bat` 或 `.sh` 文件
2. 根据需要修改参数
3. 以新名称保存到 `optim/training_configs/` 目录

## 参数

`train.py` 脚本接受大量参数以自定义优化。以下是按类别分组的最重要参数。完整列表请参阅 `ctrl_optim/optim/config/arg_parser.py`。

### 模型配置

原始注册表键定义了环境。完整参考请参见[定义环境](../getting-started/defining-an-environment_zh.md)。运行 `python -m assist_sim list` 可查看有效键。

- `--msk`：人体 MSK 模型。2D 使用 `myolegs22`。3D 使用 `myolegs26` 或 80 肌肉的 `myolegs`。肌肉数量以及 2D/3D 控制模式由该键决定。
- `--device`：辅助设备，例如 `Tutorial_L1`、`Humotech_L1` 或 `DephyExoBoot_L1`。
- `--terrain`：可选地形。给出 `myoassist_terrains` JSON 路径，或内联配置，如 `'{"terrain":"slope","deg":8}'`。平地可省略。`slope` 地形设置了路面坡度，因此没有单独的 `--tgt_slope`。
- `--env-spec`：JSON 环境规格（`{msk, device, terrain}`）的路径。用它替代上述三个标志。
- `--delayed`：设为 `1` 以使用延迟肌肉动力学。默认关闭。

### 运行与仿真设置

每个随附配置都会设置这些参数。

- `--optim_mode`：运行模式。框架实现了 `single`（单次优化）和 `evaluate`（评估现有参数）。帮助文本中的其他值尚未实现。
- `--save_path`：结果文件夹的名称或路径。
- `--sim_time`：每次评估的最大仿真时间（秒）。
- `--num_strides`：计算代价所需的最小步数。
- `--pose_key`：模型的初始关键姿态，例如 `walk_left`。

### 反射模式

`--reflex_mode` 设置反射控制器如何将参数映射到两条腿。

- `uni` 或不设置（默认）：对称。一个反射块驱动双腿。`uni` 是常见的对称设置。所有随附的 2D 配置和教程均对 `myolegs22` 使用 `--reflex_mode uni`。
- `bilat`：双侧。每条腿拥有自己的反射块，因此两条腿相互独立。这会使反射参数数量翻倍。
- `amp`：截肢者。这是 `bilat` 加假肢容差，适用于佩戴假肢设备的模型。见[截肢与假肢控制](Amputee_Prosthetic_Control_zh.md)。
- `ind`：另一个可接受的值。框架将其映射为对称，与 `uni` 相同。

### 截肢者与假肢设备

要在截肢模型上进行优化，请将假肢设备与 `--reflex_mode amp` 搭配使用。若要同时调优被动假肢踝关节，请添加 `--optimize_stiffness`。两者详见[截肢与假肢控制](Amputee_Prosthetic_Control_zh.md)。

### 踝关节活动范围

`--ankle_range MIN MAX` 限制踝关节活动范围（弧度）。`MIN` 是跖屈限位（负值），`MAX` 是背屈限位（正值）。框架会在每一步将双踝限制在该范围内。可将其作为扫描研究变量，例如与 Anatomics 外骨骼配合使用。

### 外骨骼配置
- `--ExoOn`：设为 `1` 启用外骨骼，或 `0` 禁用。
- `--use_4param_spline`：在外骨骼开启时使用 4 参数样条控制器。不加该标志则使用 n 点样条。
- `--n_points`：n 点样条的控制点数量，例如 `4`。
- `--max_torque`：外骨骼可施加的最大力矩（Nm）。同时也为两个控制器设置初始力矩值。默认 `10.0`。
- `--fixed_exo`：固定外骨骼参数，使优化器不调优它们。仅影响 4 参数控制器。对 n 点样条无效果。

### 优化目标
- `-eff`、`-vel`、`-kine` 等：这些标志设置代价函数的主要目标。它们互斥。选择最符合你目标的一项，例如最小化能耗、匹配目标速度或跟踪参考运动学。更多信息见（**[理解代价函数](Understanding_Cost_zh.md)**）。
- `--tgt_vel`：目标行走速度（m/s）。
- `--tgt_sym_th`：代价中使用的对称性阈值。
- `--tgt_grf_th`：代价中使用的归一化地面反作用力阈值。

### 优化器设置
- `--popsize`：CMA-ES 优化器的种群大小（每代候选解数量）。
- `--maxiter`：优化器运行的最大代数。
- `--threads`：评估种群时使用的并行线程数。
- `--sigma_gain`：CMA-ES 优化器初始标准差（步长）的增益值（若 gain = 1，则 sigma = 0.01）。

### 延续优化

你可以从先前优化的结果开始新的优化，或恢复被中断的运行。

#### `--param_path`：使用现有参数开始
用于以先前运行的最佳参数为起点，开始新的优化（例如使用不同的代价函数或模型）。
- **参数**：`--param_path <path_to_results_folder>`
- **行为**：脚本会在指定文件夹中查找 `*_BestLast.txt` 文件并将其加载为新优化的初始猜测。仅含 `_Best.txt` 文件的文件夹无效。优化器的内部状态（协方差矩阵、步长）会被重置。

**示例**：
```bash
--param_path results/exo_npoint_date_time
```

#### `--pickle_path`：恢复已保存的状态
用于继续被提前停止的优化。
- **参数**：`--pickle_path <path_to_pickle_file>`
- **行为**：脚本加载一个 `.pkl` 文件，其中包含 CMA-ES 优化器在保存时刻的完整状态。这样优化可以从停下的位置精确恢复，保留协方差矩阵、步长和进化路径。优化结束时或被中断时，pickle 文件会自动保存在结果目录中。

**示例**：
```bash
--pickle_path results/my_run_date_time/myo_reflex_date_time.pkl
```

## 结果与配置保存

### 结果位置
所有结果会自动保存到 `ctrl_optim/results/optim_results/` 目录，每次运行都会创建带时间戳的子目录。

### 配置保存
系统会自动保存每次运行使用的最终配置：

- **配置文件**：根据平台保存为 `config_name_timestamp.bat` 或 `config_name_timestamp.sh`
- **结果目录**：创建包含所有优化输出的带时间戳子目录

### 输出文件
每次优化运行会产生多个输出文件：
- `*_Best.txt`：优化过程中找到的最佳参数
- `*_BestLast.txt`：最终种群中的最佳参数
- `*_Cost.txt`：最佳解的详细代价分解
- `*_Pickle.pkl`：用于恢复优化的 CMA-ES 状态
- `outcmaes/`：包含 CMA-ES 内部文件的目录

## 故障排查

### 常见问题

1. **"Module not found" 错误**：确保从正确的目录运行：
   ```bash
   cd ctrl_optim
   python run_optim.py <config_name>
   ```

2. **配置未找到**：验证配置名称是否存在于 `optim/training_configs/` 目录：
   ```bash
   python run_optim.py
   # 这将列出所有可用配置
   ```

3. **文件路径错误**：系统会自动解析路径，但请确保目录结构正确。

4. **.sh 文件权限被拒绝**：`run_optim.py` 脚本会自动处理，但如果你需要直接运行 .sh 文件：
   ```bash
   chmod +x optim/training_configs/*.sh
   ```

`run_optim.py` 在所有操作系统上使用同一条命令。这适用于同时附带 `.bat` 和 `.sh` 文件的配置。五个仅 `.bat` 的配置只能在 Windows 上运行。要在 Unix 上使用，请先将参数复制到 `.sh` 文件中。
