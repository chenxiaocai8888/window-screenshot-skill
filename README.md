# Fang-lab

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

## 系统要求

- Windows 10 或更高版本
- Python 3.9+
- Pillow
- Codex Desktop（使用 skill 时需要）

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

其中 `<CODEX_HOME>` 由你的 Codex 安装决定，不要照抄其他电脑的用户目录。安装后应确认以下文件存在：

```text
<CODEX_HOME>\skills\window-screenshot\SKILL.md
<CODEX_HOME>\skills\window-screenshot\scripts\capture_window.py
```

重启 Codex Desktop，或重新加载 skills，使 `$window-screenshot` 生效。

## 使用方式

在 Codex 中直接提出截图请求，例如：

```text
请使用 $window-screenshot 截取记事本窗口，并验证截图只包含该窗口。
```

也可以直接运行脚本。以下命令中的 `<SKILL_ROOT>` 代表本 skill 的安装目录，`<OUTPUT_PATH>` 代表你选择的可写输出路径：

列出可见窗口：

```powershell
python "<SKILL_ROOT>\scripts\capture_window.py" --list
```

按标题截取窗口：

```powershell
python "<SKILL_ROOT>\scripts\capture_window.py" `
  --title "记事本" `
  --out "<OUTPUT_PATH>\notepad.png"
```

按句柄截取窗口：

```powershell
python "<SKILL_ROOT>\scripts\capture_window.py" `
  --hwnd 123456 `
  --out "<OUTPUT_PATH>\window.png"
```

## 参数

| 参数 | 说明 |
| --- | --- |
| `--list` | 以 JSON 列出可见顶层窗口 |
| `--title TEXT` | 按标题子串匹配窗口 |
| `--exact` | 要求标题完全匹配 |
| `--process TEXT` | 按进程名子串筛选，例如 `python.exe` |
| `--hwnd NUMBER` | 使用 `--list` 输出的窗口句柄 |
| `--index N` | 多个匹配结果时选择排序后的第 N 个 |
| `--out PATH` | 输出 PNG 路径 |
| `--padding N` | 在窗口边界外额外增加 N 像素 |
| `--no-activate` | 不恢复或激活目标窗口 |
| `--no-topmost` | 不临时置顶目标窗口 |

`--title`、`--process`、`--hwnd` 至少需要提供一个定位条件；执行截图时需要提供 `--out`。

## 故障排查

- **找不到窗口**：先运行 `--list`，确认窗口已打开，并使用输出中的标题、进程名或句柄。
- **Pillow 缺失**：运行 `python -m pip install pillow`。
- **非 Windows 系统**：脚本依赖 Windows User32/DWM API，不支持 macOS 或 Linux。
- **截图被遮挡或内容错误**：去掉 `--no-activate` 和 `--no-topmost`，按句柄重新捕获。
- **DPI 或多显示器异常**：对照 `--list` 输出的窗口矩形和生成 PNG 的尺寸，再决定是否使用 `--padding`。

## 安全与隐私

截图可能包含密码、令牌、个人信息或其他敏感内容。请在保存、上传或分享前检查 PNG 内容，并将输出路径指向受信任的目录。不要把截图中的敏感信息提交到公开仓库。

## 许可证

当前仓库未声明特定开源许可证。如需公开分发，请补充合适的 LICENSE 文件。
