# 故障排查（Troubleshooting）

## 错误：macOS 上的 MuJoCo Viewer

```
.../lib/python3.11/site-packages/mujoco/viewer.py", line 590, in launch_passive
    raise RuntimeError(
RuntimeError: `launch_passive` requires that the Python script be run under `mjpython` on macOS
```

**解决方案：**
如果你在 macOS 上看到此错误，只需用 `mjpython` 而不是 `python` 来运行你的脚本。
你不需要安装任何额外的东西。只需更改命令：

```bash
mjpython example.py
```


## 错误：`ModuleNotFoundError: No module named 'flatten_dict'`

```
ModuleNotFoundError: No module named 'flatten_dict'
```

**解决方案：**
再次运行该命令。这通常会自动解决问题。


## 从仓库根目录运行命令

有些文件通过相对路径加载。例如，`reference_data/segmented.npz` 相对于当前目录加载。请从仓库根目录运行 `run_train.py` 和 `run_policy_eval.py`。如果你从其他目录运行它们，将找不到这些文件。
