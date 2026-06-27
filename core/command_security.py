import re
import shlex


SAFE_EXACT_COMMANDS = {
    "date",
    "git branch",
    "git diff",
    "git log",
    "git status",
    "ls",
    "pwd",
    "python --version",
    "python3 --version",
    "which python",
    "which python3",
}

SAFE_PREFIXES = (
    "cargo check",
    "cargo test",
    "git status",
    "git diff",
    "git log",
    "git branch",
    "git show",
    "git grep",
    "git ls-files",
    "git rev-parse",
    "go test",
    "npm run lint",
    "npm run test",
    "npm run typecheck",
    "npm test",
    "pnpm lint",
    "pnpm test",
    "pnpm typecheck",
    "python -m compileall",
    "python -m py_compile",
    "python -m pytest",
    "python3 -m compileall",
    "python3 -m py_compile",
    "python3 -m pytest",
    "python -m json.tool",
    "python3 -m json.tool",
    "pytest",
    "ruff check",
    "yarn lint",
    "yarn test",
    "yarn typecheck",
)

SAFE_READ_ONLY_BASE_COMMANDS = {
    "du",
    "file",
    "find",
    "grep",
    "head",
    "ls",
    "rg",
    "stat",
    "tail",
    "tree",
    "wc",
}

UNSAFE_READ_ONLY_TOKENS = {
    "-delete",
    "-exec",
    "-execdir",
    "-i",
    "--in-place",
}

BANNED_BASE_COMMANDS = {
    "chmod",
    "chown",
    "dd",
    "diskutil",
    "kill",
    "killall",
    "mkfs",
    "pkill",
    "reboot",
    "rm",
    "rmdir",
    "shutdown",
    "su",
    "sudo",
}

BANNED_PATTERNS = (
    r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}",
    r"\b(curl|wget)\b[^\n]*(\||>)\s*(sh|bash|zsh|python|python3)\b",
    r"\b(sh|bash|zsh)\s+-c\s+['\"][^'\"]*(rm|mkfs|dd|chmod|chown)\b",
    r"\bpython3?\s+-c\s+['\"][^'\"]*(os\.remove|shutil\.rmtree|unlink|rmdir)\b",
    r">\s*/dev/(disk|rdisk|sda|nvme)",
    r">\s*(~?/)?\.ssh/",
    r">\s*/etc/(sudoers|passwd|shadow|hosts)",
    r"\bmkfs\.",
    r"\brm\s+-[^\n;|&]*[rf]",
)

CONTROL_SPLIT_RE = re.compile(r"\s*(?:&&|\|\||;|\|)\s*")


def normalize_command(command):
    return " ".join(str(command).strip().split())


def command_segments(command):
    return [
        segment.strip()
        for segment in CONTROL_SPLIT_RE.split(str(command))
        if segment.strip()
    ]


def first_word(segment):
    try:
        parts = shlex.split(segment)
    except ValueError:
        parts = segment.split()

    return parts[0] if parts else ""


def is_safe_command(command):
    normalized = normalize_command(command)

    if normalized in SAFE_EXACT_COMMANDS:
        return True

    if any(normalized.startswith(prefix) for prefix in SAFE_PREFIXES):
        return True

    segments = command_segments(command)

    return bool(segments) and all(
        is_safe_read_only_segment(segment)
        for segment in segments
    )


def is_safe_read_only_segment(segment):
    try:
        parts = shlex.split(segment)
    except ValueError:
        parts = segment.split()

    if not parts:
        return False

    base = parts[0].lower()

    if base not in SAFE_READ_ONLY_BASE_COMMANDS:
        return False

    return not any(part in UNSAFE_READ_ONLY_TOKENS for part in parts[1:])


def command_prefix(command):
    segment = command_segments(command)[0] if command_segments(command) else ""
    base = first_word(segment)

    if not base:
        return ""

    try:
        parts = shlex.split(segment)
    except ValueError:
        parts = segment.split()

    return " ".join(parts[:2]) if len(parts) > 1 else base


def validate_command(command):
    if not isinstance(command, str) or not command.strip():
        return {
            "ok": False,
            "safe": False,
            "error": "command must be a non-empty string.",
        }

    return {
        "ok": True,
        "safe": is_safe_command(command),
        "prefix": command_prefix(command),
    }
