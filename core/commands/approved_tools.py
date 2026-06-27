from core.approved_tools import (
    handle_list_approved_tools,
    handle_add_approved_tool,
    handle_remove_approved_tool,
    ProjectConfigHandler,
)


def handle_approved_tools_command(args: list, cwd: str, config_handler: ProjectConfigHandler = None) -> str:
    """
    Handle /approved-tools commands
    Usage:
        /approved-tools list
        /approved-tools add <tool_name>
        /approved-tools remove <tool_name>
    """
    if not args or args[0] == "list":
        return handle_list_approved_tools(cwd, config_handler)

    if len(args) < 2:
        return "Usage: /approved-tools [list|add|remove] [tool_name]"

    action = args[0].lower()
    tool = args[1]

    if action == "add":
        result = handle_add_approved_tool(tool, config_handler)
        return result["message"]

    if action == "remove":
        result = handle_remove_approved_tool(tool, config_handler)
        return result["message"]

    return f"Unknown action: {action}. Use: list, add, or remove"