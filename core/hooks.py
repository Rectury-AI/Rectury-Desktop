import json
import shlex
import shutil
from fnmatch import fnmatch
from pathlib import Path

from core.command_security import validate_command
from core.workspace import resolve_workspace_path
from tools.functions.run_command import run_command


HOOK_EVENTS = {
    "before_edit",
    "after_edit",
    "before_command",
    "after_command",
    "task_complete",
}

DEFAULT_HOOK_CONFIG = {
    "hooks": {
        "before_edit": [],
        "after_edit": [
            {
                "name": "ruff check changed Python file",
                "enabled": True,
                "glob": "*.py",
                "if_command_exists": "ruff",
                "command": "ruff check {file}",
                "timeout": 30,
            }
        ],
        "before_command": [],
        "after_command": [],
        "task_complete": [
            {
                "name": "project tests example",
                "enabled": False,
                "if_command_exists": "pytest",
                "command": "pytest",
                "timeout": 60,
            }
        ],
    }
}


def hook_config_path(workspace):
    return Path(workspace) / ".rectury" / "hooks.json"


def create_default_hook_config(workspace):
    path = hook_config_path(workspace)
    path.parent.mkdir(parents=True, exist_ok=True)

    if not path.exists():
        path.write_text(
            json.dumps(DEFAULT_HOOK_CONFIG, indent=2) + "\n",
            encoding="utf-8",
        )

    return path


def load_hook_config(workspace):
    path = hook_config_path(workspace)

    if not path.exists():
        return {"hooks": {}}

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return {
            "hooks": {},
            "error": f"Could not load hooks config: {error}",
        }

    if not isinstance(data, dict):
        return {"hooks": {}, "error": "Hooks config must be a JSON object."}

    hooks = data.get("hooks", {})

    if not isinstance(hooks, dict):
        return {"hooks": {}, "error": "hooks must be an object."}

    return {"hooks": hooks}


def quote_value(value):
    return shlex.quote(str(value or ""))


def format_hook_command(command, context):
    replacements = {
        "event": quote_value(context.get("event", "")),
        "file": quote_value(context.get("file", "")),
        "tool": quote_value(context.get("tool", "")),
        "command": quote_value(context.get("command", "")),
        "exit_code": quote_value(context.get("exit_code", "")),
    }

    formatted = str(command or "")

    for key, value in replacements.items():
        formatted = formatted.replace("{" + key + "}", value)

    return formatted


def hook_matches(hook, context):
    if not hook.get("enabled", True):
        return False

    required_command = hook.get("if_command_exists")

    if required_command and shutil.which(str(required_command)) is None:
        return False

    glob = hook.get("glob")

    if glob:
        file_path = context.get("file", "")

        if not file_path:
            return False

        return fnmatch(Path(file_path).name, glob) or fnmatch(file_path, glob)

    return True


def run_hooks(state, event, context=None, permission_mode="ask"):
    context = dict(context or {})
    context["event"] = event

    if event not in HOOK_EVENTS:
        return []

    config = load_hook_config(state.workspace)
    hooks = config.get("hooks", {}).get(event, [])

    if not isinstance(hooks, list):
        return [
            {
                "name": event,
                "event": event,
                "error": f"hooks.{event} must be a list.",
            }
        ]

    results = []

    if config.get("error"):
        results.append(
            {
                "name": "load hooks",
                "event": event,
                "error": config["error"],
            }
        )

    for hook in hooks:
        if not isinstance(hook, dict):
            results.append(
                {
                    "name": "invalid hook",
                    "event": event,
                    "error": "Hook entries must be objects.",
                }
            )
            continue

        if not hook_matches(hook, context):
            continue

        command = format_hook_command(hook.get("command", ""), context)
        name = str(hook.get("name") or command or event)

        validation = validate_command(command)

        if not validation.get("ok"):
            results.append(
                {
                    "name": name,
                    "event": event,
                    "command": command,
                    "error": validation.get("error"),
                    "code": validation.get("code", "invalid_command"),
                }
            )
            continue

        if not validation.get("safe") and permission_mode != "danger":
            results.append(
                {
                    "name": name,
                    "event": event,
                    "command": command,
                    "error": (
                        "Hook command is not marked safe. Enable danger mode "
                        "or use a safer hook command."
                    ),
                    "code": "unsafe_hook_command",
                }
            )
            continue

        cwd = hook.get("cwd", ".")

        try:
            resolve_workspace_path(state.workspace, cwd)
        except ValueError as error:
            results.append(
                {
                    "name": name,
                    "event": event,
                    "command": command,
                    "error": str(error),
                    "code": "invalid_cwd",
                }
            )
            continue

        result = run_command(
            command,
            state,
            cwd=cwd,
            timeout=int(hook.get("timeout", 30) or 30),
        )
        results.append(
            {
                "name": name,
                "event": event,
                "command": command,
                "result": result,
                "success": not result.get("error")
                and result.get("returncode", 0) == 0,
            }
        )

    return results
