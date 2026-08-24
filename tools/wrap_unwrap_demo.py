"""
wrap 与 unwrap 演示（纯 Python，零依赖）
========================================

不依赖 gym/gymnasium，用几十行纯 Python 自己实现一个迷你 wrapper 机制，
把 gym.make(...).unwrapped 背后的道理讲清楚。

对照本项目 create_environment 的两行：

    env = gym.make(env_id, ...).unwrapped                        # 单环境 / 渲染
    env = SubprocVecEnv([lambda: gym.make(env_id, ...).unwrapped, ...])  # 多环境

运行：
    python tools/wrap_unwrap_demo.py
"""


# ---------------------------------------------------------------------------
# 1) 一个极简"环境"：只有步数计数，自己永远不结束
# ---------------------------------------------------------------------------
class TinyEnv:
    """对应 myoassist_leg_base：环境自己决定何时结束（自管理截断）。"""

    def __init__(self):
        self.step_count = 0
        # 专有属性/方法 —— 对应 myoassist 的 self.sim / mujoco_render_frames
        # / set_target_velocity_mode_manually 这类"只有裸环境才有"的接口
        self.favorite_color = "blue"

    def reset(self):
        self.step_count = 0
        return "obs"

    def step(self, action):
        self.step_count += 1
        # (obs, reward, terminated, truncated) —— 永远不结束
        return "obs", 1.0, False, False

    def say_hello(self):
        return f"hi, I am {type(self).__name__}, favorite_color={self.favorite_color}"


# ---------------------------------------------------------------------------
# 2) 迷你版 Wrapper：所有包装器的基类（仿 gymnasium 的 Wrapper）
# ---------------------------------------------------------------------------
class BaseWrapper:
    def __init__(self, env):
        self.env = env

    @property
    def unwrapped(self):
        """沿 .env 链一路剥到最里面的原始环境。"""
        e = self.env
        while getattr(e, "env", None) is not None:
            e = e.env
        return e

    # 注意：gymnasium 1.x 的 Wrapper 并不定义 __getattr__ 转发，
    # 所以专有属性/方法在 wrapped 对象上访问会 AttributeError ——
    # 这正是本项目两个分支都必须 .unwrapped 的硬理由。
    def reset(self):
        return self.env.reset()

    def step(self, action):
        return self.env.step(action)


# ---------------------------------------------------------------------------
# 3) 两个具体包装器：TimeLimit（超步自动截断）和 OrderEnforcing（必须先 reset）
# ---------------------------------------------------------------------------
class TimeLimitWrapper(BaseWrapper):
    """仿 gymnasium.TimeLimit：超过 max_steps 时自动注入 truncated=True。"""

    def __init__(self, env, max_steps):
        super().__init__(env)
        self.max_steps = max_steps
        self._step_count = 0

    def reset(self):
        self._step_count = 0
        return super().reset()

    def step(self, action):
        self._step_count += 1
        obs, reward, terminated, truncated = super().step(action)
        if self._step_count >= self.max_steps:
            truncated = True  # 外层包装器替环境兜底：强制截断
        return obs, reward, terminated, truncated


class OrderEnforcingWrapper(BaseWrapper):
    """仿 gymnasium.OrderEnforcing：不 reset 就直接 step 会报错。"""

    def __init__(self, env):
        super().__init__(env)
        self._has_reset = False

    def reset(self):
        self._has_reset = True
        return super().reset()

    def step(self, action):
        if not self._has_reset:
            raise RuntimeError("ResetNeeded: 必须先 reset() 再 step()！")
        return super().step(action)


def gym_make(env, max_episode_steps=10):
    """迷你版 gym.make：把环境按固定顺序套上包装器。"""
    return OrderEnforcingWrapper(TimeLimitWrapper(env, max_episode_steps))


# ---------------------------------------------------------------------------
# 4) 演示
# ---------------------------------------------------------------------------
def print_wrapper_chain(env):
    """从外层向内层逐层打印包装链。"""
    names, e = [], env
    while True:
        names.append(type(e).__name__)
        inner = getattr(e, "env", None)
        if inner is None or inner is e:
            break
        e = inner
    print("  wrapper 链（外层 -> 内层）: " + " < ".join(names))


def main():
    print("=" * 66)
    print("Step 1 | gym_make() —— 自动包装")
    print("=" * 66)
    env = gym_make(TinyEnv())
    print_wrapper_chain(env)

    print("\n" + "=" * 66)
    print("Step 2 | wrapped vs unwrapped 的对象类型")
    print("=" * 66)
    print(f"  type(env)            = {type(env).__name__}")
    print(f"  type(env.unwrapped)  = {type(env.unwrapped).__name__}")
    print(f"  env is env.unwrapped = {env is env.unwrapped}")

    print("\n" + "=" * 66)
    print("Step 3 | 专有属性/方法 —— wrapper 不转发，必须 unwrap")
    print("=" * 66)
    for name in ("favorite_color", "say_hello"):
        try:
            getattr(env, name)()
        except AttributeError:
            print(f"  env.{name:<14} -> AttributeError（专有接口被包装层挡住）")
        except TypeError:
            print(f"  env.{name:<14} = {getattr(env, name)}（被挡住了？见下方 unwrap）")
    print(f"  env.unwrapped.favorite_color = {env.unwrapped.favorite_color}")
    print(f"  env.unwrapped.say_hello()    = {env.unwrapped.say_hello()}")

    print("\n" + "=" * 66)
    print("Step 4 | step() 行为差异 —— TimeLimit 自动截断 vs 裸环境无限跑")
    print("=" * 66)
    print("  wrapped 环境连跑 15 步：")
    env.reset()
    for i in range(1, 16):
        _, _, terminated, truncated = env.step(0)
        if terminated or truncated:
            print(f"    第 {i:2d} 步: terminated={terminated}, truncated={truncated}   <-- 被 TimeLimit 截断")
            break
        print(f"    第 {i:2d} 步: terminated={terminated}, truncated={truncated}")

    print("  unwrapped 环境连跑 15 步：")
    raw = gym_make(TinyEnv()).unwrapped
    raw.reset()
    for i in range(1, 16):
        _, _, terminated, truncated = raw.step(0)
        if terminated or truncated:
            print(f"    第 {i:2d} 步: terminated={terminated}, truncated={truncated}   <-- 竟然会停？")
            break
    else:
        print("    15 步跑完，全程没有截断 —— 结束与否全由环境自己/调用方决定")

    print("\n" + "=" * 66)
    print("Step 5 | OrderEnforcing —— 不 reset 就直接 step")
    print("=" * 66)
    fresh = gym_make(TinyEnv())
    try:
        fresh.step(0)
        print("  wrapped   : 竟然没报错？")
    except RuntimeError as e:
        print(f"  wrapped   : 报错 {type(e).__name__}: {e}")
    fresh_raw = gym_make(TinyEnv()).unwrapped
    try:
        print(f"  unwrapped : 正常返回 {fresh_raw.step(0)}")
    except Exception as e:
        print(f"  unwrapped : 报错 {type(e).__name__}: {e}")

    print("\n" + "=" * 66)
    print("对照本项目 create_environment")
    print("=" * 66)
    print(
        """
  env = gym.make(env_id, **gym_make_args).unwrapped
        ^^^^       ^^^^^^^^^^^^^^^^^^^^^^^   ^^^^^^^^^
         |                |                      |
         |                +-- 自动挂 TimeLimit /  +-- 剥掉它们，
         |                    OrderEnforcing /      拿回你自己的裸环境
         |                    PassiveEnvChecker
         +-- 需要 sim / mujoco_render_frames / set_target_velocity_mode_manually
             等 MyoAssist 专有接口（wrapper 不转发这些，必须 unwrap 才能访问）；
             且环境已在 step() 里自管理截断（CUSTOM_MAX_EPISODE_STEPS），
             TimeLimit 的自动截断反而多余，所以两个分支都 .unwrapped。

  env = SubprocVecEnv([lambda: gym.make(env_id, ...).unwrapped, ...])
        ^^^^^^^^^^^^                                          ^^^^^^^^^
        多环境时由 SubprocVecEnv 在"外面"重新提供标准接口：
        子进程里跑裸环境（可以用专有接口），父进程统一 step/reset。
"""
    )


if __name__ == "__main__":
    main()
