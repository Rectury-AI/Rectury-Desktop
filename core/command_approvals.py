import json
from pathlib import Path


APPROVALS_PATH = Path.home() / ".rectury" / "approved_commands.json"


def workspace_key(workspace):
    return str(Path(workspace).expanduser().resolve())


def load_approved_commands():
    if not APPROVALS_PATH.exists():
        return {}

    try:
        with APPROVALS_PATH.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError):
        return {}

    return data if isinstance(data, dict) else {}


def save_approved_commands(data):
    APPROVALS_PATH.parent.mkdir(parents=True, exist_ok=True)

    with APPROVALS_PATH.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False, sort_keys=True)


def approved_command_keys(workspace):
    data = load_approved_commands()
    keys = data.get(workspace_key(workspace), [])
    return set(keys if isinstance(keys, list) else [])


def is_command_approved(workspace, key):
    return key in approved_command_keys(workspace)


def approve_command(workspace, key):
    data = load_approved_commands()
    project_key = workspace_key(workspace)
    keys = set(data.get(project_key, []))
    keys.add(key)
    data[project_key] = sorted(keys)
    save_approved_commands(data)
