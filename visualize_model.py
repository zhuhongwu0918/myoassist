#!/usr/bin/env python3
"""
可视化训练好的模型
用法: python visualize_model.py <训练结果目录路径> [步数]
"""
import sys
import os
import json
from pathlib import Path

# 设置渲染后端
os.environ['MUJOCO_GL'] = 'glfw'  # 使用 GLFW 窗口渲染

from rl_train.envs.environment_handler import EnvironmentHandler
from rl_train.train.train_configs.config_imiatation_exo import ExoImitationTrainSessionConfig
from stable_baselines3 import PPO

def visualize_trained_model(session_dir, num_steps=1000):
    """
    加载训练好的模型并可视化运行

    参数:
        session_dir: 训练结果目录路径
        num_steps: 运行步数
    """
    session_path = Path(session_dir)

    # 1. 加载配置
    config_path = session_path / "session_config.json"
    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    print(f"加载配置: {config_path}")
    with open(config_path, 'r') as f:
        config_dict = json.load(f)

    # 找到最新的模型
    model_dir = session_path / "trained_models"
    model_files = sorted(model_dir.glob("model_*.zip"))
    if not model_files:
        raise FileNotFoundError(f"没有找到训练好的模型: {model_dir}")

    latest_model = model_files[-1]
    print(f"加载模型: {latest_model}")

    # 2. 从配置文件重建完整的配置对象
    from rl_train.utils.data_types import DictionableDataclass

    # 获取正确的配置类型
    config_type = EnvironmentHandler.get_config_type_from_session_id(config_dict["env_params"]["env_id"])

    # 从字典重建配置
    config = DictionableDataclass.create(config_type, config_dict)

    # 强制单环境用于可视化
    config.env_params.num_envs = 1

    # 3. 创建环境（带渲染）
    print("创建环境（启用渲染）...")
    env = EnvironmentHandler.create_environment(config, is_rendering_on=True, is_evaluate_mode=True)

    # 4. 加载模型
    print("加载训练好的策略...")
    model = PPO.load(str(latest_model))

    # 5. 运行可视化
    print(f"\n开始可视化（运行 {num_steps} 步）...")
    print("按 Ctrl+C 停止\n")

    obs, info = env.reset()
    total_reward = 0
    episode_count = 0

    try:
        for step in range(num_steps):
            # 使用训练好的策略选择动作
            action, _states = model.predict(obs, deterministic=True)
            obs, reward, done, truncated, info = env.step(action)
            total_reward += reward

            # 每100步打印一次信息
            if step % 100 == 0:
                print(f"步数: {step}/{num_steps}, 累计奖励: {total_reward:.2f}, 回合数: {episode_count}")

            # 如果回合结束，重置
            if done or truncated:
                episode_count += 1
                print(f"\n回合 {episode_count} 结束! 奖励: {reward:.3f}")
                obs, info = env.reset()

    except KeyboardInterrupt:
        print("\n\n用户中断可视化")

    finally:
        env.close()
        print(f"\n总步数: {step + 1}")
        print(f"总回合数: {episode_count}")
        print(f"平均奖励: {total_reward / (step + 1):.4f}")
        print("\n可视化结束")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python visualize_model.py <训练结果目录> [步数]")
        print("\n示例:")
        print("  python visualize_model.py rl_train/results/train_session_20260820-135449")
        print("  python visualize_model.py rl_train/results/train_session_20260820-135449 2000")
        sys.exit(1)

    session_dir = sys.argv[1]
    num_steps = int(sys.argv[2]) if len(sys.argv) > 2 else 1000

    visualize_trained_model(session_dir, num_steps)
