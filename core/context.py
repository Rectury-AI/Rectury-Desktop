import subprocess
import json
from pathlib import Path


MAX_README_CHARS = 6000
MAX_PROJECT_INSTRUCTIONS_CHARS = 12000
MAX_DIRECTORY_LINES = 160
MAX_GIT_STATUS_LINES = 120
MAX_INDEX_FILES = 20

PROJECT_INSTRUCTION_FILES = [
    "RECTURY.md",
    ".rectury.md",
    "AGENTS.md",
    ".cursorrules",
    ".github/copilot-instructions.md",
]

IGNORED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "node_modules",
    "dist",
    "build",
    ".next",
    ".nuxt",
    "target",
    ".idea",
    ".vscode",
}


def truncate_middle(text, limit):
    if len(text) <= limit:
        return text

    half = max(1, limit // 2)
    omitted = len(text) - half * 2
    return (
        text[:half].rstrip()
        + f"\n\n... {omitted} characters omitted ...\n\n"
        + text[-half:].lstrip()
    )


def run_git(workspace, args, timeout=2):
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except Exception:
        return ""

    if completed.returncode != 0:
        return ""

    return completed.stdout.strip()


def read_optional_file(workspace, names, limit):
    for name in names:
        path = workspace / name

        if not path.exists() or not path.is_file():
            continue

        try:
            return truncate_middle(path.read_text(encoding="utf-8"), limit)
        except (OSError, UnicodeError):
            continue

    return ""


def read_project_instructions(workspace):
    sections = []
    remaining = MAX_PROJECT_INSTRUCTIONS_CHARS

    for name in PROJECT_INSTRUCTION_FILES:
        if remaining <= 0:
            break

        path = workspace / name

        if not path.exists() or not path.is_file():
            continue

        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue

        content = truncate_middle(content, remaining)
        sections.append(f"## {name}\n\n{content}")
        remaining -= len(content)

    return "\n\n".join(sections)


def directory_snapshot(workspace):
    lines = []

    def walk(path, depth=0):
        if len(lines) >= MAX_DIRECTORY_LINES:
            return

        try:
            entries = sorted(
                path.iterdir(),
                key=lambda item: (not item.is_dir(), item.name.lower()),
            )
        except OSError:
            return

        for entry in entries:
            if len(lines) >= MAX_DIRECTORY_LINES:
                break

            if entry.name in IGNORED_DIRS:
                continue

            relative = entry.relative_to(workspace)
            prefix = "  " * depth
            suffix = "/" if entry.is_dir() else ""
            lines.append(f"{prefix}{relative.name}{suffix}")

            if entry.is_dir() and depth < 2:
                walk(entry, depth + 1)

    walk(workspace)

    if len(lines) >= MAX_DIRECTORY_LINES:
        lines.append("... directory snapshot truncated ...")

    return "\n".join(lines)


def git_context(workspace):
    branch = run_git(workspace, ["branch", "--show-current"])
    status = run_git(workspace, ["status", "--short"])
    log = run_git(workspace, ["log", "--oneline", "-n", "5"])

    if not branch and not status and not log:
        return ""

    status_lines = status.splitlines()
    if len(status_lines) > MAX_GIT_STATUS_LINES:
        status = "\n".join(status_lines[:MAX_GIT_STATUS_LINES])
        status += "\n... git status truncated ..."

    return "\n".join(
        part
        for part in [
            f"Branch: {branch}" if branch else "",
            f"Status:\n{status or '(clean)'}",
            f"Recent commits:\n{log}" if log else "",
        ]
        if part
    )


def project_index_context(workspace):
    path = workspace / ".rectury" / "index.json"

    if not path.exists() or not path.is_file():
        return ""

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return ""

    summary = data.get("summary", {})
    important_files = summary.get("important_files", [])[:MAX_INDEX_FILES]

    if not summary and not important_files:
        return ""

    lines = [
        f"Generated: {data.get('generated_at', 'unknown')}",
        f"Files: {summary.get('files', 0)}",
        f"Symbols: {summary.get('symbols', 0)}",
        f"Imports: {summary.get('imports', 0)}",
        f"Languages: {summary.get('languages', {})}",
    ]

    if important_files:
        lines.append("Important files:")
        lines.extend(
            (
                f"- {item.get('path')} "
                f"(score {item.get('importance', 0)}, "
                f"{item.get('symbols', 0)} symbols, "
                f"{item.get('imports', 0)} imports)"
            )
            for item in important_files
        )

    return "\n".join(lines)


def build_context(workspace_value):
    workspace = Path(workspace_value).expanduser().resolve()
    sections = []

    instructions = read_project_instructions(workspace)
    if instructions:
        sections.append(
            "# Project instructions\n\n"
            "These files contain user- or project-authored instructions. "
            "Follow them when they do not conflict with higher-priority safety "
            "rules or the current user request.\n\n"
            + instructions
        )

    readme = read_optional_file(
        workspace,
        ["README.md", "README.mdx", "readme.md"],
        MAX_README_CHARS,
    )
    if readme:
        sections.append("# README snapshot\n\n" + readme)

    snapshot = directory_snapshot(workspace)
    if snapshot:
        sections.append(
            "# Directory snapshot\n\n"
            "This is a startup snapshot. It may become stale during the "
            "conversation.\n\n"
            + snapshot
        )

    git = git_context(workspace)
    if git:
        sections.append(
            "# Git snapshot\n\n"
            "This is a startup snapshot. It may become stale during the "
            "conversation.\n\n"
            + git
        )

    project_index = project_index_context(workspace)
    if project_index:
        sections.append(
            "# Project index snapshot\n\n"
            "This is a compact cached index. Refresh it with index_project "
            "if freshness matters.\n\n"
            + project_index
        )

    return "\n\n".join(sections)
