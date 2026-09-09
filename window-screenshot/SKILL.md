---
name: window-screenshot
description: Use whenever the user needs a screenshot on Windows, including full-screen, region, app/window, report evidence, UI QA, debugging, or program-running screenshots. For target app/window screenshots, first identify the window position and size, bring the target window to the front, capture exactly the window bounds, and verify the saved image.
---

# Window Screenshot

Use this skill for any Windows screenshot request. If the request is for a specific app or program window, the required discipline is: identify the window first, activate it, capture exactly its current window rectangle, then visually verify the saved image.

## Decision Rules

- For a target app/window screenshot, always use the window-identification workflow below.
- For a full-screen screenshot, capture the current screen state and verify that it contains exactly what the user asked for.
- For a user-specified pixel region, use the provided coordinates, then verify the crop.
- When the user asks for a program-running/report screenshot but does not name the window clearly, enumerate visible windows first and pick the matching app by title/process/size.
- When the screenshot will be used as formal evidence, prefer the exact target-window workflow over full-screen capture.

## Core Rules

- Do not use a fixed screen region unless the user explicitly gives pixel coordinates.
- Do not reuse an old screenshot. Capture a fresh image after every requested UI/state change.
- Do not include unrelated windows, desktop background, taskbar, or large empty area around the app.
- Do not crop by guessing. Use the target window handle and rectangle.
- After capture, inspect the image before reporting success. If the wrong window, partial window, or outside content appears, recapture.

## Workflow

### Resolve bundled script paths

`<SKILL_ROOT>` means the directory that contains this `SKILL.md`. Resolve it from
the skill's installed location at runtime; never assume a particular user's
home directory, drive letter, or checkout path. `<OUTPUT_PATH>` means a
user-approved writable path for the resulting image (for example,
`<WORKSPACE>\artifacts\window.png`). Replace both placeholders with concrete
paths before running a command.

1. Enumerate candidate windows:
   - Use `<SKILL_ROOT>\scripts\capture_window.py --list` to get visible top-level windows with handle, title, pid, process name, and rectangle.
   - Match by title/process/pid. If there are multiple plausible windows, prefer the one whose title/process and size match the requested program.

2. Confirm the target rectangle:
   - Record the target `hwnd`, title, process, and `left, top, right, bottom`.
   - If the window is minimized, restore it before capture.

3. Bring the target window to the front:
   - Activate and temporarily topmost the target window so it is not covered by other windows.
   - Wait briefly for the UI to repaint before capture.

4. Capture exactly the target window bounds:
   - Use `<SKILL_ROOT>\scripts\capture_window.py --title "<substring>" --out "<OUTPUT_PATH>"` or `--hwnd <handle>`.
   - Prefer the DWM extended frame bounds when available, because they match the visible Windows app frame better than raw legacy bounds.

5. Verify the result:
   - Open the saved image with `view_image`.
   - Check that the full program window is visible, including title bar, borders, and bottom/right edges.
   - Check that no other windows or large external whitespace are included.
   - If the screenshot is wrong, repeat from enumeration instead of adjusting blindly.

## Script Usage

List visible windows:

```powershell
python "<SKILL_ROOT>\scripts\capture_window.py" --list
```

Capture by title substring:

```powershell
python "<SKILL_ROOT>\scripts\capture_window.py" --title "SecureFileSync 客户端" --out "<OUTPUT_PATH>"
```

Capture by exact handle from the list output:

```powershell
python "<SKILL_ROOT>\scripts\capture_window.py" --hwnd 123456 --out "<OUTPUT_PATH>"
```

Example placeholder mapping (illustrative only):

```text
<SKILL_ROOT>   = the installed window-screenshot skill directory
<OUTPUT_PATH>  = a writable path selected for this task
```

If the runtime exposes the skill directory through a variable or metadata,
use that value. Otherwise locate the directory containing `SKILL.md` and use
its `scripts` subdirectory. Do not copy a developer's absolute path into a
generated command, report, or repository documentation.

Useful options:

- `--process python.exe`: narrow candidates by process name.
- `--exact`: require exact title match instead of substring match.
- `--index N`: choose the Nth matched candidate after sorting by area.
- `--padding N`: include N pixels around the detected frame only when the visible border is being clipped.
- `--no-activate`: capture without bringing the window forward only when activation would alter the state being documented.

## Failure Handling

- If `--list` cannot find the target, ask the user to open the app or provide the visible title/process name.
- If activation fails, retry once with `--no-topmost` only if the target is already unobstructed.
- If the image is blank or shows the wrong app, do not claim success; list windows again and recapture by `--hwnd`.
- If there are DPI or multi-monitor issues, use the script output rectangle and saved image dimensions to diagnose before recapturing.
