# Keylogger for Learning

A modular keylogger written in Python for **educational and learning purposes**. The
project demonstrates how to capture keystrokes across platforms, log them in a
structured way, enrich them with window context, and optionally deliver them to a remote
endpoint.

> [!WARNING]
> **For authorized use only.** This tool is meant for learning about system and security
> internals on your own devices, or with explicit consent. Secretly recording other
> people's keystrokes is a criminal offense in most jurisdictions. Only run it on
> systems you have permission to use it on.

## Features

- **Cross-platform keystroke capture** via [`pynput`](https://pypi.org/project/pynput/).
- **Window tracking** – logs the title of the active window on Windows, macOS, and Linux
  (see [Platform dependencies](#platform-dependencies)).
- **Structured events** – every keystroke is captured as a `KeyEvent` with timestamp,
  window title, and type (`CHAR`, `SPECIAL`, `UNKNOWN`).
- **Automatic log rotation** – log files are rolled over once a configurable maximum
  size is reached.
- **Special-key mapping** – keys such as `[SPACE]`, `[ENTER]`, `[CTRL]` are rendered in a
  readable form.
- **Optional webhook delivery** – events are batched and sent via HTTP POST to a remote
  endpoint.
- **Toggle key** – pause/resume recording at runtime (default: `F9`).

## Architecture

All code lives in `keylogger.py` and is split into clearly separated components:

| Component          | Responsibility                                                      |
| ------------------ | ------------------------------------------------------------------- |
| `Keylogger`        | Main class; coordinates the listener, log writer, and webhook.      |
| `KeyloggerConfig`  | Dataclass holding all runtime configuration.                        |
| `KeyEvent`         | A single keystroke with timestamp, window title, and type.          |
| `LogManager`       | File writer with size-based rotation and an explicit `close()`.     |
| `WebhookDelivery`  | Batched HTTP delivery; releases the buffer lock before the POST.    |
| `WindowTracker`    | Looks up the active window title across the three platforms.        |
| `KeyType`          | Enum categorizing keystrokes: `CHAR`, `SPECIAL`, `UNKNOWN`.         |
| `SPECIAL_KEYS`     | Mapping of `pynput` keys to their display labels.                   |

## Requirements

- **Python ≥ 3.12**
- [`pynput`](https://pypi.org/project/pynput/) (required)
- [`requests`](https://pypi.org/project/requests/) (optional, only for webhook delivery)

### Platform dependencies

Window tracking needs additional packages depending on the operating system:

- **Windows:** `pywin32` (`win32gui`, `win32process`) and `psutil`
- **macOS:** `pyobjc` (`AppKit` / `NSWorkspace`)
- **Linux:** `xdotool` (installed as a system package)

If these are missing, window tracking disables itself automatically – plain keystroke
capture keeps working.

## Installation

The project uses [`uv`](https://github.com/astral-sh/uv):

```bash
# Clone the repository
git clone <repo-url>
cd keylogger

# Install dependencies
uv sync

# Optional extras as needed
uv add requests          # for webhook delivery
uv add pywin32 psutil    # window tracking on Windows
uv add pyobjc            # window tracking on macOS
```

Alternatively with `pip`:

```bash
pip install pynput requests
```

## Usage

```bash
uv run keylogger.py
```

On startup it prints the log directory, current log file, toggle key, and webhook status:

- **`F9`** – pause/resume recording
- **`CTRL+C`** – exit the program (logs are closed cleanly and any remaining webhook
  events are flushed)

Log files are stored in `~/.keylogger_logs/` by default.

### Log format

Each line follows this pattern:

```
[2026-09-05 13:42:07][Firefox - Example page] H
[2026-09-05 13:42:07][Firefox - Example page] a
[2026-09-05 13:42:08][Firefox - Example page] [SPACE]
```

## Configuration

Behavior is controlled through the `KeyloggerConfig` dataclass. To customize it, adjust
the configuration in `main()`:

```python
from pathlib import Path
from pynput.keyboard import Key
from keylogger import Keylogger, KeyloggerConfig

config = KeyloggerConfig(
    log_dir=Path.home() / ".keylogger_logs",
    log_file_prefix="keylog",
    max_log_size_mb=5.0,
    webhook_url="https://example.com/collect",  # None = disabled
    webhook_batch_size=50,
    toggle_key=Key.f9,
    enable_window_tracking=True,
    log_special_keys=True,
    window_check_interval=0.5,
)

Keylogger(config).start()
```

| Option                   | Default                    | Description                                          |
| ------------------------ | -------------------------- | --------------------------------------------------- |
| `log_dir`                | `~/.keylogger_logs`        | Directory for log files.                             |
| `log_file_prefix`        | `"keylog"`                 | Prefix for log file names.                           |
| `max_log_size_mb`        | `5.0`                      | Max file size before rotation (MB).                  |
| `webhook_url`            | `None`                     | Target URL for HTTP delivery (`None` = off).         |
| `webhook_batch_size`     | `50`                       | Number of events per POST batch.                     |
| `toggle_key`             | `Key.f9`                   | Key to pause/resume.                                 |
| `enable_window_tracking` | `True`                     | Log the active window alongside keystrokes.          |
| `log_special_keys`       | `True`                     | Log special keys (`[ENTER]`, `[CTRL]` …).            |
| `window_check_interval`  | `0.5`                      | Polling interval for the window title (seconds).     |

### Webhook payload

When the webhook is enabled, the following JSON is sent per batch:

```json
{
  "timestamp": "2026-09-05T13:42:07.123456",
  "host": "my-machine",
  "events": [
    {
      "timestamp": "2026-09-05T13:42:07.100000",
      "key": "H",
      "window_title": "Firefox - Example page",
      "key_type": "char"
    }
  ]
}
```

## Permission notes

- On **macOS**, the terminal running the tool must be granted **Accessibility** (and
  possibly **Input Monitoring**) access in System Settings.
- On **Linux**, a running X server and an installed `xdotool` may be required.

## License

Released under the [MIT License](LICENSE) — free to use, modify, and distribute.

This project is intended solely for learning and educational purposes.
