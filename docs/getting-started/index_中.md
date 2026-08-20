# MyoAssist 快速入门（Getting Started with MyoAssist）

欢迎使用 MyoAssist！本节将帮助你快速上手本框架。

## 环境要求（Prerequisites）

开始之前，请确保你已具备：
- [Python 3.11](https://www.python.org/downloads/release/python-3119/) 或更新版本（安装时请将 Python 添加到 PATH）。Python 3.11 和 3.12 是经过测试的版本。
- [Git](https://git-scm.com/downloads)
- [uv](https://docs.astral.sh/uv/)（MyoAssist 使用的安装工具；参见下面的虚拟环境步骤）
- [Visual Studio Code](https://code.visualstudio.com/download) 或其他 IDE

MuJoCo 会随包自动安装。MyoAssist 安装固定为 `mujoco>=3.4,<3.5`。独立的兄弟包（`assist_sim`、`myoassist-terrains`）可能构建在不同或更宽的 MuJoCo 版本范围上；如果你单独安装某个兄弟包，请查看那些仓库的说明。

## 安装（Installation）

### 第 1 步：克隆仓库
```bash
git clone https://github.com/neumovelab/myoassist.git
cd myoassist
```

### 第 2 步：设置虚拟环境（venv）

> *如果你已经熟悉 Python 虚拟环境并倾向于自行设置环境，此步骤为可选。*

<div class="info-box">
   <h4>为什么使用 VENV？</h4>
   <p>虚拟环境（venv）允许你为项目创建隔离的 Python 环境。这意味着每个项目都可以拥有自己的依赖，无论其他项目有什么依赖。这有助于防止版本冲突，并使你的开发过程更可靠、更可复现。</p>
</div>

### 如何设置虚拟环境

1. **创建虚拟环境：**

   - 在 **Linux/macOS** 上：
   ```bash
   python3.11 -m venv .my_venv
   ```
   - 在 **Windows** 上：
   ```bash
   py -3.11 -m venv .my_venv
   ```
   这将在你的项目目录中创建一个名为 `.my_venv` 的新文件夹。

2. **激活虚拟环境：**
   - 在 **Linux/macOS** 上：
     ```bash
     source .my_venv/bin/activate
     ```
   - 在 **Windows** 上：
     ```bash
     .my_venv\Scripts\activate
     ```

   > **注意：**
   >  
   > 激活后，你的命令提示符将在当前目录前显示 `(.my_venv)`。
   > 在本项目上工作时，必须始终激活虚拟环境。如果你在按照文档操作时遇到问题，请再次确认你的虚拟环境是否已激活。
   >  
   > **示例：**
   > ```bash
   > (.my_venv) D:\your\project\directory\myoassist
   > ```
   >  
   > 这表明虚拟环境当前处于激活状态。

3. **安装 uv（MyoAssist 使用的安装工具）：**
   ```bash
   pip install uv
   ```

   <div class="info-box">
     <h4>为什么使用 uv？</h4>
     <p>MyoAssist 使用 <code>uv</code> 安装，而不是普通的 <code>pip</code>。MyoSuite 2.8.4 在其元数据中固定了较旧版本的 MuJoCo，但框架需要 MuJoCo 3.4 来支持兄弟包（<code>myo-sim</code>、<code>assist-sim</code> 和 <code>myoassist-terrains</code>）。<code>pyproject.toml</code> 中的一行覆盖配置放宽了该固定版本限制，因此 <code>uv</code> 可以用一条命令解析整个依赖栈。普通的 <code>pip</code> 无法做到这一点，会因解析错误而中止。</p>
   </div>

4. **停用虚拟环境（可选）：**
   ```bash
   deactivate
   ```
   只有在你完全完成项目工作，或想切换到另一个虚拟环境时，才需要停用虚拟环境。
   大多数情况下，除非你特别想离开当前环境，否则无需停用。

创建并激活虚拟环境后，就可以安装所需的软件包了。这样可以确保你的依赖按项目管理，不会影响全局 Python 安装。

### 第 3 步：安装软件包
```bash
uv pip install -e .
```

这一条命令会安装 MyoAssist 及其所有依赖，包括来自 PyPI 的三个兄弟包（`myo-sim`、`assist-sim` 和 `myoassist-terrains`）。它使用 `uv`，因此 `pyproject.toml` 中的覆盖配置得以生效（参见上面的「为什么使用 uv？」）。

### 第 4 步：验证安装

```bash
python test_setup.py
```

你应该会看到类似下面的输出：

```bash
Test Summary
----------------------------------------
Total tests: 16
Passed: 16
Failed: 0
Total time: 13.60s
```

### 第 5 步：开启模型缓存（在训练之前）

MyoAssist 在内存中组合模型：它在运行时拼接 MSK 模型、设备和地形。一次训练运行为每个并行环境以及每个优化候选解构建一个模型，因此**不开启缓存时，每个环境的运行速度会慢 13 到 15 倍**。只需一个环境变量即可为两条训练流程开启缓存：

```bash
export MYOASSIST_CACHE_DIR=~/.cache/myoassist
```

在 Windows 命令提示符中，使用 `setx MYOASSIST_CACHE_DIR %USERPROFILE%\.cache\myoassist`，然后打开一个新终端。在 PowerShell 中，使用 `$env:MYOASSIST_CACHE_DIR = "$HOME\.cache\myoassist"`。

把这行加入你的 shell 配置文件，之后就不用再操心了。唯一的例外是 `myofullbody`，它太大，无法从缓存中获益。有关实测数值以及导致缓存未命中的规则，请参见[缓存](https://myoassist.neumove.org/modeling/devices/exporting-and-loading/#caching)。

## 下一步

- **[快速上手](https://myoassist.neumove.org/getting-started/quick-start/)**：运行一个最小环境以确认你的安装。
- **[定义环境](defining-an-environment_zh.md)**：一次性描述一个 `{msk, device, terrain}` 环境，即可在任一条流程中运行。
- **[示例](https://myoassist.neumove.org/getting-started/examples/)**：开箱即用的环境规格。
- **[仿真环境](https://myoassist.neumove.org/modeling/)**：你可以组合的 MSK 模型、设备和地形。
- **[强化学习](../reinforcement-learning/index_zh.md)** 和 **[控制器优化](../controller-optimization/index_zh.md)**：两大训练框架。
