"""Visible-browser helpers for accepting Colab's local MCP connect dialog."""

from __future__ import annotations

from dataclasses import dataclass
import json
import shutil
import subprocess
import time


KEY_ENTER = ["28:1", "28:0"]
KEY_TAB = ["15:1", "15:0"]
KEY_CTRL_N = ["29:1", "49:1", "49:0", "29:0"]


@dataclass
class VisibleConnectResult:
    ok: bool
    reason: str
    strategy: str | None = None
    title: str | None = None

    def as_log(self) -> str:
        parts = [f"ok={self.ok}", f"reason={self.reason}"]
        if self.strategy:
            parts.append(f"strategy={self.strategy}")
        if self.title:
            parts.append(f"title={self.title!r}")
        return " ".join(parts)


def helper_available() -> bool:
    return bool(shutil.which("hyprctl") and shutil.which("ydotool"))


def _run(command: list[str], *, timeout: int = 5) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, capture_output=True, timeout=timeout)


def _colab_chrome_window(title_filter: str, *, allow_any_chrome: bool = False) -> dict | None:
    completed = _run(["hyprctl", "clients", "-j"])
    if completed.returncode != 0:
        return None
    try:
        clients = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return None

    title_filter = title_filter.lower()
    chrome_windows = []
    candidates = []
    for client in clients:
        class_name = str(client.get("class") or "").lower()
        title = str(client.get("title") or "")
        title_lower = title.lower()
        if "chrome" not in class_name and "chromium" not in class_name:
            continue
        chrome_windows.append(client)
        score = 0
        if title_filter and title_filter in title_lower:
            score += 50
        if "colab" in title_lower:
            score += 40
        if "scratchpad" in title_lower:
            score += 20
        if score:
            candidates.append((score, client))
    if not candidates:
        return chrome_windows[0] if allow_any_chrome and chrome_windows else None
    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]


def _focus_window(window: dict) -> bool:
    address = window.get("address")
    workspace = (window.get("workspace") or {}).get("name")
    if workspace:
        _run(["hyprctl", "dispatch", "workspace", str(workspace)])
        time.sleep(0.2)
    if not address:
        return False
    completed = _run(["hyprctl", "dispatch", "focuswindow", f"address:{address}"])
    time.sleep(0.2)
    return completed.returncode == 0


def _send_keys(keys: list[str]) -> bool:
    completed = _run(["ydotool", "key", *keys], timeout=10)
    return completed.returncode == 0


def _type_text(text: str) -> bool:
    completed = _run(["ydotool", "type", text], timeout=20)
    return completed.returncode == 0


def visible_connect_attempt(
    *,
    attempt_index: int,
    title_filter: str = "Colab",
    target_url: str | None = None,
) -> VisibleConnectResult:
    if not helper_available():
        return VisibleConnectResult(False, "hyprctl or ydotool unavailable")

    window = _colab_chrome_window(title_filter, allow_any_chrome=bool(target_url))
    if not window:
        return VisibleConnectResult(False, "no visible Chrome Colab window")
    title = str(window.get("title") or "")
    if not _focus_window(window):
        return VisibleConnectResult(False, "could not focus Chrome Colab window", title=title)

    if target_url and attempt_index == 0:
        if not _send_keys(KEY_CTRL_N):
            return VisibleConnectResult(False, "could not open new Chrome window", strategy="new-window-url-enter", title=title)
        time.sleep(0.5)
        if not _type_text(target_url):
            return VisibleConnectResult(False, "could not type scratch URL", strategy="new-window-url-enter", title=title)
        if not _send_keys(KEY_ENTER):
            return VisibleConnectResult(False, "could not submit scratch URL", strategy="new-window-url-enter", title=title)
        time.sleep(5)
        if not _send_keys(KEY_ENTER):
            return VisibleConnectResult(False, "could not send Connect default key", strategy="new-window-url-enter", title=title)
        return VisibleConnectResult(True, "opened scratch URL and sent connect key", strategy="new-window-url-enter", title=title)

    strategies = [
        ("enter", KEY_ENTER),
        ("enter", KEY_ENTER),
        ("tab-enter", [*KEY_TAB, *KEY_ENTER]),
        ("tab-tab-enter", [*KEY_TAB, *KEY_TAB, *KEY_ENTER]),
    ]
    strategy, keys = strategies[min(max(attempt_index, 0), len(strategies) - 1)]
    if not _send_keys(keys):
        return VisibleConnectResult(False, "ydotool key sequence failed", strategy=strategy, title=title)
    return VisibleConnectResult(True, "sent connect key sequence", strategy=strategy, title=title)
