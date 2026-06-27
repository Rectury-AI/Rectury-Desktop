import json
from dataclasses import dataclass

from core.command_approvals import is_command_approved
from core.command_security import validate_command


PERMISSION_TOOLS = {
    "change_workspace",
    "delete_file",
    "edit_file",
    "edit_notebook",
    "insert_notebook_cell",
    "delete_notebook_cell",
    "memory_write",
    "mcp_call_tool",
    "mcp_list_tools",
    "multi_edit",
    "write_file",
    "run_command",
    "undo_last_change",
}

MUTATING_TOOLS = PERMISSION_TOOLS

RUN_TOOL_PERMISSION_TOOLS = PERMISSION_TOOLS - {
    "run_command",
    "undo_last_change",
}

AUTO_APPROVED_TOOLS = {
    "delete_file",
    "edit_file",
    "edit_notebook",
    "insert_notebook_cell",
    "delete_notebook_cell",
    "memory_write",
    "multi_edit",
    "write_file",
}

SESSION_FILE_WRITE_TOOLS = {"edit_file", "write_file"}

REJECTED_PREVIEW_KEYS = {
    "file_path",
    "created",
    "diff",
    "diff_lines",
    "snippet",
    "additions",
    "removals",
}


@dataclass(frozen=True)
class ToolPermissionDecision:
    action: str
    reason: str
    permission_key: str | None = None
    code: str | None = None

    @property
    def allowed(self):
        return self.action == "allow"

    @property
    def denied(self):
        return self.action == "deny"

    @property
    def needs_prompt(self):
        return self.action == "ask"


def permission_key(tool_name, arguments, preview=None):
    preview = preview or {}

    if tool_name in SESSION_FILE_WRITE_TOOLS:
        return "file_write:workspace"

    if tool_name == "run_command":
        prefix = preview.get("prefix") or arguments.get("command", "")
        return f"run_command:{prefix}"

    if tool_name == "change_workspace":
        return f"change_workspace:{arguments.get('new_path', '')}"

    return f"{tool_name}:{json.dumps(arguments, sort_keys=True)}"


def tool_needs_permission(tool_name, arguments, preview=None):
    if tool_name not in PERMISSION_TOOLS:
        return False

    if tool_name == "run_command":
        preview = preview or {}
        if "safe" in preview:
            return not bool(preview.get("safe"))

        validation = validate_command(arguments.get("command", ""))
        return not validation.get("safe", False)

    return True


def can_use_tool(
    tool_name,
    arguments,
    preview=None,
    permission_mode="ask",
    approved_permission_keys=None,
    allow_edits_for_session=False,
    workspace=None,
):
    key = permission_key(tool_name, arguments, preview)
    approved_permission_keys = approved_permission_keys or set()

    if permission_mode == "plan" and tool_name in MUTATING_TOOLS:
        return ToolPermissionDecision(
            action="deny",
            reason="plan_mode",
            permission_key=key,
            code="plan_mode_blocks_tool",
        )

    if not tool_needs_permission(tool_name, arguments, preview):
        return ToolPermissionDecision(
            action="allow",
            reason="no_permission_needed",
            permission_key=key,
        )

    if permission_mode == "danger":
        return ToolPermissionDecision(
            action="allow",
            reason="danger_mode",
            permission_key=key,
        )

    if permission_mode == "auto" and tool_name in AUTO_APPROVED_TOOLS:
        return ToolPermissionDecision(
            action="allow",
            reason="auto_mode",
            permission_key=key,
        )

    if key in approved_permission_keys:
        return ToolPermissionDecision(
            action="allow",
            reason="session_approval",
            permission_key=key,
        )

    if (
        tool_name == "run_command"
        and workspace is not None
        and is_command_approved(workspace, key)
    ):
        return ToolPermissionDecision(
            action="allow",
            reason="project_approval",
            permission_key=key,
        )

    if tool_name in SESSION_FILE_WRITE_TOOLS and allow_edits_for_session:
        return ToolPermissionDecision(
            action="allow",
            reason="file_session_approval",
            permission_key=key,
        )

    return ToolPermissionDecision(
        action="ask",
        reason="requires_user_approval",
        permission_key=key,
    )


def denied_tool_result(tool_name, decision):
    if decision.code == "plan_mode_blocks_tool":
        return {
            "error": (
                "Permission mode is plan. Mutating tools are disabled; "
                "explain the plan instead."
            ),
            "code": "plan_mode_blocks_tool",
            "tool": tool_name,
        }

    return {
        "error": f"The {tool_name} request is not allowed.",
        "code": decision.code or "permission_denied",
        "tool": tool_name,
    }


def rejected_tool_result(tool_name, preview=None):
    preview = preview or {}
    return {
        "error": f"The user rejected the {tool_name} request.",
        "code": "permission_denied",
        "rejected": True,
        "tool": tool_name,
        **{
            key: value
            for key, value in preview.items()
            if key in REJECTED_PREVIEW_KEYS
        },
    }
