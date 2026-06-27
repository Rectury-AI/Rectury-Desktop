from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TerminalTheme:
    assistant: str = "#D97757"
    command: str = "#fd5db1"
    permission: str = "#b1b9f9"
    text: str = "#ffffff"
    secondary_text: str = "#999999"
    secondary_border: str = "#888888"
    success: str = "#4eba65"
    error: str = "#ff6b80"
    warning: str = "#ffc107"
    suggestion: str = "#b1b9f9"
    diff_added: str = "#225c2b"
    diff_removed: str = "#7a2936"
    diff_added_dimmed: str = "#47584a"
    diff_removed_dimmed: str = "#69484d"


THEME = TerminalTheme()


def wrap_text(text, width):
    lines = []
    current = ""

    for character in str(text or ""):
        if len(current) < width:
            current += character
        else:
            lines.append(current)
            current = character

    if current:
        lines.append(current)

    return lines


def format_duration_ms(milliseconds):
    if milliseconds is None:
        return ""

    try:
        milliseconds = float(milliseconds)
    except (TypeError, ValueError):
        return ""

    if milliseconds < 60_000:
        return f"{milliseconds / 1000:.1f}s"

    hours = int(milliseconds // 3_600_000)
    minutes = int((milliseconds % 3_600_000) // 60_000)
    seconds = (milliseconds % 60_000) / 1000

    if hours:
        return f"{hours}h {minutes}m {seconds:.1f}s"

    if minutes:
        return f"{minutes}m {seconds:.1f}s"

    return f"{seconds:.1f}s"


def format_number(value):
    try:
        value = float(value or 0)
    except (TypeError, ValueError):
        return "0"

    sign = "-" if value < 0 else ""
    value = abs(value)

    for suffix, threshold in (("b", 1_000_000_000), ("m", 1_000_000), ("k", 1_000)):
        if value >= threshold:
            return f"{sign}{value / threshold:.1f}{suffix}"

    return f"{sign}{int(value)}"


def format_bytes(value):
    try:
        value = float(value or 0)
    except (TypeError, ValueError):
        return "0 B"

    for suffix in ("B", "KB", "MB", "GB"):
        if value < 1024 or suffix == "GB":
            if suffix == "B":
                return f"{int(value)} {suffix}"
            return f"{value:.1f} {suffix}"
        value /= 1024

    return f"{value:.1f} GB"


def display_path(value, cwd=None):
    if not value:
        return ""

    path = Path(str(value)).expanduser()
    cwd = Path(cwd or Path.cwd()).expanduser()

    try:
        return str(path.resolve().relative_to(cwd.resolve()))
    except (OSError, ValueError):
        pass

    try:
        home = Path.home().resolve()
        resolved = path.resolve()
        if resolved == home or home in resolved.parents:
            return "~/" + str(resolved.relative_to(home))
    except (OSError, ValueError):
        pass

    return str(path)


def truncate_middle(value, limit=120):
    value = str(value or "")

    if len(value) <= limit:
        return value

    keep = max(8, (limit - 1) // 2)
    return f"{value[:keep]}…{value[-keep:]}"


def compact_path(value, limit=120):
    return truncate_middle(display_path(value), limit)
