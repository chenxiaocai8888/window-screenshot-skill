#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ctypes
import json
import sys
import time
from ctypes import wintypes
from pathlib import Path

try:
    from PIL import ImageGrab
except ImportError as exc:
    raise SystemExit("Pillow is required for ImageGrab. Install with: python -m pip install pillow") from exc


if sys.platform != "win32":
    raise SystemExit("capture_window.py only supports Windows.")


user32 = ctypes.windll.user32
dwmapi = ctypes.windll.dwmapi
kernel32 = ctypes.windll.kernel32

DWMWA_EXTENDED_FRAME_BOUNDS = 9
SW_RESTORE = 9
HWND_TOPMOST = -1
HWND_NOTOPMOST = -2
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_SHOWWINDOW = 0x0040


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]


class WINDOWINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcWindow", RECT),
        ("rcClient", RECT),
        ("dwStyle", wintypes.DWORD),
        ("dwExStyle", wintypes.DWORD),
        ("dwWindowStatus", wintypes.DWORD),
        ("cxWindowBorders", wintypes.UINT),
        ("cyWindowBorders", wintypes.UINT),
        ("atomWindowType", wintypes.ATOM),
        ("wCreatorVersion", wintypes.WORD),
    ]


def enable_dpi_awareness() -> None:
    try:
        user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
        return
    except Exception:
        pass
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
        return
    except Exception:
        pass
    try:
        user32.SetProcessDPIAware()
    except Exception:
        pass


def get_window_text(hwnd: int) -> str:
    length = user32.GetWindowTextLengthW(hwnd)
    if length <= 0:
        return ""
    buf = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buf, length + 1)
    return buf.value


def get_process_name(pid: int) -> str:
    try:
        import subprocess

        cmd = [
            "powershell",
            "-NoProfile",
            "-Command",
            f"(Get-Process -Id {pid} -ErrorAction SilentlyContinue).ProcessName",
        ]
        out = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL, timeout=2).strip()
        return f"{out}.exe" if out and not out.lower().endswith(".exe") else out
    except Exception:
        return ""


def rect_to_tuple(rect: RECT) -> tuple[int, int, int, int]:
    return (int(rect.left), int(rect.top), int(rect.right), int(rect.bottom))


def get_frame_rect(hwnd: int) -> tuple[int, int, int, int]:
    rect = RECT()
    hr = dwmapi.DwmGetWindowAttribute(
        wintypes.HWND(hwnd),
        wintypes.DWORD(DWMWA_EXTENDED_FRAME_BOUNDS),
        ctypes.byref(rect),
        ctypes.sizeof(rect),
    )
    if hr == 0 and rect.right > rect.left and rect.bottom > rect.top:
        return rect_to_tuple(rect)
    if not user32.GetWindowRect(wintypes.HWND(hwnd), ctypes.byref(rect)):
        raise OSError(f"GetWindowRect failed for hwnd={hwnd}")
    return rect_to_tuple(rect)


def is_real_window(hwnd: int) -> bool:
    if not user32.IsWindowVisible(wintypes.HWND(hwnd)):
        return False
    title = get_window_text(hwnd).strip()
    if not title:
        return False
    left, top, right, bottom = get_frame_rect(hwnd)
    if right - left < 80 or bottom - top < 60:
        return False
    return True


def enum_windows() -> list[dict]:
    windows: list[dict] = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def callback(hwnd: int, _lparam: int) -> bool:
        try:
            if is_real_window(hwnd):
                pid = wintypes.DWORD()
                user32.GetWindowThreadProcessId(wintypes.HWND(hwnd), ctypes.byref(pid))
                left, top, right, bottom = get_frame_rect(hwnd)
                windows.append(
                    {
                        "hwnd": int(hwnd),
                        "title": get_window_text(hwnd),
                        "pid": int(pid.value),
                        "process": get_process_name(int(pid.value)),
                        "rect": [left, top, right, bottom],
                        "width": right - left,
                        "height": bottom - top,
                    }
                )
        except Exception:
            pass
        return True

    user32.EnumWindows(callback, 0)
    windows.sort(key=lambda w: (w["process"].lower(), w["title"].lower(), -w["width"] * w["height"]))
    return windows


def find_window(args: argparse.Namespace, windows: list[dict]) -> dict:
    matches = windows
    if args.hwnd is not None:
        matches = [w for w in matches if w["hwnd"] == args.hwnd]
    if args.title:
        needle = args.title.casefold()
        if args.exact:
            matches = [w for w in matches if w["title"].casefold() == needle]
        else:
            matches = [w for w in matches if needle in w["title"].casefold()]
    if args.process:
        proc = args.process.casefold()
        matches = [w for w in matches if proc in w["process"].casefold()]
    matches.sort(key=lambda w: w["width"] * w["height"], reverse=True)
    if not matches:
        raise SystemExit("No matching window found. Run with --list to inspect candidates.")
    if args.index < 0 or args.index >= len(matches):
        raise SystemExit(f"--index {args.index} out of range for {len(matches)} matches.")
    return matches[args.index]


def activate_window(hwnd: int, topmost: bool = True) -> None:
    user32.ShowWindow(wintypes.HWND(hwnd), SW_RESTORE)
    user32.BringWindowToTop(wintypes.HWND(hwnd))
    user32.SetForegroundWindow(wintypes.HWND(hwnd))
    if topmost:
        user32.SetWindowPos(wintypes.HWND(hwnd), HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW)
        time.sleep(0.15)
        user32.SetWindowPos(wintypes.HWND(hwnd), HWND_NOTOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW)
    time.sleep(0.35)


def capture(window: dict, out_path: Path, padding: int, activate: bool, topmost: bool) -> dict:
    hwnd = window["hwnd"]
    if activate:
        activate_window(hwnd, topmost=topmost)
    left, top, right, bottom = get_frame_rect(hwnd)
    if padding:
        left -= padding
        top -= padding
        right += padding
        bottom += padding
    image = ImageGrab.grab(bbox=(left, top, right, bottom), all_screens=True)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(out_path)
    result = dict(window)
    result["captured_rect"] = [left, top, right, bottom]
    result["output"] = str(out_path)
    result["image_size"] = list(image.size)
    return result


def main() -> int:
    enable_dpi_awareness()
    parser = argparse.ArgumentParser(description="Capture an exact Windows top-level window screenshot.")
    parser.add_argument("--list", action="store_true", help="List visible windows as JSON.")
    parser.add_argument("--title", help="Window title substring to match.")
    parser.add_argument("--exact", action="store_true", help="Require exact title match.")
    parser.add_argument("--process", help="Process name substring, e.g. python.exe.")
    parser.add_argument("--hwnd", type=int, help="Window handle from --list.")
    parser.add_argument("--index", type=int, default=0, help="Matched candidate index after sorting by area.")
    parser.add_argument("--out", help="Output PNG path.")
    parser.add_argument("--padding", type=int, default=0, help="Extra pixels around detected frame.")
    parser.add_argument("--no-activate", action="store_true", help="Do not restore/foreground the target window.")
    parser.add_argument("--no-topmost", action="store_true", help="Do not temporarily set target window topmost.")
    args = parser.parse_args()

    windows = enum_windows()
    if args.list:
        print(json.dumps(windows, ensure_ascii=False, indent=2))
        return 0
    if not args.out:
        parser.error("--out is required unless --list is used")
    target = find_window(args, windows)
    result = capture(
        target,
        Path(args.out),
        padding=args.padding,
        activate=not args.no_activate,
        topmost=not args.no_topmost,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
