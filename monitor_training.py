#!/usr/bin/env python3
"""
实时监控训练进度
"""
import json
import time
import sys
from pathlib import Path

def monitor_training(session_dir, refresh_interval=10):
    """实时显示训练进度"""
    session_path = Path(session_dir)
    log_file = session_path / "train_log.json"

    if not log_file.exists():
        print(f"等待训练日志: {log_file}")
        while not log_file.exists():
            time.sleep(1)

    print(f"监控训练日志: {log_file}")
    print("=" * 80)

    last_size = 0
    while True:
        try:
            # 检查文件是否更新
            current_size = log_file.stat().st_size
            if current_size > last_size:
                last_size = current_size

                # 读取日志
                with open(log_file, 'r') as f:
                    content = f.read().strip()
                    if not content:
                        print("日志文件为空，等待数据...")
                        time.sleep(refresh_interval)
                        continue
                    logs = json.loads(content)

                if logs:
                    latest = logs[-1]

                    # 提取关键信息
                    total_steps = latest.get('total_timesteps', 0)
                    ep_len = latest.get('rollout', {}).get('ep_len_mean', 0)
                    ep_rew = latest.get('rollout', {}).get('ep_rew_mean', 0)

                    # 训练指标
                    train_metrics = latest.get('train', {})

                    # 清屏并显示
                    print("\033[2J\033[H")  # 清屏
                    print("=" * 80)
                    print(f"训练监控 - {session_path.name}")
                    print("=" * 80)
                    print(f"\n总步数: {total_steps:,}")
                    print(f"平均回合长度: {ep_len:.2f}")
                    print(f"平均回合奖励: {ep_rew:.4f}")

                    if train_metrics:
                        print("\n训练指标:")
                        print(f"  Policy Loss: {train_metrics.get('policy_gradient_loss', 0):.6f}")
                        print(f"  Value Loss: {train_metrics.get('value_loss', 0):.6f}")
                        print(f"  Entropy Loss: {train_metrics.get('entropy_loss', 0):.4f}")
                        print(f"  KL Divergence: {train_metrics.get('approx_kl', 0):.6f}")

                    # 奖励分解
                    reward_acc = latest.get('reward_accumulate', {})
                    if reward_acc:
                        print("\n奖励组成:")
                        for key, value in list(reward_acc.items())[:8]:
                            if isinstance(value, (int, float)):
                                print(f"  {key}: {value:.2f}")

                    print(f"\n最后更新: {latest.get('time', 'N/A')}")
                    print(f"刷新间隔: {refresh_interval}秒")
                    print("\n按 Ctrl+C 退出")

            time.sleep(refresh_interval)

        except KeyboardInterrupt:
            print("\n\n监控已停止")
            break
        except Exception as e:
            print(f"\n错误: {e}")
            time.sleep(refresh_interval)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        # 自动找最新的训练目录
        results_dir = Path("rl_train/results")
        sessions = sorted(results_dir.glob("train_session_*"), key=lambda p: p.stat().st_mtime, reverse=True)
        if sessions:
            session_dir = sessions[0]
            print(f"自动选择最新训练: {session_dir}")
        else:
            print("用法: python monitor_training.py [训练目录]")
            print("或自动监控最新训练")
            sys.exit(1)
    else:
        session_dir = sys.argv[1]

    refresh_interval = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    monitor_training(session_dir, refresh_interval)
