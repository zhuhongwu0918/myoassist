# 环境规格示例（Environment spec examples）

这里的每个 `.json` 都是一个完整的**环境规格** —— 人体 MSK 模型 + 辅助设备 + 地形 —— CO 和 RL 两条流程都可以使用。完整的字段参考请参见[定义环境](../getting-started/defining-an-environment_zh.md)。

| 文件 | MSK | 设备 | 地形 |
|------|-----|--------|---------|
| `env_exo_flat.json` | `myolegs22` | `Humotech_L1` | 平地 |
| `env_exo_slope.json` | `myolegs22` | `Humotech_L1` | 8° 斜坡 |
| `env_prosthesis_rough.json` | `myolegs22` | `OpenSourceLeg_A_L1` | 粗糙高度场（6 cm） |
| `env_tiled_course.json` | `myolegs22` | `Humotech_L1` | 平铺 1×3 赛道：平地 → 斜坡 → 楼梯 |
| `env_tiled_random.json` | `myolegs22` | `OpenExo_L1` | 随机化 3×3 平铺网格 |

## 使用其中一个

```bash
# 控制器优化（反射）
python -m ctrl_optim.optim.train --env-spec docs/examples/env_exo_slope.json --sim_time 20 -eff --ExoOn 1 ...
```

```python
# 以编程方式
from myoassist_utils.env_spec import EnvSpec
spec = EnvSpec.load("docs/examples/env_exo_slope.json").validate()
xml = spec.compose()   # -> 可加载的 MJCF 字符串
```

要制作自己的规格，请复制一个并更改键 —— `python -m assist_sim list`
会显示所有有效的 MSK / 设备，而地形字段（统一或平铺）在[定义环境](../getting-started/defining-an-environment_zh.md)中有文档说明。
