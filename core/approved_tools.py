import json
from pathlib import Path
from typing import Callable


APPROVED_TOOLS_PATH = Path.home() / ".rectury" / "approved_tools.json"


def workspace_key(workspace):
    return str(Path(workspace).expanduser().resolve())


def load_approved_tools():
    if not APPROVED_TOOLS_PATH.exists():
        return {}

    try:
        with APPROVED_TOOLS_PATH.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError):
        return {}

    return data if isinstance(data, dict) else {}


def save_approved_tools(data):
    APPROVED_TOOLS_PATH.parent.mkdir(parents=True, exist_ok=True)

    with APPROVED_TOOLS_PATH.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False, sort_keys=True)


class ProjectConfig:
    def __init__(self, allowed_tools: list = None):
        self.allowed_tools = allowed_tools or []


class ProjectConfigHandler:
    def __init__(self, get_config: Callable = None, save_config: Callable = None):
        self.get_current_project_config = get_config or self._default_get_config
        self.save_current_project_config = save_config or self._default_save_config
        self._config = ProjectConfig()

    def _default_get_config(self):
        return self._config

    def _default_save_config(self, config):
        self._config = config


DEFAULT_CONFIG_HANDLER = ProjectConfigHandler()


def handle_list_approved_tools(
    cwd: str,
    project_config_handler: ProjectConfigHandler = None
) -> str:
    handler = project_config_handler or DEFAULT_CONFIG_HANDLER
    project_config = handler.get_current_project_config()
    tools_list = "\n".join(project_config.allowed_tools) if project_config.allowed_tools else ""
    return f"Allowed tools for {cwd}:\n{tools_list}"


def handle_add_approved_tool(
    tool: str,
    project_config_handler: ProjectConfigHandler = None
) -> dict:
    handler = project_config_handler or DEFAULT_CONFIG_HANDLER
    project_config = handler.get_current_project_config()

    if tool in project_config.allowed_tools:
        return {
            "success": False,
            "message": f"{tool} is already in the list of approved tools"
        }

    project_config.allowed_tools.append(tool)
    handler.save_current_project_config(project_config)
    return {
        "success": True,
        "message": f"Added {tool} to the list of approved tools"
    }


def handle_remove_approved_tool(
    tool: str,
    project_config_handler: ProjectConfigHandler = None
) -> dict:
    handler = project_config_handler or DEFAULT_CONFIG_HANDLER
    project_config = handler.get_current_project_config()
    original_count = len(project_config.allowed_tools)
    updated_tools = [t for t in project_config.allowed_tools if t != tool]

    if len(updated_tools) != original_count:
        project_config.allowed_tools = updated_tools
        handler.save_current_project_config(project_config)
        return {
            "success": True,
            "message": f"Removed {tool} from the list of approved tools"
        }
    else:
        return {
            "success": False,
            "message": f"{tool} was not in the list of approved tools"
        }