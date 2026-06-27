import json
import base64
import os
import re
from copy import deepcopy
from pathlib import Path
from datetime import datetime
from time import monotonic
from uuid import uuid4

from core.command_security import validate_command
from core.client import ClientConfig, create_client, model_env_version
from core.commands.approved_tools import handle_approved_tools_command
from core.commands.bug import handle_bug_command
from core.commands.compact import handle_compact_command
from core.commands.cost import handle_cost_command
from core.commands.doctor import handle_doctor_command
from core.commands.init import handle_init_command
from core.commands.listen import handle_listen_command, is_listen_enabled
from core.commands.pr_comments import handle_pr_comments_command
from core.commands.review import handle_review_command
from core.cost_tracker import add_to_total_cost
from core.conversation_store import (
    list_conversations,
    load_conversation,
    save_conversation,
)
from core.context import build_context
from core.prompts import TITLE_PROMPT, create_system_message
from core.session_state import SessionState
from core.tool_permissions import (
    can_use_tool,
    denied_tool_result,
    rejected_tool_result,
)
from core.tool_results import result_for_model
from core.tool_runner import run_tool
from core.thinking import (
    get_max_thinking_tokens,
    is_thinking_parameter_error,
    thinking_request_kwargs,
)
from core.checkpoints import preview_undo_last_change
from core.hooks import run_hooks
from tools.functions.delete_file import preview_delete_file
from tools.functions.edit_file import preview_edit_file
from tools.functions.memory import preview_memory_write
from tools.functions.multi_edit import preview_multi_edit
from tools.functions.notebook import (
    preview_delete_notebook_cell,
    preview_edit_notebook,
    preview_insert_notebook_cell,
)
from tools.functions.run_command import run_command_stream
from tools.functions.write_file import preview_write_file
from tools.catalog import load_response_tools
from tools.compact_compat import normalize_compact_tool_call


MAX_API_MESSAGES_CHARS = 60000
MEMORY_COMPACTION_TRIGGER_CHARS = 45000
MAX_MEMORY_SUMMARY_CHARS = 12000
RECENT_MESSAGES_TO_KEEP = 12
TOKEN_ESTIMATE_DIVISOR = 4
DEFAULT_CONTEXT_WINDOW_TOKENS = 128000
MAX_INVALID_TOOL_RETRIES = 2
MAX_REQUIRED_TOOL_RETRIES = 2
MAX_WORKFLOW_PLANNING_TOOLS = {
    "architect",
    "task",
    "project_overview",
    "index_project",
    "search_project",
    "list_files_in_dir",
    "git_status",
}

ACTION_TOOL_VERBS = {
    "add",
    "anade",
    "analiza",
    "analyze",
    "añade",
    "arregla",
    "build",
    "cambia",
    "change",
    "check",
    "comprueba",
    "configura",
    "configure",
    "corrige",
    "create",
    "crea",
    "delete",
    "deploy",
    "edit",
    "ejecuta",
    "fix",
    "haz",
    "implement",
    "implementa",
    "install",
    "instala",
    "inspect",
    "make",
    "modifica",
    "modify",
    "move",
    "organiza",
    "push",
    "read",
    "refactor",
    "renombra",
    "rename",
    "revisa",
    "run",
    "scrape",
    "setup",
    "test",
    "update",
    "write",
}

ACTION_TOOL_PHRASES = {
    "can create",
    "can you create",
    "could you create",
    "que ves aqui",
    "qué ves aquí",
    "que ves en",
    "qué ves en",
    "new file",
    "new folder",
    "nuevo archivo",
    "nueva carpeta",
    "create a file",
    "create a folder",
    "crear un archivo",
    "crear una carpeta",
    "run command",
    "hazlo",
}

URL_PATTERN = re.compile(r"https?://\S+|(?:[a-z0-9-]+\.)+[a-z]{2,}(?:/\S*)?", re.IGNORECASE)

MAX_WORKFLOW_WORDS = {
    "app",
    "architecture",
    "arquitectura",
    "complete",
    "completo",
    "dashboard",
    "desde",
    "full",
    "landing",
    "migrate",
    "migration",
    "migracion",
    "migración",
    "project",
    "proyecto",
    "refactor",
    "setup",
    "site",
    "website",
}

MAX_WORKFLOW_PHRASES = {
    "desde cero",
    "from scratch",
    "full project",
    "full website",
    "nuevo proyecto",
    "new project",
    "todo completo",
    "proyecto completo",
    "web completa",
    "sitio completo",
}

MODEL_CONTEXT_WINDOWS = {
    "gpt-4.1": 1047576,
    "gpt-4.1-mini": 1047576,
    "gpt-4.1-nano": 1047576,
    "gpt-4o": 128000,
    "gpt-4o-mini": 128000,
}


def current_time():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def estimate_tokens(value):
    if not isinstance(value, str):
        value = json.dumps(value, ensure_ascii=False)

    return max(1, len(value) // TOKEN_ESTIMATE_DIVISOR)


def attachment_to_content(attachment):
    kind = attachment.get("kind")

    if kind == "text":
        content = attachment.get("content", "")

        if not content:
            return None

        line_count = attachment.get("line_count")
        char_count = attachment.get("char_count")
        metadata = []

        if line_count:
            metadata.append(f"{line_count} lines")
        if char_count:
            metadata.append(f"{char_count} characters")

        suffix = f" ({', '.join(metadata)})" if metadata else ""

        return {
            "type": "text",
            "text": f"Pasted text attachment{suffix}:\n\n{content}",
        }

    if kind != "image":
        return None

    data_url = attachment.get("data_url")

    if not data_url:
        file_path = attachment.get("path")

        if not file_path:
            return None

        try:
            raw_bytes = Path(file_path).read_bytes()
        except OSError:
            return None

        mime_type = attachment.get("mime_type") or "image/png"
        encoded = base64.b64encode(raw_bytes).decode("ascii")
        data_url = f"data:{mime_type};base64,{encoded}"

    return {
        "type": "image_url",
        "image_url": {"url": data_url},
    }


def user_message_to_api_content(message):
    content = message.get("content", "")
    attachments = message.get("attachments", []) or []

    if not attachments:
        return content

    parts = []

    if content:
        parts.append({"type": "text", "text": content})

    for attachment in attachments:
        attachment_content = attachment_to_content(attachment)

        if attachment_content is not None:
            parts.append(attachment_content)

    if not parts:
        return content

    if len(parts) == 1:
        return parts[0]

    return parts


def context_window_for_model(model):
    model_key = str(model or "").lower()

    for known_model, context_window in MODEL_CONTEXT_WINDOWS.items():
        if known_model in model_key:
            return context_window

    if "1m" in model_key or "1m" in model_key.replace("_", "-"):
        return 1000000

    return DEFAULT_CONTEXT_WINDOW_TOKENS


def initial_usage_stats(config):
    context_window = context_window_for_model(config.model)
    return {
        "provider": config.provider or "not configured",
        "model": config.model or "not configured",
        "effort_mode": "normal",
        "context_window_tokens": context_window,
        "last_input_tokens": 0,
        "last_output_tokens": 0,
        "last_total_tokens": 0,
        "last_estimated": True,
        "last_duration_ms": 0,
        "last_tokens_per_second": 0.0,
        "last_thinking_tokens": 0,
        "session_input_tokens": 0,
        "session_output_tokens": 0,
        "session_total_tokens": 0,
        "session_requests": 0,
        "context_used_tokens": 0,
        "context_used_percent": 0.0,
        "history_omitted": False,
    }


def create_edit_intro(tool_calls):
    actions = []

    for tool_call in tool_calls:
        function = tool_call.get("function", {})
        tool_name = function.get("name")

        if tool_name not in {
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
            "change_workspace",
        }:
            continue

        try:
            arguments = json.loads(function.get("arguments") or "{}")
        except (TypeError, ValueError):
            arguments = {}

        if tool_name == "edit_file":
            file_path = arguments.get("file_path")
            action = "create" if arguments.get("old_text") == "" else "modify"

            if file_path:
                actions.append(f"{action} `{file_path}`")
            else:
                actions.append(f"{action} the requested file")
        elif tool_name == "delete_file":
            file_path = arguments.get("file_path")
            actions.append(
                f"delete `{file_path}`"
                if file_path
                else "delete a file"
            )
        elif tool_name == "multi_edit":
            file_path = arguments.get("file_path")
            edit_count = len(arguments.get("edits") or [])
            actions.append(
                f"apply {edit_count} edits to `{file_path}`"
                if file_path
                else "apply multiple edits to a file"
            )
        elif tool_name == "memory_write":
            file_path = arguments.get("file_path", "RECTURY.md")
            actions.append(f"update project memory `{file_path}`")
        elif tool_name == "edit_notebook":
            file_path = arguments.get("file_path")
            cell_index = arguments.get("cell_index")
            actions.append(
                f"edit notebook cell {cell_index} in `{file_path}`"
                if file_path
                else "edit a notebook cell"
            )
        elif tool_name == "insert_notebook_cell":
            file_path = arguments.get("file_path")
            cell_index = arguments.get("cell_index")
            actions.append(
                f"insert notebook cell {cell_index} in `{file_path}`"
                if file_path
                else "insert a notebook cell"
            )
        elif tool_name == "delete_notebook_cell":
            file_path = arguments.get("file_path")
            cell_index = arguments.get("cell_index")
            actions.append(
                f"delete notebook cell {cell_index} in `{file_path}`"
                if file_path
                else "delete a notebook cell"
            )
        elif tool_name == "mcp_list_tools":
            actions.append(
                f"start MCP server `{arguments.get('server', '')}` to list tools"
            )
        elif tool_name == "mcp_call_tool":
            actions.append(
                f"call MCP tool `{arguments.get('tool', '')}` on `{arguments.get('server', '')}`"
            )
        elif tool_name == "write_file":
            file_path = arguments.get("file_path")
            actions.append(
                f"write `{file_path}`"
                if file_path
                else "write a file"
            )
        elif tool_name == "run_command":
            command = arguments.get("command", "")
            actions.append(
                f"run `{command}`"
                if command
                else "run a command"
            )
        elif tool_name == "change_workspace":
            new_path = arguments.get("new_path", "")
            actions.append(
                f"change the workspace to `{new_path}`"
                if new_path
                else "change the workspace"
            )

    if not actions:
        return ""

    if len(actions) == 1:
        scope = actions[0]
    else:
        scope = ", ".join(actions[:-1]) + f" and {actions[-1]}"

    return f"I’ll {scope} now."


def create_fallback_conclusion(tool_results):
    successful_edits = []
    failed_tools = []

    for tool_result in tool_results:
        result = tool_result["result"]

        if result.get("error"):
            failed_tools.append(tool_result["name"])
            continue

        if tool_result["name"] in {
            "delete_file",
            "edit_file",
            "edit_notebook",
            "insert_notebook_cell",
            "delete_notebook_cell",
            "memory_write",
            "multi_edit",
            "write_file",
        }:
            file_path = tool_result["arguments"].get(
                "file_path"
            ) or result.get("file_path")

            if file_path and file_path not in successful_edits:
                successful_edits.append(file_path)

    if successful_edits:
        files = "\n".join(
            f"- `{file_path}`"
            for file_path in successful_edits
        )
        conclusion = (
            "The requested change completed successfully.\n\n"
            f"Modified files:\n{files}\n\n"
            "No additional tests or validation checks were run."
        )
    else:
        conclusion = "The requested operation has finished."

    if failed_tools:
        tools = ", ".join(sorted(set(failed_tools)))
        conclusion += (
            "\n\nSome tools returned errors: "
            f"{tools}."
        )

    return conclusion


def redact_secrets(text):
    redacted = str(text)

    for key, value in os.environ.items():
        upper_key = key.upper()

        if not value or len(value) < 8:
            continue

        if any(marker in upper_key for marker in {"API_KEY", "TOKEN", "SECRET"}):
            redacted = redacted.replace(value, "[redacted]")

    return redacted


def format_model_error(error):
    message = redact_secrets(str(error).strip() or error.__class__.__name__)
    return (
        "Request failed before Rectury could finish the response:\n\n"
        f"{message}\n\n"
        "Check the selected model, base URL, API key, and network connection. "
        "You can run `/models` to update the local model configuration."
    )


def normalized_words(text):
    word = []
    words = []

    for character in str(text).lower():
        if character.isalnum() or character in {"_", "-"}:
            word.append(character)
        elif word:
            words.append("".join(word))
            word = []

    if word:
        words.append("".join(word))

    return words


def request_requires_tool_action(text):
    lowered = str(text or "").lower()

    if URL_PATTERN.search(lowered):
        return True

    if any(phrase in lowered for phrase in ACTION_TOOL_PHRASES):
        return True

    words = set(normalized_words(lowered))

    if words.intersection(ACTION_TOOL_VERBS):
        return True

    return False


def request_requires_max_workflow(text):
    lowered = str(text or "").lower()

    if any(phrase in lowered for phrase in MAX_WORKFLOW_PHRASES):
        return True

    words = set(normalized_words(lowered))

    return bool(words.intersection(MAX_WORKFLOW_WORDS))


def required_tool_reminder(retry=False):
    prefix = (
        "Your previous response did not use tools for an actionable workspace "
        "request. "
        if retry
        else ""
    )
    return (
        f"{prefix}"
        "The user's request requires Rectury to act locally. Your next assistant "
        "message must call at least one relevant tool such as run_command, "
        "write_file, edit_file, list_files_in_dir, change_workspace, or "
        "search_project. Continue with tools until the requested work is done, "
        "validated, or genuinely blocked. Do not ask whether to proceed when "
        "the next step is clear, and do not answer with shell commands or "
        "instructions for the user to run manually unless a tool fails or the "
        "task is blocked."
    )


def max_effort_turn_reminder(user_text):
    if not request_requires_tool_action(user_text):
        return ""

    return (
        "Max effort is enabled for this turn. This is the high-budget workflow: "
        "spend extra tool calls and context when useful. For broad or "
        "project-level work, create a todo_write checklist, perform a planning "
        "or investigation phase, implement in several coherent steps, validate "
        "with real commands or file inspection, and only then conclude. Do not "
        "ask the user whether to continue after planning; continue implementing "
        "unless a real blocker prevents progress. Do not "
        "collapse a requested project into one small file unless the user "
        "explicitly asked for a single-file result."
    )


def validate_tool_calls(tool_calls, available_tool_names):
    valid = []
    invalid = []

    for index, tool_call in enumerate(tool_calls):
        function = tool_call.get("function", {})
        tool_name = function.get("name", "")
        arguments = function.get("arguments", "")

        if not tool_call.get("id"):
            invalid.append(f"tool call {index} had no id")
            continue

        if not tool_name:
            invalid.append(f"tool call {index} had no function name")
            continue

        if tool_name not in available_tool_names:
            invalid.append(f"tool call {index} requested unknown tool `{tool_name}`")
            continue

        try:
            json.loads(arguments or "{}")
        except Exception as error:
            invalid.append(
                f"tool call {index} `{tool_name}` had invalid JSON arguments: {error}"
            )
            continue

        valid.append(tool_call)

    return valid, invalid


def load_tools():
    return load_response_tools()


def api_messages(messages):
    allowed_keys = {
        "system": {"role", "content"},
        "user": {"role", "content"},
        "assistant": {"role", "content", "tool_calls"},
        "tool": {"role", "tool_call_id", "content"},
    }
    sanitized = []

    tool_names_by_id = {}

    for message in messages:
        if message.get("role") != "assistant":
            continue

        for tool_call in message.get("tool_calls", []) or []:
            function = tool_call.get("function", {})
            tool_names_by_id[tool_call.get("id")] = function.get("name", "")

    for message in messages:
        role = message.get("role")
        keys = allowed_keys.get(role)

        if keys is None:
            continue

        if role == "tool":
            content = message.get("content", "")
            display_result = message.get("display_result")

            if display_result is None:
                try:
                    display_result = json.loads(content or "{}")
                except (TypeError, ValueError):
                    display_result = None

            if isinstance(display_result, dict):
                tool_name = tool_names_by_id.get(
                    message.get("tool_call_id"),
                    "",
                )
                content = result_for_model(tool_name, {}, display_result)

            sanitized.append(
                {
                    "role": "tool",
                    "tool_call_id": message.get("tool_call_id"),
                    "content": content,
                }
            )
            continue

        if role == "user":
            sanitized.append(
                {
                    "role": "user",
                    "content": user_message_to_api_content(message),
                }
            )
            continue

        sanitized.append(
            {
                key: value
                for key, value in message.items()
                if key in keys and value is not None
            }
        )

    return trim_api_messages(sanitized)


def trim_api_messages(messages, max_chars=MAX_API_MESSAGES_CHARS):
    encoded = json.dumps(messages, ensure_ascii=False)

    if len(encoded) <= max_chars:
        return messages

    system_messages = [
        message
        for message in messages
        if message.get("role") == "system"
    ][:1]
    body = [
        message
        for message in messages
        if message.get("role") != "system"
    ]

    user_indexes = [
        index
        for index, message in enumerate(body)
        if message.get("role") == "user"
    ]

    for index in reversed(user_indexes):
        # Only include the omission notice if we are actually dropping earlier messages
        has_earlier = index > 0
        candidate = system_messages + (
            [
                {
                    "role": "user",
                    "content": (
                        "Earlier conversation history was omitted automatically "
                        "to keep the request within Rectury's context budget."
                    ),
                }
            ]
            if has_earlier
            else []
        ) + body[index:]

        if len(json.dumps(candidate, ensure_ascii=False)) <= max_chars:
            return candidate

    if user_indexes:
        index = user_indexes[-1]
        has_earlier = index > 0
        return system_messages + (
            [
                {
                    "role": "user",
                    "content": (
                        "Earlier conversation history was omitted automatically "
                        "to keep the request within Rectury's context budget."
                    ),
                }
            ]
            if has_earlier
            else []
        ) + body[index:]

    return system_messages + body[-2:]


def api_context_was_trimmed(messages):
    return len(json.dumps(messages, ensure_ascii=False)) > MAX_API_MESSAGES_CHARS


def memory_summary_prompt(existing_summary, message_chunk):
    return (
        "You maintain the durable memory for a coding assistant.\n"
        "Update the memory using the new conversation chunk.\n\n"
        "Rules:\n"
        "- Preserve only stable, useful state.\n"
        "- Keep the result concise but complete.\n"
        "- Use English.\n"
        "- Include the current goal, important decisions, files touched, "
        "commands run, tool outcomes, open tasks, and any risks or caveats.\n"
        "- Omit chit-chat and exact wording unless it matters.\n"
        "- If the new chunk conflicts with the previous memory, prefer the "
        "newer explicit instruction or result.\n"
        "- Return only the updated memory text.\n\n"
        "Existing memory:\n"
        f"{existing_summary or '(empty)'}\n\n"
        "New conversation chunk:\n"
        f"{message_chunk}"
    )


def hook_summary_for_model(hook_result):
    nested = hook_result.get("result", {})
    status = "failed" if hook_result.get("error") else "completed"

    if nested:
        if nested.get("error") or nested.get("returncode", 0) != 0:
            status = "failed"
        else:
            status = "completed"

    parts = [
        f"Hook {hook_result.get('event')} / {hook_result.get('name')} {status}.",
    ]

    if hook_result.get("command"):
        parts.append(f"Command: {hook_result['command']}")

    if hook_result.get("error"):
        parts.append(f"Error: {hook_result['error']}")

    if nested:
        parts.append(f"Exit: {nested.get('returncode')}")
        stdout = (nested.get("stdout") or "").strip()
        stderr = (nested.get("stderr") or "").strip()

        if stdout:
            parts.append(f"stdout:\n{stdout[:2000]}")

        if stderr:
            parts.append(f"stderr:\n{stderr[:2000]}")

    return "\n".join(parts)


def normalized_positive_int(value, default):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default

    return parsed if parsed > 0 else default


def read_tool_cache_key(tool_name, arguments):
    if tool_name == "read_file":
        return json.dumps(
            {
                "tool": tool_name,
                "file_path": str(arguments.get("file_path", "")),
                "offset": normalized_positive_int(arguments.get("offset", 1), 1),
                "limit": normalized_positive_int(arguments.get("limit", 500), 500),
            },
            sort_keys=True,
        )

    if tool_name == "read_reference_file":
        return json.dumps(
            {
                "tool": tool_name,
                "reference": str(arguments.get("reference", "")),
                "file_path": str(arguments.get("file_path", "")),
                "offset": normalized_positive_int(arguments.get("offset", 1), 1),
                "limit": normalized_positive_int(arguments.get("limit", 500), 500),
            },
            sort_keys=True,
        )

    return None


class ChatSession:
    MAX_TOOL_ROUNDS = 32

    def __init__(self, permission_handler=None):
        try:
            self.client, self.config = create_client()
        except ValueError:
            self.client = None
            self.config = ClientConfig(provider="", model="", base_url=None)
        self.config_version = model_env_version()
        self.tools = load_tools()
        self.available_tool_names = {
            tool["function"]["name"]
            for tool in self.tools
        }
        self.permission_handler = permission_handler
        self.usage_stats = initial_usage_stats(self.config)
        self.command_cancel_requested = None
        self.active_command_process = None
        self.permission_mode = "auto"
        self.effort_mode = "normal"
        self.current_turn_thinking_tokens = 0
        self.new_conversation()

    def set_permission_mode(self, mode):
        if mode not in {"ask", "auto", "plan", "danger"}:
            raise ValueError("mode must be ask, auto, plan, or danger")

        self.permission_mode = mode
        self._refresh_system_message()

    def set_effort_mode(self, mode):
        if mode not in {"normal", "max"}:
            raise ValueError("mode must be normal or max")

        self.effort_mode = mode
        self.usage_stats["effort_mode"] = mode
        self._refresh_system_message()

    def should_request_permission(self, tool_name, arguments, preview):
        decision = can_use_tool(
            tool_name,
            arguments,
            preview,
            permission_mode=self.permission_mode,
        )
        return decision.needs_prompt

    def cancel_active_command(self):
        if self.command_cancel_requested is not None:
            self.command_cancel_requested.set()
            return True

        return False

    def set_active_command_process(self, process):
        self.active_command_process = process

    def hook_context_for_tool(self, tool_name, arguments, result=None):
        context = {
            "tool": tool_name,
        }

        if tool_name in {
            "delete_file",
            "edit_file",
            "edit_notebook",
            "insert_notebook_cell",
            "delete_notebook_cell",
            "memory_write",
            "multi_edit",
            "write_file",
        }:
            context["file"] = (
                (result or {}).get("file_path")
                or arguments.get("file_path", "")
            )

        if tool_name == "run_command":
            context["command"] = arguments.get("command", "")
            if result is not None:
                context["exit_code"] = result.get("returncode", "")

        return context

    def emit_hook_events(self, event, context, tool_round, tool_results):
        hook_results = run_hooks(
            self.state,
            event,
            context,
            self.permission_mode,
        )

        for index, hook_result in enumerate(hook_results):
            event_key = f"{tool_round}:hook:{event}:{index}"
            arguments = {
                "event": event,
                "name": hook_result.get("name", event),
                "command": hook_result.get("command", ""),
            }
            yield {
                "type": "tool_started",
                "tool_call_id": event_key,
                "event_key": event_key,
                "tool": "hook",
                "arguments": arguments,
            }
            yield {
                "type": "tool_finished",
                "tool_call_id": event_key,
                "event_key": event_key,
                "tool": "hook",
                "arguments": arguments,
                "result": hook_result,
            }
            tool_results.append(
                {
                    "name": "hook",
                    "arguments": arguments,
                    "result": hook_result,
                }
            )
            self.messages.append(
                {
                    "role": "system",
                    "content": hook_summary_for_model(hook_result),
                }
            )

    def reload_client(self):
        self.client, self.config = create_client()
        self.config_version = model_env_version()
        self.usage_stats.update(
            {
                "provider": self.config.provider,
                "model": self.config.model,
                "context_window_tokens": context_window_for_model(
                    self.config.model
                ),
            }
        )

    def reload_client_if_config_changed(self):
        current_version = model_env_version()

        if current_version == self.config_version:
            return

        try:
            self.reload_client()
        except ValueError:
            self.client = None
            self.config = ClientConfig(provider="", model="", base_url=None)
            self.config_version = current_version

    def _system_message(self):
        return create_system_message(
            self.state.workspace,
            current_time(),
            build_context(str(self.state.workspace)),
            self.memory_summary,
            self.permission_mode,
            self.effort_mode,
            self.state.get_reference_paths(),
            self.config.provider,
            self.config.model,
        )

    def _refresh_system_message(self):
        system_message = self._system_message()

        if self.messages and self.messages[0].get("role") == "system":
            self.messages[0] = system_message
        else:
            self.messages.insert(0, system_message)

    def _conversation_data(self):
        return {
            "id": self.conversation_id,
            "title": self.title,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "messages": self.messages,
            "memory_summary": self.memory_summary,
            "memory_compacted_upto": self.memory_compacted_upto,
            "todos": self.state.get_todos(),
            "checkpoints": self.state.get_checkpoints(),
            "reference_paths": self.state.get_reference_paths(),
            "effort_mode": self.effort_mode,
        }

    def _save(self):
        self.updated_at = current_time()
        save_conversation(self._conversation_data())

    def open_conversation(self, conversation_id):
        conversation = load_conversation(conversation_id)

        if conversation is None:
            return False
        self.state = SessionState.from_cwd()
        self.state.set_todos(conversation.get("todos", []))
        self.state.set_checkpoints(conversation.get("checkpoints", []))
        self.state.set_reference_paths(conversation.get("reference_paths", []))
        self.conversation_id = conversation["id"]
        self.title = conversation.get("title", "New conversation")
        self.created_at = conversation.get("created_at", current_time())
        self.updated_at = conversation.get("updated_at", current_time())
        self.messages = conversation.get("messages", [])
        self.memory_summary = conversation.get("memory_summary", "")
        self.effort_mode = conversation.get("effort_mode", "normal")
        if self.effort_mode not in {"normal", "max"}:
            self.effort_mode = "normal"
        self.usage_stats["effort_mode"] = self.effort_mode
        self.current_turn_thinking_tokens = 0
        self.usage_stats["last_thinking_tokens"] = 0
        self.memory_compacted_upto = max(
            1,
            min(
                conversation.get("memory_compacted_upto", 1),
                len(self.messages),
            ),
        )
        self._refresh_system_message()

        return True

    def new_conversation(self):
        self.state = SessionState.from_cwd()
        self.conversation_id = str(uuid4())
        self.title = "New conversation"
        self.created_at = current_time()
        self.updated_at = self.created_at
        self.memory_summary = ""
        self.memory_compacted_upto = 1
        self.effort_mode = getattr(self, "effort_mode", "normal")
        if self.effort_mode not in {"normal", "max"}:
            self.effort_mode = "normal"
        self.usage_stats["effort_mode"] = self.effort_mode
        self.current_turn_thinking_tokens = 0
        self.usage_stats["last_thinking_tokens"] = 0
        self.messages = []
        self._refresh_system_message()

    def get_conversations(self):
        return list_conversations()

    def _fallback_title(self, user_input):
        words = user_input.strip().split()
        title = " ".join(words[:6])
        return title[:60] or "New conversation"

    def _generate_title(self, user_input, assistant_response):
        if self.client is None:
            return self._fallback_title(user_input)

        try:
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {
                        "role": "system",
                        "content": TITLE_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": (
                            f"User: {user_input}\n"
                            f"Assistant: {assistant_response}"
                        ),
                    },
                ],
            )
            title = response.choices[0].message.content or ""
            title = " ".join(title.strip().strip('"').strip("'").split())
            return title[:60] or self._fallback_title(user_input)
        except Exception:
            return self._fallback_title(user_input)

    def _memory_compaction_cutoff(self):
        if len(self.messages) <= 2:
            return self.memory_compacted_upto

        recent_start = max(1, len(self.messages) - RECENT_MESSAGES_TO_KEEP)
        return max(self.memory_compacted_upto, recent_start)

    def _compact_memory(self, force=False):
        self.reload_client_if_config_changed()

        if self.client is None:
            return False, "Model is not configured."

        messages_for_api = api_messages(self.messages)
        encoded_length = len(json.dumps(messages_for_api, ensure_ascii=False))

        if not force and encoded_length < MEMORY_COMPACTION_TRIGGER_CHARS:
            return False, "Conversation does not need compaction yet."

        cutoff = self._memory_compaction_cutoff()

        if cutoff <= self.memory_compacted_upto:
            return False, "There is no new conversation history to compact."

        chunk = self.messages[self.memory_compacted_upto:cutoff]

        if not chunk:
            return False, "There is no new conversation history to compact."

        try:
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You compact long coding-agent conversations into "
                            "durable working memory."
                        ),
                    },
                    {
                        "role": "user",
                        "content": memory_summary_prompt(
                            self.memory_summary.strip(),
                            json.dumps(
                                api_messages(chunk),
                                ensure_ascii=False,
                            ),
                        ),
                    },
                ],
            )
            summary = response.choices[0].message.content or ""
        except Exception as error:
            return False, f"Could not compact conversation: {error}"

        summary = " ".join(summary.strip().split())

        if not summary:
            return False, "Could not compact conversation: empty summary."

        if len(summary) > MAX_MEMORY_SUMMARY_CHARS:
            summary = summary[:MAX_MEMORY_SUMMARY_CHARS].rstrip()

        self.memory_summary = summary
        self.memory_compacted_upto = cutoff
        self._refresh_system_message()
        self._save()
        return True, "Conversation compacted. Durable memory updated."

    def _stream_response(
        self,
        tool_round,
        require_tool=False,
        required_tool_retry=False,
        forced_tool_name=None,
    ):
        messages_for_api = api_messages(self.messages)

        if require_tool:
            messages_for_api.append(
                {
                    "role": "system",
                    "content": required_tool_reminder(required_tool_retry),
                }
            )

        request_started_at = monotonic()
        estimated_input_tokens = estimate_tokens(messages_for_api)
        context_window = context_window_for_model(self.config.model)
        history_omitted = api_context_was_trimmed(self.messages)
        request_kwargs = {
            "model": self.config.model,
            "messages": messages_for_api,
            "tools": self.tools,
            "parallel_tool_calls": False,
            "stream": True,
        }
        requested_thinking_tokens = getattr(
            self,
            "current_turn_thinking_tokens",
            0,
        )
        applied_thinking_kwargs = thinking_request_kwargs(
            self.config.provider,
            self.config.model,
            requested_thinking_tokens,
        )
        request_kwargs.update(applied_thinking_kwargs)

        if forced_tool_name:
            request_kwargs["tool_choice"] = {
                "type": "function",
                "function": {"name": forced_tool_name},
            }
        elif require_tool:
            request_kwargs["tool_choice"] = "required"

        api_start_time = monotonic()

        def create_stream(kwargs):
            try:
                return self.client.chat.completions.create(
                    **kwargs,
                    stream_options={"include_usage": True},
                )
            except Exception:
                return self.client.chat.completions.create(**kwargs)

        while True:
            try:
                stream = create_stream(request_kwargs)
                break
            except Exception as error:
                error_text = str(error).lower()
                unsupported_required_tool_choice = (
                    "tool_choice" in error_text
                    or "required" in error_text
                    or "unsupported" in error_text
                )

                if applied_thinking_kwargs and is_thinking_parameter_error(error):
                    for key in applied_thinking_kwargs:
                        request_kwargs.pop(key, None)
                    applied_thinking_kwargs = {}
                    self.usage_stats["last_thinking_tokens"] = 0
                    continue

                if require_tool and unsupported_required_tool_choice:
                    request_kwargs.pop("tool_choice", None)
                    continue

                raise

        content_parts = []
        tool_calls = {}
        usage = None

        for chunk in stream:
            if getattr(chunk, "usage", None):
                usage = chunk.usage

            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta

            if delta.content:
                content_parts.append(delta.content)
                if not require_tool:
                    yield {
                        "type": "content",
                        "content": delta.content,
                    }

            for tool_call in delta.tool_calls or []:
                event_key = f"{tool_round}:{tool_call.index}"
                current = tool_calls.setdefault(
                    tool_call.index,
                    {
                        "id": "",
                        "type": "function",
                        "function": {"name": "", "arguments": ""},
                        "event_key": event_key,
                    },
                )

                if tool_call.id:
                    current["id"] = tool_call.id
                if tool_call.function:
                    if tool_call.function.name:
                        current["function"]["name"] += tool_call.function.name
                    if tool_call.function.arguments:
                        current["function"]["arguments"] += (
                            tool_call.function.arguments
                        )

        completed_tool_calls = []

        for index in sorted(tool_calls):
            tool_call = tool_calls[index]
            completed_tool_calls.append(tool_call)

        content = "".join(content_parts)

        if require_tool and completed_tool_calls and content:
            yield {
                "type": "content",
                "content": content,
            }

        visible_output_tokens = estimate_tokens(content) if content else 0
        estimated_output_tokens = visible_output_tokens
        input_tokens = estimated_input_tokens
        output_tokens = estimated_output_tokens
        total_tokens = input_tokens + output_tokens
        estimated = True

        if usage is not None:
            input_tokens = (
                getattr(usage, "prompt_tokens", None)
                or getattr(usage, "input_tokens", None)
                or input_tokens
            )
            output_tokens = (
                getattr(usage, "completion_tokens", None)
                or getattr(usage, "output_tokens", None)
                or output_tokens
            )
            total_tokens = (
                getattr(usage, "total_tokens", None)
                or input_tokens + output_tokens
            )
            estimated = False

        duration_ms = int((monotonic() - request_started_at) * 1000)
        api_duration_seconds = monotonic() - api_start_time
        tokens_per_second = (
            visible_output_tokens / (duration_ms / 1000)
            if duration_ms > 0
            else 0.0
        )

        # Track API cost and duration
        add_to_total_cost(0.0, api_duration_seconds)
        self.usage_stats.update(
            {
                "provider": self.config.provider or "not configured",
                "model": self.config.model or "not configured",
                "context_window_tokens": context_window,
                "last_input_tokens": input_tokens,
                "last_output_tokens": output_tokens,
                "last_total_tokens": total_tokens,
                "last_estimated": estimated,
                "last_duration_ms": duration_ms,
                "last_tokens_per_second": tokens_per_second,
                "last_thinking_tokens": (
                    requested_thinking_tokens
                    if applied_thinking_kwargs
                    else 0
                ),
                "context_used_tokens": estimated_input_tokens,
                "context_used_percent": min(
                    100.0,
                    (estimated_input_tokens / context_window) * 100,
                ),
                "history_omitted": history_omitted,
            }
        )
        self.usage_stats["session_input_tokens"] += input_tokens
        self.usage_stats["session_output_tokens"] += output_tokens
        self.usage_stats["session_total_tokens"] += total_tokens
        self.usage_stats["session_requests"] += 1

        return content, completed_tool_calls

    def compact_conversation(self):
        return self._compact_memory(force=True)

    def send_message(self, user_input):
        self.reload_client_if_config_changed()

        if self.client is None:
            yield {
                "type": "content",
                "content": "Model is not configured. Run `/models` to set one up.",
            }
            return

        if isinstance(user_input, dict):
            user_text = str(user_input.get("text", ""))
            user_attachments = user_input.get("attachments", []) or []
        else:
            user_text = str(user_input)
            user_attachments = []

        # Handle slash commands
        if user_text.startswith("/approved-tools"):
            args = user_text.split()[1:] if len(user_text.split()) > 1 else []
            cwd = getattr(self, "workspace", ".")
            result = handle_approved_tools_command(args, cwd)
            yield {"type": "content", "content": result}
            return

        if user_text.startswith("/bug"):
            description = user_text[4:].strip()
            messages = getattr(self, "messages", [])
            cwd = getattr(self, "workspace", ".")
            result = handle_bug_command(description, messages, cwd)
            yield {"type": "content", "content": result}
            return

        if user_text.startswith("/cost"):
            result = handle_cost_command()
            yield {"type": "content", "content": result}
            return

        if user_text.startswith("/doctor"):
            result = handle_doctor_command()
            yield {"type": "content", "content": result}
            return

        if user_text.startswith("/init"):
            cwd = getattr(self, "workspace", ".")
            result = handle_init_command(cwd)
            yield {"type": "content", "content": result}
            return

        if user_text.startswith("/compact"):
            result = handle_compact_command(
                client=self.client,
                model=self.config.model if self.config else "",
                messages=self.messages,
            )

            if result["success"]:
                # Replace messages with compacted version (summary only)
                self.messages = result["cleared_messages"]
                self._refresh_system_message()
                yield {"type": "content", "content": result["message"]}
            else:
                yield {"type": "content", "content": result["message"]}
            return

        if user_text.startswith("/listen"):
            if is_listen_enabled():
                result = handle_listen_command()
                yield {"type": "content", "content": result}
            else:
                yield {"type": "content", "content": "Listen command is only available on macOS with iTerm.app or Apple Terminal."}
            return

        if user_text.startswith("/pr-comments"):
            result = handle_pr_comments_command()
            yield {"type": "content", "content": result}
            return

        if user_text.startswith("/review"):
            args = user_text[7:].strip()
            result = handle_review_command(args)
            yield {"type": "content", "content": result}
            return

        self.messages.append(
            {
                "role": "user",
                "content": user_text,
                "attachments": user_attachments,
            }
        )
        self.current_turn_thinking_tokens = get_max_thinking_tokens(
            [
                {
                    "role": "user",
                    "content": user_text,
                }
            ],
            think_tool_enabled=False,
        )
        self.usage_stats["last_thinking_tokens"] = (
            self.current_turn_thinking_tokens
        )
        self._refresh_system_message()

        self._compact_memory()

        final_content = ""
        failed_tool_calls = {}
        successful_read_calls = {}
        edit_intro_shown = False
        tool_results = []
        empty_completion_retries = 0
        invalid_tool_retries = 0
        required_tool_retries = 0
        completion_reminder = None
        action_requires_tools = request_requires_tool_action(user_text)
        max_workflow = (
            self.effort_mode == "max"
            and action_requires_tools
            and request_requires_max_workflow(user_text)
        )
        max_effort_reminder = None

        if self.effort_mode == "max":
            reminder_content = max_effort_turn_reminder(user_text)

            if reminder_content:
                max_effort_reminder = {
                    "role": "system",
                    "content": reminder_content,
                }
                self.messages.append(max_effort_reminder)

        for tool_round in range(self.MAX_TOOL_ROUNDS):
            self._compact_memory()

            try:
                completed_tool_names = {
                    tool_result["name"]
                    for tool_result in tool_results
                    if not tool_result["result"].get("error")
                }
                forced_tool_name = None

                if max_workflow:
                    if "todo_write" not in completed_tool_names:
                        forced_tool_name = "todo_write"
                    elif not completed_tool_names.intersection(
                        MAX_WORKFLOW_PLANNING_TOOLS
                    ):
                        forced_tool_name = "architect"

                require_tool = (
                    action_requires_tools
                    and not tool_results
                    and required_tool_retries <= MAX_REQUIRED_TOOL_RETRIES
                )
                stream = self._stream_response(
                    tool_round,
                    require_tool=require_tool or bool(forced_tool_name),
                    required_tool_retry=required_tool_retries > 0,
                    forced_tool_name=forced_tool_name,
                )

                while True:
                    yield next(stream)
            except StopIteration as completed:
                content, tool_calls = completed.value
                yield {
                    "type": "usage",
                    "stats": self.usage_stats,
                }
            except Exception as error:
                content = format_model_error(error)
                yield {
                    "type": "content",
                    "content": content,
                }
                self.messages.append(
                    {
                        "role": "assistant",
                        "content": content,
                    }
                )
                final_content += content

                if self.title == "New conversation":
                    self.title = self._generate_title(user_input, final_content)

                if max_effort_reminder in self.messages:
                    self.messages.remove(max_effort_reminder)

                self._save()
                return

            if completion_reminder is not None:
                self.messages.remove(completion_reminder)
                completion_reminder = None

            valid_tool_calls, invalid_tool_calls = validate_tool_calls(
                tool_calls,
                self.available_tool_names,
            )

            if invalid_tool_calls:
                invalid_summary = "\n".join(
                    f"- {item}"
                    for item in invalid_tool_calls[:10]
                )

                if invalid_tool_retries < MAX_INVALID_TOOL_RETRIES:
                    self.messages.append(
                        {
                            "role": "assistant",
                            "content": content or None,
                        }
                    )
                    self.messages.append(
                        {
                            "role": "system",
                            "content": (
                                "The previous response contained invalid tool "
                                "calls and Rectury did not execute them:\n"
                                f"{invalid_summary}\n\n"
                                "Continue by replying again with valid tool "
                                "calls, or answer directly if no tool is needed."
                            ),
                        }
                    )
                    invalid_tool_retries += 1
                    continue

                if not valid_tool_calls:
                    suffix = (
                        "\n\nRectury could not execute the model's invalid "
                        "tool calls:\n"
                        f"{invalid_summary}"
                    )
                    yield {
                        "type": "content",
                        "content": suffix,
                    }
                    content += suffix

            tool_calls = valid_tool_calls

            if (
                action_requires_tools
                and not tool_calls
                and not tool_results
                and required_tool_retries < MAX_REQUIRED_TOOL_RETRIES
            ):
                required_tool_retries += 1
                continue

            if (
                action_requires_tools
                and not tool_calls
                and not tool_results
                and required_tool_retries >= MAX_REQUIRED_TOOL_RETRIES
            ):
                content = (
                    "Rectury could not get the configured model to use tools "
                    "for this actionable request. Try again, or switch to a "
                    "model with reliable function/tool calling in `/models`."
                )
                yield {
                    "type": "content",
                    "content": content,
                }

            has_sensitive = any(
                tool_call.get("function", {}).get("name")
                in {
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
                    "change_workspace",
                    "run_command",
                }
                for tool_call in tool_calls
            )

            if has_sensitive and not edit_intro_shown:
                if not content.strip():
                    content = create_edit_intro(tool_calls)

                    if content:
                        yield {
                            "type": "content",
                            "content": content,
                        }

                edit_intro_shown = True

            if not tool_calls and not content.strip() and tool_results:
                if empty_completion_retries == 0:
                    completion_reminder = {
                        "role": "system",
                        "content": (
                            "Your response after the tool result was empty. "
                            "Continue the task if work remains. Otherwise, "
                            "provide the required final conclusion now."
                        ),
                    }
                    self.messages.append(completion_reminder)
                    empty_completion_retries += 1
                    continue

                content = create_fallback_conclusion(tool_results)
                yield {
                    "type": "content",
                    "content": content,
                }

            if not tool_calls and not content.strip():
                content = (
                    "The configured model returned an empty response. Please try "
                    "again in a moment."
                )
                yield {
                    "type": "content",
                    "content": content,
                }

            final_content += content
            assistant_message = {
                "role": "assistant",
                "content": content or None,
            }

            if tool_calls:
                assistant_message["tool_calls"] = [
                    {
                        "id": tool_call["id"],
                        "type": tool_call["type"],
                        "function": tool_call["function"],
                    }
                    for tool_call in tool_calls
                ]

            self.messages.append(assistant_message)

            if not tool_calls:
                if max_effort_reminder in self.messages:
                    self.messages.remove(max_effort_reminder)

                if self.title == "New conversation":
                    self.title = self._generate_title(user_input, final_content)
                self._save()
                return

            for tool_call in tool_calls:
                function = tool_call["function"]
                arguments = {}
                call_key = None
                read_call_key = None
                preview = None
                display_tool_call = True

                try:
                    arguments = json.loads(function["arguments"] or "{}")
                except Exception as error:
                    result = {"error": str(error)}
                else:
                    result = None
                    tool_name, arguments = normalize_compact_tool_call(
                        function["name"],
                        arguments,
                    )
                    function["name"] = tool_name
                    function["arguments"] = json.dumps(arguments)

                call_key = json.dumps(
                    {
                        "tool": function["name"],
                        "arguments": arguments,
                    },
                    sort_keys=True,
                )
                read_call_key = read_tool_cache_key(function["name"], arguments)

                if (
                    result is None
                    and read_call_key is not None
                    and read_call_key in successful_read_calls
                ):
                    result = deepcopy(successful_read_calls[read_call_key])
                    result["cached"] = True
                    result["duplicate_read_skipped"] = True
                    result["duration_ms"] = 0
                    display_tool_call = False

                if display_tool_call:
                    yield {
                        "type": "tool_started",
                        "tool_call_id": tool_call["id"],
                        "event_key": tool_call["event_key"],
                        "tool": function["name"],
                        "arguments": arguments,
                    }

                if result is None:
                    previous_failure = failed_tool_calls.get(call_key)

                    permission_decision = can_use_tool(
                        function["name"],
                        arguments,
                        preview,
                        permission_mode=self.permission_mode,
                    )

                    if permission_decision.denied:
                        result = denied_tool_result(
                            function["name"],
                            permission_decision,
                        )
                    elif previous_failure is not None:
                        result = {
                            "error": (
                                "This identical tool call already failed. "
                                "Change the arguments or use a different "
                                "approach instead of retrying it unchanged."
                            ),
                            "code": "duplicate_failed_call",
                            "previous_error": previous_failure.get("error"),
                        }
                    elif function["name"] == "run_command":
                        validation = validate_command(
                            arguments.get("command", "")
                        )

                        if not validation["ok"]:
                            result = {
                                "error": validation["error"],
                                "code": validation.get(
                                    "code",
                                    "invalid_command",
                                ),
                            }
                        else:
                            preview = {
                                "success": True,
                                "tool": function["name"],
                                "arguments": arguments,
                                "safe": validation["safe"],
                                "prefix": validation.get("prefix", ""),
                            }

                    elif function["name"] == "delete_file":
                        try:
                            preview = preview_delete_file(
                                state=self.state, **arguments
                            )
                        except TypeError as error:
                            result = {"error": str(error)}
                            preview = None

                    elif function["name"] == "write_file":
                        try:
                            preview = preview_write_file(
                                state=self.state, **arguments
                            )
                        except TypeError as error:
                            result = {"error": str(error)}
                            preview = None

                    elif function["name"] == "edit_file":
                        try:
                            preview = preview_edit_file(
                                state=self.state, **arguments
                            )
                        except TypeError as error:
                            result = {"error": str(error)}
                            preview = None

                    elif function["name"] == "multi_edit":
                        try:
                            preview = preview_multi_edit(
                                state=self.state, **arguments
                            )
                        except TypeError as error:
                            result = {"error": str(error)}
                            preview = None

                    elif function["name"] == "memory_write":
                        try:
                            preview = preview_memory_write(
                                state=self.state, **arguments
                            )
                        except TypeError as error:
                            result = {"error": str(error)}
                            preview = None

                    elif function["name"] == "edit_notebook":
                        try:
                            preview = preview_edit_notebook(
                                state=self.state, **arguments
                            )
                        except TypeError as error:
                            result = {"error": str(error)}
                            preview = None

                    elif function["name"] == "insert_notebook_cell":
                        try:
                            preview = preview_insert_notebook_cell(
                                state=self.state, **arguments
                            )
                        except TypeError as error:
                            result = {"error": str(error)}
                            preview = None

                    elif function["name"] == "delete_notebook_cell":
                        try:
                            preview = preview_delete_notebook_cell(
                                state=self.state, **arguments
                            )
                        except TypeError as error:
                            result = {"error": str(error)}
                            preview = None

                    elif function["name"] in {"mcp_list_tools", "mcp_call_tool"}:
                        preview = {
                            "success": True,
                            "tool": function["name"],
                            "arguments": arguments,
                        }

                    elif function["name"] == "change_workspace":
                        preview = {
                            "success": True,
                            "tool": function["name"],
                            "arguments": arguments,
                        }

                    elif function["name"] == "undo_last_change":
                        preview = preview_undo_last_change(self.state)

                    else:
                        preview = None

                    if (
                        result is None
                        and preview is not None
                        and self.should_request_permission(
                            function["name"],
                            arguments,
                            preview,
                        )
                        and self.permission_handler is not None
                    ):
                        if not preview.get("success"):
                            result = preview
                        elif not self.permission_handler(
                            function["name"],
                            arguments,
                            preview,
                        ):
                            result = rejected_tool_result(
                                function["name"],
                                preview,
                            )

                    if result is None:
                        try:
                            started_at = monotonic()
                            if function["name"] in {
                                "delete_file",
                                "edit_file",
                                "edit_notebook",
                                "insert_notebook_cell",
                                "delete_notebook_cell",
                                "memory_write",
                                "multi_edit",
                                "write_file",
                            }:
                                yield from self.emit_hook_events(
                                    "before_edit",
                                    self.hook_context_for_tool(
                                        function["name"],
                                        arguments,
                                    ),
                                    tool_round,
                                    tool_results,
                                )

                            if function["name"] == "run_command":
                                yield from self.emit_hook_events(
                                    "before_command",
                                    self.hook_context_for_tool(
                                        function["name"],
                                        arguments,
                                    ),
                                    tool_round,
                                    tool_results,
                                )

                            if function["name"] == "run_command":
                                from threading import Event

                                self.command_cancel_requested = Event()
                                self.active_command_process = None
                                result = None

                                for command_event in run_command_stream(
                                    state=self.state,
                                    cancel_event=self.command_cancel_requested,
                                    on_process=self.set_active_command_process,
                                    **arguments,
                                ):
                                    if command_event.get("type") == "output":
                                        yield {
                                            "type": "tool_update",
                                            "tool_call_id": tool_call["id"],
                                            "event_key": tool_call["event_key"],
                                            "tool": function["name"],
                                            "arguments": arguments,
                                            "stream": command_event["stream"],
                                            "content": command_event["content"],
                                            "duration_ms": command_event.get(
                                                "duration_ms"
                                            ),
                                        }
                                    elif command_event.get("type") == "result":
                                        result = command_event["result"]

                                if result is None:
                                    result = {
                                        "error": "command produced no result."
                                    }
                            else:
                                result = run_tool(
                                    function["name"],
                                    arguments,
                                    self.state,
                                )
                            result.setdefault(
                                "duration_ms",
                                int((monotonic() - started_at) * 1000),
                            )
                        except Exception as error:
                            result = {"error": str(error)}
                        finally:
                            if function["name"] == "run_command":
                                self.command_cancel_requested = None
                                self.active_command_process = None

                    if (
                        result is not None
                        and not result.get("error")
                        and function["name"]
                        in {"reference_add", "reference_remove"}
                    ):
                        self._refresh_system_message()

                    if (
                        result is not None
                        and not result.get("error")
                        and function["name"] in {
                            "delete_file",
                            "edit_file",
                            "edit_notebook",
                            "insert_notebook_cell",
                            "delete_notebook_cell",
                            "memory_write",
                            "multi_edit",
                            "write_file",
                        }
                    ):
                        yield from self.emit_hook_events(
                            "after_edit",
                            self.hook_context_for_tool(
                                function["name"],
                                arguments,
                                result,
                            ),
                            tool_round,
                            tool_results,
                        )

                    if result is not None and function["name"] == "run_command":
                        yield from self.emit_hook_events(
                            "after_command",
                            self.hook_context_for_tool(
                                function["name"],
                                arguments,
                                result,
                            ),
                            tool_round,
                            tool_results,
                        )

                    if (
                        result is not None
                        and not result.get("error")
                        and function["name"] == "todo_write"
                        and result.get("counts", {}).get("pending", 0) == 0
                        and result.get("counts", {}).get("in_progress", 0) == 0
                        and result.get("total", 0) > 0
                    ):
                        yield from self.emit_hook_events(
                            "task_complete",
                            {"tool": function["name"]},
                            tool_round,
                            tool_results,
                        )

                    if result.get("error"):
                        failed_tool_calls[call_key] = result
                    else:
                        failed_tool_calls.pop(call_key, None)

                    if (
                        read_call_key is not None
                        and not result.get("error")
                        and not result.get("rejected")
                    ):
                        successful_read_calls[read_call_key] = deepcopy(result)

                output = result_for_model(
                    function["name"],
                    arguments,
                    result,
                )

                if display_tool_call:
                    yield {
                        "type": "tool_finished",
                        "tool_call_id": tool_call["id"],
                        "event_key": tool_call["event_key"],
                        "tool": function["name"],
                        "arguments": arguments,
                        "result": result,
                    }

                tool_results.append(
                    {
                        "name": function["name"],
                        "arguments": arguments,
                        "result": result,
                    }
                )

                self.messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": output,
                        "display_result": result,
                    }
                )

                if result.get("code") == "permission_denied":
                    if max_effort_reminder in self.messages:
                        self.messages.remove(max_effort_reminder)
                    self._save()
                    return

        max_rounds_message = (
            "Tool execution stopped after reaching the maximum number "
            "of tool rounds. Review the last visible tool result and continue "
            "with a narrower request if more work is needed."
        )
        yield {
            "type": "content",
            "content": max_rounds_message,
        }
        self.messages.append(
            {
                "role": "assistant",
                "content": max_rounds_message,
            }
        )
        if max_effort_reminder in self.messages:
            self.messages.remove(max_effort_reminder)
        self._save()
