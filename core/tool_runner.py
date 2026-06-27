from tools.registry import TOOLS_REGISTRY
from core.tool_permissions import RUN_TOOL_PERMISSION_TOOLS
from core.approved_tools import handle_list_approved_tools, handle_add_approved_tool, handle_remove_approved_tool


def run_tool(tool_name, arguments, state, permission_handler=None):
    tool = TOOLS_REGISTRY.get(tool_name)

    if tool is None:
        raise ValueError(f"Tool '{tool_name}' not found in the registry.")

    # Check if tool is in approved list (auto-approve if approved)
    workspace = state.get("workspace", "") if isinstance(state, dict) else getattr(state, "workspace", "")
    project_config = handle_list_approved_tools(workspace)

    # Tools that require explicit user approval (unless pre-approved)
    requires_approval = tool_name in RUN_TOOL_PERMISSION_TOOLS

    # Auto-approve if tool is in approved list
    if requires_approval and tool_name in project_config:
        pass  # Tool is pre-approved, skip permission check
    elif requires_approval:
        if permission_handler is not None:
            preview = {"tool": tool_name, "arguments": arguments}
            approved = permission_handler(tool_name, arguments, preview)
            if not approved:
                return {"rejected": True, "tool": tool_name}

    return tool(state=state, **arguments)
