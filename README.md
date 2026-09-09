# 截图skill

使用codex执行截图任务时，他总是乱截图，没有截到我们预期的窗口。

可移植的 Codex `window-screenshot` skill，用于在 Windows 上枚举窗口、捕获指定窗口的完整边界，并检查截图是否正确。

## 功能

- 按窗口标题、进程名或窗口句柄定位目标窗口
- 自动恢复并激活目标窗口
- 优先使用 DWM extended frame bounds，减少边框和 DPI 偏差
- 输出 PNG，并支持截图前后验证流程
- 不依赖任何特定用户目录或盘符

## 目录结构

```text
window-screenshot/
├── SKILL.md
├── agents/
│   └── openai.yaml
└── scripts/
    └── capture_window.py
```

## 要求

- Python 3.9+
- Pillow

## 安装

### 1. 安装 Python 依赖

在 PowerShell 中执行：

```powershell
python -m pip install --upgrade pillow
```

### 2. 安装 skill

将 `window-screenshot` 整个目录复制到 Codex 的 skills 目录。常见位置是：

```text
<CODEX_HOME>\skills\window-screenshot
```

其中 `<CODEX_HOME>` 由你的 Codex 安装决定
重启 Codex Desktop，或重新加载 skills，使 `$window-screenshot` 生效。

### 一句话安装

在codex对话框中发送：
```text
请从 https://github.com/chenxiaocai8888/Fang-lab 仓库安装 `window-screenshot` skill，将其复制到当前 Codex 的 skills 目录，安装 Pillow 依赖，并验证 `$window-screenshot` 可以正常调用。
```

## 使用方式

在 Codex 中直接提出截图请求即可
