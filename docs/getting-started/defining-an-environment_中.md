# 定义环境（Defining an Environment）

在 MyoAssist 中，一个**环境**是人体肌肉骨骼（MSK）模型、辅助**设备**和**地形**组合而成的单个 MuJoCo 模型。同一个定义驱动两条流程：反射**控制器优化（CO）**和**强化学习（RL）**。

## 环境规格（environment spec）

一个环境有三个字段。每个字段都是一个**原始注册表键（raw registry key）**：

```json
{ "msk": "myolegs22", "device": "Humotech_L1", "terrain": { "terrain": "slope", "deg": 8 } }
```

| 字段 | 含义 | 示例 |
|-------|------------|----------|
| `msk` | 人体 MSK 模型 | `myolegs22`、`myolegs26` |
| `device` | 辅助设备 | `DephyExoBoot_L1`、`Humotech_L1`、`OpenSourceLeg_A_L1`、`Tutorial_L1` |
| `terrain` | 地面（可选） | 平地省略；内联配置；或 terrains JSON 路径 |

运行 **`python -m assist_sim list`** 可查看所有已安装的 MSK 和设备，以及哪些组合兼容。

### MSK 模型

| 键 | 肌肉数量 | 描述 |
|-----|---------|-------------|
| `myolegs22` | 22 | **2D**（矢状面） |
| `myolegs26` | 26 | **3D** |
| `myolegs` | 80 | **3D**。80 肌肉模型的键是 `myolegs`，而不是 `myolegs80`。 |
| `myofullbody` | 416 | **3D**，带手臂和躯干肌肉的全身模型 |

肌肉数量和 2D/3D 控制模式由 `msk` 决定。你无需单独设置它们。

对于 3D 键，CO 流程会用命名的矢状面自由度替换自由根节点，因为反射控制器从这些自由度读取骨盆状态。这是自动完成的。参见[根节点框架](https://myoassist.neumove.org/modeling/msk-models/#root-frame)。

### 发现与验证

`python -m assist_sim list` 打印权威的已安装集合。`python -m assist_sim validate <msk> <device>` 检查一对组合。

```bash
python -m assist_sim list                       # 所有已安装的 MSK / 设备 + 兼容性
python -m assist_sim validate myolegs22 Humotech_L1
```

`EnvSpec.validate()` 在代码中执行相同的检查。当键未知或 MSK 与设备组合不兼容时，它会抛出 `ValueError`，并列出有效选项。

> **注意：**
>  
> 环境验证**必须**使用正确的原始注册表键，否则返回的结果将不准确。
>  
> **示例：**
> ```bash
> python -m assist_sim validate myolegs22 Dephy_L1
> INVALID: myolegs22 x Dephy_L1
>
> python -m assist_sim validate myolegs22 DephyExoboot_L1
> INVALID: myolegs22 x DephyExoboot_L1
>
> python -m assist_sim validate myolegs22 DephyExoBoot_L1
> OK: myolegs22 x DephyExoBoot_L1
>    human:  myolegs22 (composed MjSpec, 38 bodies)
>    config: ...\Lib\site-packages\assist_sim\models\DephyExoBoot\L1config.yaml
> ```

### 地形（Terrain）

对于平坦的、实际上无限大的地面，将 `terrain` 留空（或设为 `null`）。否则给出以下任一项。

**统一表面**（一个平面或一个高度场）：

| `terrain` | 结果 |
|-----------|--------|
| `{ "terrain": "flat" }` | 一个平坦平面 |
| `{ "terrain": "slope", "deg": 8 }` | 恒定 8° 上坡（倾斜平面） |
| `{ "terrain": "random", "amplitude": 0.06 }` | 粗糙高度场，起伏最高 6 cm |
| `{ "terrain": "sinusoidal", "amplitude": 0.05, "period": 1.0 }` | 起伏的波浪 |

这些是常见情况。完整的字段集，包括 `resolution`、`extent`、`safe_zone_radius` 和 `seed`，见[统一地形](https://myoassist.neumove.org/modeling/terrains/uniform/)。请将 `resolution` 和 `extent` 一起理解：它们共同决定高度场单元的大小，这才是脚下实际感受到的粗糙程度。

**平铺网格（Tiled grid）**：一个带 `grid` 和逐单元 `tiles` 的[地形配置](https://myoassist.neumove.org/modeling/terrains/configuration/)。瓦片类型有 `flat`、`slope`、`stairs`、`pyramid_stairs`、`rough`、`boulders`、`stepping_stones`、`discrete_obstacles` 和 `gap`。你可以用 `randomization` 填充空单元。配置可以内联给出，也可以作为 JSON 文件路径：

```json
"terrain": {
  "grid": { "rows": 1, "cols": 3, "tile_size": [4.0, 4.0] },
  "border": { "width": 0.5 },
  "tiles": [
    { "row": 0, "col": 0, "type": "flat",   "params": { "height": 0.0 } },
    { "row": 0, "col": 1, "type": "slope",  "params": { "angle_deg": 8.0, "axis": "x" } },
    { "row": 0, "col": 2, "type": "stairs", "params": { "n_steps": 5, "step_height": 0.1, "axis": "x" } }
  ]
}
```

地形决定路线的坡度。`slope` 地形就是斜坡本身，评估相机、代价函数和读数都从中推导出角度。没有单独的坡度标志。

> **反射 CO 用于稳态运动。** 恒定地形是可以处理的。CO 流程和反射控制器不对高度可变的地形（粗糙、楼梯、混合瓦片）进行优化。可变地形请使用 RL。

## 使用环境规格

### 控制器优化（反射）

```bash
# 原始标志
python -m ctrl_optim.optim.train --msk myolegs22 --device Humotech_L1 \
    --terrain '{"terrain":"slope","deg":8}' --sim_time 20 -eff --ExoOn 1 ...

# 或共享的 env-spec 文件
python -m ctrl_optim.optim.train --env-spec docs/examples/env_exo_slope.json --sim_time 20 -eff --ExoOn 1 ...
```

### 强化学习

在训练配置 JSON 的 `env_params` 上设置相同的三个字段：

```json
"env_params": { "msk_key": "myolegs22", "device_key": "Humotech_L1", "terrain": null }
```

### 以编程方式使用

```python
from myoassist_utils.env_spec import EnvSpec

spec = EnvSpec.load("docs/examples/env_exo_slope.json")
# 或：EnvSpec(msk="myolegs22", device="Humotech_L1", terrain={"terrain": "slope", "deg": 8})

spec.validate()          # 根据注册表检查键；遇到错误键时会抛出异常并附带有效选项
xml = spec.compose()     # 返回一个可加载的 MuJoCo MJCF 字符串
spec.compose(export_path="my_env.xml")   # 同时写入一个独立的、可加载的文件
```

## 开箱即用的示例

[myoassist 仓库](https://github.com/neumovelab/myoassist/tree/main/docs/examples)中的 `docs/examples/` 目录包含可运行的环境规格：

| 文件 | 环境 |
|------|-------------|
| `env_exo_flat.json` | `myolegs22` + `Humotech_L1`，平地 |
| `env_exo_slope.json` | `myolegs22` + `Humotech_L1`，8° 斜坡 |
| `env_prosthesis_rough.json` | `myolegs22` + `OpenSourceLeg_A_L1`，粗糙高度场 |
| `env_tiled_course.json` | `myolegs22` + `Humotech_L1`，平地、斜坡与楼梯的组合赛道 |
| `env_tiled_random.json` | `myolegs22` + `OpenExo_L1`，随机化 3×3 平铺网格 |
