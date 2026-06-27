import json
import mimetypes
import os
import re
import shlex
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
from threading import Event
from urllib.parse import unquote, urlparse
from uuid import uuid4

from core.command_approvals import (
    approve_command,
    approved_command_keys,
)
from core.command_security import validate_command
from core.hooks import (
    create_default_hook_config,
    hook_config_path,
    load_hook_config,
    run_hooks,
)
from textual.app import App, ComposeResult
from textual.screen import ModalScreen
from textual.widgets import (
    Input,
    Label,
    ListItem,
    ListView,
    Markdown,
    Static,
    TextArea,
)
from textual.containers import Container, Horizontal, VerticalScroll, Vertical
from core.chat import ChatSession
from core.tool_permissions import (
    can_use_tool,
    permission_key as build_permission_key,
)
from core.tool_runner import run_tool
from tools.functions.run_command import run_command_stream
from ui.components import PermissionMessage, ToolMessage, get_tool_target
from ui.theme import APP_CSS
from ui.visual import THEME, format_number
from textual import work
from textual.binding import Binding
from textual.events import Key, MouseUp, Paste, TextSelected
from PIL import ImageGrab, Image


ENV_PATH = Path(".env")
MODEL_ENV_KEYS = ("AI_PROVIDER", "AI_MODEL", "AI_API_KEY", "AI_BASE_URL")
LONG_PASTE_MIN_CHARS = 200
LONG_PASTE_MIN_LINES = 2
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}
IMAGE_MARKER_RE = re.compile(r"\[Image #\d+\]")


@dataclass(frozen=True)
class ModelOption:
    name: str
    provider: str
    model: str
    base_url: str
    note: str = ""
    free: bool = False
    api_key: str = ""


MODEL_OPTIONS = [
    ModelOption(
        "OpenRouter: DeepSeek V3.1 Free",
        "openrouter",
        "deepseek/deepseek-chat-v3.1:free",
        "https://openrouter.ai/api/v1",
        "API key",
        free=True,
    ),
    ModelOption(
        "OpenRouter: Qwen3 Coder Free",
        "openrouter",
        "qwen/qwen3-coder:free",
        "https://openrouter.ai/api/v1",
        "API key",
        free=True,
    ),
    ModelOption(
        "OpenRouter: Kimi K2 Free",
        "openrouter",
        "moonshotai/kimi-k2:free",
        "https://openrouter.ai/api/v1",
        "API key",
        free=True,
    ),
    ModelOption(
        "OpenAI",
        "openai",
        "gpt-4.1",
        "https://api.openai.com/v1",
        "ChatGPT Plus/Pro or API key",
    ),
    ModelOption(
        "OpenRouter",
        "openrouter",
        "openai/gpt-4.1",
        "https://openrouter.ai/api/v1",
        "Many providers through one API key",
    ),
    ModelOption(
        "xAI: Grok 4.3",
        "xai",
        "grok-4.3",
        "https://api.x.ai/v1",
        "xAI API key",
    ),
    ModelOption(
        "xAI: Grok 3 Mini",
        "xai",
        "grok-3-mini",
        "https://api.x.ai/v1",
        "xAI API key",
    ),
    ModelOption(
        "Ollama Local",
        "ollama",
        "qwen3",
        "http://localhost:11434/v1",
        "Local",
        api_key="ollama",
    ),
    ModelOption(
        "Custom OpenAI-compatible",
        "custom",
        "",
        "",
        "Manual",
    ),
]


def format_token_count(value):
    return format_number(value)


def format_usage_bar(stats):
    model = stats.get("model") or "not configured"
    mode = stats.get("permission_mode") or "auto"
    effort = stats.get("effort_mode") or "normal"
    last_total = stats.get("last_total_tokens", 0)
    session_total = stats.get("session_total_tokens", 0)
    context_percent = stats.get("context_used_percent", 0.0)
    speed = stats.get("last_tokens_per_second", 0.0)
    estimated = " est" if stats.get("last_estimated") else ""
    trimmed = " trimmed" if stats.get("history_omitted") else ""
    speed_value = f"{speed:.1f}/s" if speed > 0 else "n/a"

    return (
        f"[{THEME.suggestion}]model[/] {model}  "
        f"[#555555]|[/] [{THEME.warning}]mode[/] {mode}  "
        f"[#555555]|[/] [{THEME.warning}]effort[/] {effort}  "
        f"[#555555]|[/] [{THEME.suggestion}]last[/] {format_token_count(last_total)}"
        f"{estimated}  "
        f"[#555555]|[/] [{THEME.suggestion}]sess[/] {format_token_count(session_total)}  "
        f"[#555555]|[/] [{THEME.suggestion}]ctx[/] {context_percent:.1f}%"
        f"{trimmed}  "
        f"[#555555]|[/] [{THEME.success}]spd[/] {speed_value}"
    )


def current_model_env():
    file_values = {}

    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()

            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue

            key, value = stripped.split("=", 1)
            file_values[key.strip()] = value.strip().strip('"').strip("'")

    return {
        key: file_values.get(key, os.getenv(key, "")).strip()
        for key in MODEL_ENV_KEYS
    }


def write_model_env(values):
    ENV_PATH.touch(exist_ok=True)
    lines = ENV_PATH.read_text(encoding="utf-8").splitlines()
    pending = {
        key: values[key]
        for key in MODEL_ENV_KEYS
    }
    updated_lines = []

    for line in lines:
        stripped = line.strip()
        key = stripped.split("=", 1)[0].strip() if "=" in stripped else ""

        if key in pending and not stripped.startswith("#"):
            updated_lines.append(f"{key}={pending.pop(key)}")
        else:
            updated_lines.append(line)

    for key, value in pending.items():
        updated_lines.append(f"{key}={value}")

    ENV_PATH.write_text("\n".join(updated_lines) + "\n", encoding="utf-8")

    for key, value in values.items():
        os.environ[key] = value


class ConversationItem(ListItem):
    def __init__(self, conversation):
        self.conversation_id = conversation["id"]
        title = conversation["title"]
        updated_at = self.format_date(conversation["updated_at"])
        super().__init__(
            Label(
                f"{title}\n[dim]{updated_at}[/dim]",
                classes="conversation-option",
            )
        )

    @staticmethod
    def format_date(value):
        try:
            date = datetime.fromisoformat(value)
            return date.strftime("%b %d, %Y at %H:%M")
        except (TypeError, ValueError):
            return value


class ConversationScreen(ModalScreen):
    BINDINGS = [
        Binding("escape", "close", "Close", show=False),
        Binding("up", "move_selection(-1)", "Previous", show=False, priority=True),
        Binding("down", "move_selection(1)", "Next", show=False, priority=True),
        Binding("enter", "open_selected", "Open", show=False, priority=True),
    ]

    def __init__(self, conversations):
        super().__init__()
        self.conversations = conversations

    def compose(self) -> ComposeResult:
        items = [
            ConversationItem(conversation)
            for conversation in self.conversations
        ]

        with Container(id="conversation-dialog"):
            with Horizontal(id="conversation-dialog-header"):
                yield Label("Conversations", id="conversation-dialog-title")
            yield Label(
                f"{len(items)} saved conversation"
                f"{'' if len(items) == 1 else 's'}",
                id="conversation-dialog-help",
            )
            with Horizontal(id="conversation-search-row"):
                yield Input(
                    placeholder="Type to filter...",
                    id="conversation-search",
                )
            yield ListView(*items, id="conversation-list")
            yield Label(
                "No conversations found.",
                id="conversation-empty",
            )
            yield Label(
                "[b]Up/Down[/b] select    "
                "[b]Enter[/b] open    "
                "[b]Esc[/b] close",
                id="conversation-dialog-controls",
            )

    def action_close(self) -> None:
        self.dismiss(None)

    def on_mount(self) -> None:
        conversation_list = self.query_one("#conversation-list", ListView)
        conversation_list.index = 0
        self.query_one("#conversation-empty", Label).styles.display = "none"
        self.query_one("#conversation-search", Input).focus()

    def action_move_selection(self, direction: int) -> None:
        conversation_list = self.query_one("#conversation-list", ListView)
        item_count = len(conversation_list.children)

        if item_count == 0:
            return

        current_index = conversation_list.index or 0
        conversation_list.index = (current_index + direction) % item_count

    def action_open_selected(self) -> None:
        conversation_list = self.query_one("#conversation-list", ListView)
        selected_item = conversation_list.highlighted_child

        if selected_item is not None:
            self.dismiss(selected_item.conversation_id)

    async def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id != "conversation-search":
            return

        search_text = event.value.strip().lower()
        conversations = [
            conversation
            for conversation in self.conversations
            if search_text in conversation["title"].lower()
        ]
        conversation_list = self.query_one("#conversation-list", ListView)
        empty_message = self.query_one("#conversation-empty", Label)

        await conversation_list.clear()

        if not conversations:
            empty_message.styles.display = "block"
            return

        empty_message.styles.display = "none"
        await conversation_list.extend(
            ConversationItem(conversation)
            for conversation in conversations
        )
        conversation_list.index = 0

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        self.dismiss(event.item.conversation_id)


class ModelOptionItem(ListItem):
    def __init__(self, option):
        self.option = option
        price = "Free" if option.free else option.note
        line = option.name if not price else f"{option.name}\n[dim]{price}[/dim]"
        super().__init__(Label(line, classes="model-option"))


class ModelScreen(ModalScreen):
    BINDINGS = [
        Binding("escape", "close", "Close", show=False),
        Binding("ctrl+s", "save", "Save", show=False, priority=True),
    ]

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.step = "select"

    def compose(self) -> ComposeResult:
        items = [
            ModelOptionItem(option)
            for option in MODEL_OPTIONS
        ]

        with Container(id="model-dialog"):
            with Horizontal(id="model-dialog-header"):
                yield Label("Select model", id="model-dialog-title")
                yield Label("esc", id="model-dialog-escape")
            yield Label("", id="model-help")
            yield ListView(*items, id="model-list")
            yield Label("Provider", id="model-provider-label", classes="model-field-label")
            yield Input(id="model-provider")
            yield Label("Model", id="model-name-label", classes="model-field-label")
            yield Input(id="model-name")
            yield Label("API key", id="model-api-key-label", classes="model-field-label")
            yield Input(
                password=True,
                placeholder="Leave blank to keep the current key",
                id="model-api-key",
            )
            yield Label("Base URL", id="model-base-url-label", classes="model-field-label")
            yield Input(id="model-base-url")
            yield Label("", id="model-error")

    def action_close(self) -> None:
        self.dismiss(None)

    def on_mount(self) -> None:
        self.query_one("#model-list", ListView).index = 0
        self.query_one("#model-provider", Input).value = self.config.get(
            "AI_PROVIDER",
            "",
        )
        self.query_one("#model-name", Input).value = self.config.get(
            "AI_MODEL",
            "",
        )
        self.query_one("#model-base-url", Input).value = self.config.get(
            "AI_BASE_URL",
            "",
        )
        self.show_select_step()
        self.query_one("#model-list", ListView).focus()

    def set_form_display(self, display: str) -> None:
        for selector in (
            "#model-provider-label",
            "#model-provider",
            "#model-name-label",
            "#model-name",
            "#model-api-key-label",
            "#model-api-key",
            "#model-base-url-label",
            "#model-base-url",
            "#model-error",
        ):
            self.query_one(selector).styles.display = display

    def show_select_step(self) -> None:
        self.step = "select"
        self.query_one("#model-dialog-title", Label).update("Select model")
        self.query_one("#model-help", Label).update("")
        self.query_one("#model-list", ListView).styles.display = "block"
        self.set_form_display("none")

    def show_config_step(self) -> None:
        self.step = "config"
        self.query_one("#model-dialog-title", Label).update("Configure model")
        self.query_one("#model-help", Label).update("")
        self.query_one("#model-list", ListView).styles.display = "none"
        self.set_form_display("block")
        self.query_one("#model-api-key", Input).focus()

    def apply_option(self, option) -> None:
        self.query_one("#model-provider", Input).value = option.provider
        self.query_one("#model-name", Input).value = option.model
        self.query_one("#model-base-url", Input).value = option.base_url

        if option.api_key:
            self.query_one("#model-api-key", Input).value = option.api_key
        else:
            self.query_one("#model-api-key", Input).value = ""

        self.show_config_step()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        self.apply_option(event.item.option)

    def confirm_focused(self) -> None:
        focused = self.focused

        if self.step == "select" and isinstance(focused, ListView):
            selected_item = focused.highlighted_child

            if selected_item is not None:
                self.apply_option(selected_item.option)
            return

        self.action_save()

    def action_save(self) -> None:
        values = {
            "AI_PROVIDER": self.query_one("#model-provider", Input).value.strip(),
            "AI_MODEL": self.query_one("#model-name", Input).value.strip(),
            "AI_API_KEY": self.query_one("#model-api-key", Input).value.strip(),
            "AI_BASE_URL": self.query_one("#model-base-url", Input).value.strip(),
        }

        if not values["AI_API_KEY"]:
            values["AI_API_KEY"] = self.config.get("AI_API_KEY", "")

        missing = [
            key
            for key, value in values.items()
            if not value
        ]

        if missing:
            self.query_one("#model-error", Label).update(
                "Missing: " + ", ".join(missing)
            )
            return

        self.dismiss(values)


class MessageInput(TextArea):
    def visible_image_markers(self, text: str) -> list[str]:
        return IMAGE_MARKER_RE.findall(text or "")

    def text_without_image_markers(self, text: str) -> str:
        return IMAGE_MARKER_RE.sub("", text or "").strip()

    def image_paths_from_text(self, text: str) -> list[Path]:
        text = self.text_without_image_markers(text)

        if not text:
            return []

        direct_candidate = text.strip().strip("'\"")

        if direct_candidate.startswith("file://"):
            parsed = urlparse(direct_candidate)
            direct_candidate = unquote(parsed.path)

        direct_path = Path(direct_candidate).expanduser()

        if (
            direct_path.exists()
            and direct_path.is_file()
            and direct_path.suffix.lower() in IMAGE_SUFFIXES
        ):
            return [direct_path]

        candidates = []

        try:
            candidates.extend(shlex.split(text))
        except ValueError:
            candidates.extend(text.splitlines())

        if not candidates:
            candidates = text.splitlines()

        paths = []
        normalized_candidates = []

        for candidate in candidates:
            candidate = candidate.strip().strip("'\"")

            if not candidate:
                continue

            normalized_candidates.append(candidate)

            if candidate.startswith("file://"):
                parsed = urlparse(candidate)
                candidate = unquote(parsed.path)

            path = Path(candidate).expanduser()

            if (
                path.exists()
                and path.is_file()
                and path.suffix.lower() in IMAGE_SUFFIXES
            ):
                paths.append(path)

        if len(paths) != len(normalized_candidates):
            return []

        return paths

    def insert_attachments(self, attachments) -> None:
        if not attachments:
            return

        self.app.pending_attachments.extend(attachments)
        markers = " ".join(
            attachment.get("marker", "[attachment]")
            for attachment in attachments
        )
        self.insert(f" {markers}")

    def set_attachments(self, attachments) -> None:
        if not attachments:
            return

        self.app.pending_attachments.extend(attachments)
        markers = " ".join(
            attachment.get("marker", "[attachment]")
            for attachment in attachments
        )
        self.load_text(markers)
        self.move_cursor((0, len(markers)))

    def keep_only_image_markers(self) -> None:
        markers = self.visible_image_markers(self.text)

        if not markers:
            return

        text = " ".join(markers)
        self.load_text(text)
        self.move_cursor((0, len(text)))

    def pasted_text_marker(self, text: str) -> str:
        text = text or ""
        line_count = text.count("\n") + 1 if text else 0
        char_count = len(text.strip())

        if line_count >= LONG_PASTE_MIN_LINES:
            noun = "line" if line_count == 1 else "lines"
            return f"[{line_count} {noun} added]"

        if char_count >= LONG_PASTE_MIN_CHARS:
            return f"[{char_count} characters added]"

        return ""

    def clipboard_text(self, event: Paste) -> str:
        if event.text and event.text.strip():
            return event.text

        try:
            completed = subprocess.run(
                ["pbpaste"],
                capture_output=True,
                text=True,
                check=False,
            )
        except Exception:
            return ""

        return completed.stdout or ""

    async def _on_paste(self, event: Paste) -> None:
        app = self.app

        pasted_text = self.clipboard_text(event)

        if pasted_text.strip():
            image_paths = self.image_paths_from_text(pasted_text)

            if image_paths:
                self.insert_attachments(
                    app.image_attachments_from_paths(image_paths)
                )
                event.prevent_default()
                event.stop()
                return

            marker = self.pasted_text_marker(pasted_text)

            if marker:
                app.pending_attachments.append(
                    {
                        "id": uuid4().hex,
                        "kind": "text",
                        "marker": marker,
                        "content": pasted_text,
                        "line_count": pasted_text.count("\n") + 1,
                        "char_count": len(pasted_text),
                    }
                )
                if result := self._replace_via_keyboard(
                    marker,
                    *self.selection,
                ):
                    self.move_cursor(result.end_location)
                    self.focus()
                event.prevent_default()
                event.stop()
                return

            if result := self._replace_via_keyboard(
                pasted_text,
                *self.selection,
            ):
                self.move_cursor(result.end_location)
                self.focus()
            event.prevent_default()
            event.stop()
            return

        try:
            clipboard = ImageGrab.grabclipboard()
        except Exception:
            clipboard = None

        pasted_attachment = None

        if isinstance(clipboard, Image.Image):
            pasted_attachment = app.save_pasted_image(
                clipboard,
                marker=f"[Image #{len(app.pending_attachments) + 1}]",
            )
        elif isinstance(clipboard, list):
            for item in clipboard:
                candidate = Path(item)

                if (
                    candidate.exists()
                    and candidate.is_file()
                    and candidate.suffix.lower() in IMAGE_SUFFIXES
                ):
                    pasted_attachment = app.save_pasted_image(
                        candidate,
                        marker=f"[Image #{len(app.pending_attachments) + 1}]",
                    )
                    break

        if pasted_attachment is None:
            await super()._on_paste(event)
            return

        self.insert_attachments([pasted_attachment])
        event.prevent_default()
        event.stop()


class RecturyApp(App):
    CSS = APP_CSS
    ALLOW_SELECT = True
    COMMAND_MENU_VISIBLE_ROWS = 6
    CHAT_SCROLL_RETRY_DELAYS = (0.02, 0.08, 0.18, 0.35)
    CHAT_SCROLL_DELAYED_RETRY_DELAYS = (0.02, 0.08, 0.18, 0.35, 0.7)
    SPINNER_FRAMES = ["-", "\\", "|", "/"]
    THINKING_SYMBOLS = ["◌", "◎", "●", "◉"]
    THINKING_SYMBOL_MESSAGES = ["reasoning", "Thinking", "Thinking", "Thinking"]
    THINKING_MESSAGES = [
        "Thinking...",
        "Reasoning...",
        "Analyzing...",
        "Exploring...",
        "Inspecting...",
        "Searching...",
        "Reading...",
        "Understanding...",
        "Planning...",
        "Creating...",
        "Building...",
        "Generating...",
        "Writing...",
        "Editing...",
        "Refactoring...",
        "Optimizing...",
        "Comparing...",
        "Checking...",
        "Verifying...",
        "Testing...",
        "Computing...",
        "Connecting...",
        "Loading...",
        "Cooking...",
        "Tracing...",
        "Piecing together...",
        "Sketching...",
        "Forging...",
        "Sharpening...",
        "Assembling...",
        "Tuning...",
        "Weaving...",
        "Distilling...",
        "Finalizing...",
        "Preparing...",
    ]
    THINKING_DONE_MESSAGE = "Done."
    COMMANDS = [
        ("/help", "Show Rectury commands"),
        ("/conversations", "List saved conversations"),
        ("/models", "Select model and API key"),
        ("/open", "Open a conversation by ID"),
        ("/new", "Start a new conversation"),
        ("/clear", "Clear the terminal view"),
        ("/compact", "Summarize and reduce conversation context"),
        ("/init", "Create RECTURY.md project memory"),
        ("/index", "Build or inspect the project index"),
        ("/mode", "Show or change permission mode"),
        ("/max", "Toggle max effort for long projects"),
        ("/reference", "Manage read-only reference paths"),
        ("/hooks", "Create or show project hooks"),
        ("/history", "Show checkpointed file changes"),
        ("/undo", "Revert the latest checkpointed file change"),
        ("/approved-tools", "Show approvals for this session"),
        ("/cost", "Show total cost and duration of current session"),
        ("/bug", "Submit feedback about Rectury"),
        ("/doctor", "Show local configuration diagnostics"),
        ("/listen", "Activate speech recognition (macOS only)"),
        ("/pr-comments", "Get comments from a GitHub pull request"),
        ("/review", "Review a pull request"),
        ("/exit", "Exit Rectury"),
        ("/quit", "Exit Rectury"),
    ]
    BINDINGS = [
        Binding("enter", "submit_message", "Send", show=False, priority=True),
        Binding("tab", "complete_command", "Complete command", show=False),
        Binding("ctrl+l", "insert_newline", "New line", show=False, priority=True),
        Binding("ctrl+a", "select_input_all", "Select all", show=False, priority=True),
        Binding("ctrl+c", "cancel_response", "Cancel", show=False, priority=True),
    ]

    def compose(self) -> ComposeResult:
        welcome_panel = Vertical(
            Label("Rectury Agent  [dim]Experimental[/dim]", id="welcome-title"),
            Label(
                "Rectury can inspect files, use tools, run tasks, and help you "
                "work across your system from the terminal.",
                id="welcome-copy",
            ),
            Label(
                "Review commands before execution and use Rectury only in "
                "trusted projects.",
                id="welcome-note",
            ),
            Label(" "),
            Label("New conversation", id="conversation-title"),
            Label(" "),
            Label("Workspace", id="agent-name"),
            Label(f"~ {Path.cwd()}", id="status"),
            id="welcome-panel",
        )
       
        yield VerticalScroll(
            welcome_panel,
            id="chat",
        )
        with Horizontal(id="command-menu-row"):
            yield Static("", id="command-menu-spacer")
            with VerticalScroll(id="command-menu"):
                for _ in range(self.COMMAND_MENU_VISIBLE_ROWS):
                    yield Label(classes="command-option")
        with Horizontal(id="input-row"):
            yield Static(">", id="prompt")
            yield MessageInput(
                placeholder="Ask anything...",
                id="message-input",
                soft_wrap=True,
                show_line_numbers=False,
                highlight_cursor_line=False,
            )
            yield Label(
                "",
                id="permission-input",
                markup=True,
            )
        yield Label("", id="usage-bar", markup=True)

    def set_status(self, status: str) -> None:
        self.query_one("#status", Label).update(f"Status: {status}")

    @work(thread=True)
    def run_direct_command_in_background(
        self,
        command,
        thinking_label,
        spinner_timer,
    ):
        arguments = {"command": command, "cwd": ".", "timeout": 30}
        event_key = "direct:run_command"
        result = None

        try:
            self.call_from_thread(
                self.handle_agent_event,
                {
                    "type": "tool_started",
                    "tool_call_id": event_key,
                    "event_key": event_key,
                    "tool": "run_command",
                    "arguments": arguments,
                },
            )

            validation = validate_command(command)

            if not validation["ok"]:
                result = {
                    "error": validation["error"],
                    "code": validation.get("code", "invalid_command"),
                }
            else:
                preview = {
                    "success": True,
                    "tool": "run_command",
                    "arguments": arguments,
                    "safe": validation["safe"],
                    "prefix": validation.get("prefix", ""),
                }
                approved = self.command_is_allowed(
                    arguments,
                    preview,
                )

                if approved:
                    self.run_and_display_hooks(
                        "before_command",
                        {
                            "tool": "run_command",
                            "command": command,
                        },
                    )
                    self.chat_session.command_cancel_requested = Event()
                    result = None

                    for command_event in run_command_stream(
                        state=self.chat_session.state,
                        cancel_event=self.chat_session.command_cancel_requested,
                        on_process=self.chat_session.set_active_command_process,
                        **arguments,
                    ):
                        if command_event.get("type") == "output":
                            self.call_from_thread(
                                self.handle_agent_event,
                                {
                                    "type": "tool_update",
                                    "tool_call_id": event_key,
                                    "event_key": event_key,
                                    "tool": "run_command",
                                    "arguments": arguments,
                                    "stream": command_event["stream"],
                                    "content": command_event["content"],
                                    "duration_ms": command_event.get(
                                        "duration_ms"
                                    ),
                                },
                            )
                        elif command_event.get("type") == "result":
                            result = command_event["result"]

                    if result is None:
                        result = {"error": "command produced no result."}

                    self.run_and_display_hooks(
                        "after_command",
                        {
                            "tool": "run_command",
                            "command": command,
                            "exit_code": result.get("returncode", ""),
                        },
                    )
                else:
                    result = {
                        "error": (
                            "The command was not allowed in the current "
                            f"{self.permission_mode} permission mode."
                        ),
                        "code": (
                            "plan_mode_blocks_tool"
                            if self.permission_mode == "plan"
                            else "permission_denied"
                        ),
                        "rejected": True,
                        "tool": "run_command",
                    }

            self.call_from_thread(
                self.handle_agent_event,
                {
                    "type": "tool_finished",
                    "tool_call_id": event_key,
                    "event_key": event_key,
                    "tool": "run_command",
                    "arguments": arguments,
                    "result": result,
                    "awaiting_model": False,
                },
            )
        except Exception as error:
            self.call_from_thread(
                self.show_system_message,
                f"Command failed: {error}",
            )
        finally:
            self.chat_session.command_cancel_requested = None
            self.chat_session.active_command_process = None
            self.call_from_thread(spinner_timer.stop)
            if self.active_spinner_timer is spinner_timer:
                self.active_spinner_timer = None
            self.call_from_thread(
                self.finish_thinking_label,
                thinking_label,
            )
            self.call_from_thread(
                self.finish_background_response,
            )

    def run_and_display_hooks(self, event, context):
        hook_results = run_hooks(
            self.chat_session.state,
            event,
            context,
            self.permission_mode,
        )

        for index, hook_result in enumerate(hook_results):
            event_key = f"direct:hook:{event}:{index}"
            arguments = {
                "event": event,
                "name": hook_result.get("name", event),
                "command": hook_result.get("command", ""),
            }
            self.call_from_thread(
                self.handle_agent_event,
                {
                    "type": "tool_started",
                    "tool_call_id": event_key,
                    "event_key": event_key,
                    "tool": "hook",
                    "arguments": arguments,
                },
            )
            self.call_from_thread(
                self.handle_agent_event,
                {
                    "type": "tool_finished",
                    "tool_call_id": event_key,
                    "event_key": event_key,
                    "tool": "hook",
                    "arguments": arguments,
                    "result": hook_result,
                    "awaiting_model": False,
                },
            )

    @work(thread=True)
    def send_message_in_background(
        self,
        user_message,
        thinking_label,
        spinner_timer,
        response_id,
    ):
        try:
            for event in self.chat_session.send_message(user_message):
                if response_id != self.active_response_id:
                    break

                self.call_from_thread(
                    self.handle_agent_event,
                    event,
                    response_id,
                )
        except Exception as error:
            if response_id == self.active_response_id:
                self.call_from_thread(
                    self.show_system_message,
                    f"Request failed: {error}",
                )
        finally:
            self.call_from_thread(spinner_timer.stop)
            if self.active_spinner_timer is spinner_timer:
                self.active_spinner_timer = None
            if response_id == self.active_response_id:
                self.active_response_id = None
                self.active_response_worker = None
                self.call_from_thread(
                    self.finish_thinking_label,
                    thinking_label,
                )
                self.call_from_thread(
                    self.finish_background_response,
                )

    def start_hidden_background_message(self, user_message):
        self.response_in_progress = True
        chat = self.query_one("#chat", VerticalScroll)
        self.active_assistant_message = None
        self.active_assistant_content = ""
        self.tool_messages = {}

        thinking_label, spinner_timer = self.start_thinking_indicator(chat)
        response_id = uuid4().hex
        self.active_response_id = response_id

        self.schedule_chat_scroll()
        self.active_response_worker = self.send_message_in_background(
            user_message,
            thinking_label,
            spinner_timer,
            response_id,
        )

    def finish_background_response(self):
        self.response_in_progress = False
        self.query_one("#conversation-title", Label).update(
            self.chat_session.title
        )
        self.update_usage_bar()
        message_input = self.query_one("#message-input", TextArea)
        message_input.focus()
        self.schedule_chat_scroll(delayed=True)

    def install_selection_bug_workaround(self, screen=None):
        screen = screen or self.screen

        if getattr(screen, "_rectury_selection_bug_patched", False):
            return screen

        original_get_widget_and_offset_at = screen.get_widget_and_offset_at

        def get_widget_and_offset_at(x, y):
            widget, offset = original_get_widget_and_offset_at(x, y)

            if widget is screen and offset is not None:
                return widget, None

            return widget, offset

        screen.get_widget_and_offset_at = get_widget_and_offset_at
        screen._rectury_selection_bug_patched = True
        return screen

    def copy_selected_text(self):
        try:
            selected_text = self.screen.get_selected_text()
        except Exception:
            selected_text = None

        selected_text = selected_text or ""

        if not selected_text.strip():
            return

        if selected_text == self.last_copied_selection:
            return

        self.copy_text_to_clipboard(selected_text)
        self.last_copied_selection = selected_text

    def copy_text_to_clipboard(self, text):
        self.copy_to_clipboard(text)

        clipboard_commands = []

        if shutil.which("pbcopy"):
            clipboard_commands.append(["pbcopy"])
        if shutil.which("wl-copy"):
            clipboard_commands.append(["wl-copy"])
        if shutil.which("xclip"):
            clipboard_commands.append(["xclip", "-selection", "clipboard"])
        if shutil.which("xsel"):
            clipboard_commands.append(["xsel", "--clipboard", "--input"])

        for command in clipboard_commands:
            try:
                subprocess.run(
                    command,
                    input=text,
                    text=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=1,
                    check=False,
                )
                return True
            except (OSError, subprocess.SubprocessError):
                continue

        return False

    def schedule_selected_text_copy(self):
        self.copy_selected_text()
        self.set_timer(0.03, self.copy_selected_text)
        self.set_timer(0.12, self.copy_selected_text)

    def on_mouse_up(self, event: MouseUp) -> None:
        self.schedule_selected_text_copy()

    def on_text_selected(self, event: TextSelected) -> None:
        self.schedule_selected_text_copy()

    def update_usage_bar(self, stats=None):
        if stats is None:
            stats = getattr(self.chat_session, "usage_stats", {})

        stats = {
            **stats,
            "permission_mode": getattr(
                self,
                "permission_mode",
                "auto",
            ),
            "effort_mode": getattr(
                self.chat_session,
                "effort_mode",
                "normal",
            ),
        }
        self.query_one("#usage-bar", Label).update(
            format_usage_bar(stats)
        )

    def hide_thinking_label(self, thinking_label=None):
        thinking_label = thinking_label or self.active_thinking_label

        if thinking_label is None:
            return

        thinking_label.styles.display = "none"

    def finish_thinking_label(self, thinking_label=None):
        thinking_label = thinking_label or self.active_thinking_label

        if thinking_label is None:
            return

        if thinking_label.styles.display != "none":
            thinking_label.update(
                f"[{THEME.assistant}]◉[/] [dim]{self.THINKING_DONE_MESSAGE}[/]"
            )
            self.set_timer(0.25, lambda: self.hide_thinking_label(thinking_label))
            return

        self.hide_thinking_label(thinking_label)

    def scroll_chat_to_end(self):
        chat = self.query_one("#chat", VerticalScroll)
        chat.anchor(True)
        chat.scroll_end(
            animate=False,
            force=True,
            immediate=True,
            x_axis=False,
        )
        chat.scroll_to(
            y=chat.max_scroll_y,
            animate=False,
            force=True,
            immediate=True,
            release_anchor=False,
        )

    def run_scheduled_chat_scroll(self):
        self.chat_scroll_queued = False
        self.scroll_chat_to_end()

    def run_retry_chat_scroll(self, final=False):
        self.scroll_chat_to_end()

        if final:
            self.chat_scroll_retry_queued = False

    def schedule_chat_scroll(self, delayed=False):
        if not getattr(self, "chat_scroll_queued", False):
            self.chat_scroll_queued = True
            self.call_after_refresh(self.run_scheduled_chat_scroll)

        if delayed:
            delays = self.CHAT_SCROLL_DELAYED_RETRY_DELAYS
        elif not getattr(self, "chat_scroll_retry_queued", False):
            self.chat_scroll_retry_queued = True
            delays = self.CHAT_SCROLL_RETRY_DELAYS
        else:
            return

        for index, delay in enumerate(delays):
            final = index == len(delays) - 1
            self.set_timer(
                delay,
                lambda final=final: self.run_retry_chat_scroll(final),
            )

    def show_thinking_label(self):
        if self.active_thinking_label is None:
            return

        self.thinking_started_at = time.monotonic()
        self.thinking_tick = 0
        self.active_thinking_label.styles.display = "block"
        self.update_spinner(self.active_thinking_label)

    def thinking_markup(self):
        symbol_index = self.thinking_tick % len(self.THINKING_SYMBOLS)
        frame = self.THINKING_SYMBOLS[symbol_index]
        message = self.THINKING_SYMBOL_MESSAGES[symbol_index]
        elapsed_seconds = 0

        if self.thinking_started_at is not None:
            elapsed_ms = (time.monotonic() - self.thinking_started_at) * 1000
            elapsed_seconds = max(0, int(elapsed_ms // 1000))
            if elapsed_ms >= 1000:
                message_index = int((elapsed_ms - 1000) // 1400) % len(
                    self.THINKING_MESSAGES
                )
                message = self.THINKING_MESSAGES[message_index]

        left_plain = f"{frame} {message}"
        right_plain = f"{elapsed_seconds}s  Esc interrupt"
        content_width = max(36, getattr(self.size, "width", 80) - 10)
        gap = max(2, content_width - len(left_plain) - len(right_plain))
        return (
            f"[{THEME.assistant}]{frame}[/] [dim]{message}[/]"
            f"{' ' * gap}"
            f"[dim]{elapsed_seconds}s[/] [reverse] Esc [/reverse] "
            f"[dim]interrupt[/]"
        )

    def start_thinking_indicator(self, chat):
        self.spinner_index = 0
        self.thinking_tick = 0
        self.thinking_started_at = time.monotonic()
        thinking_label = Label(
            self.thinking_markup(),
            classes="assistant-message",
            markup=True,
        )
        chat.mount(thinking_label)
        self.active_thinking_label = thinking_label
        spinner_timer = self.set_interval(
            0.22,
            lambda: self.update_spinner(thinking_label),
        )
        self.active_spinner_timer = spinner_timer
        return thinking_label, spinner_timer

    def mount_before_thinking(self, widget):
        chat = self.query_one("#chat", VerticalScroll)

        if (
            self.active_thinking_label is not None
            and self.active_thinking_label.is_mounted
        ):
            chat.mount(
                widget,
                before=self.active_thinking_label,
            )
        else:
            chat.mount(widget)

    def permission_key(self, tool_name, arguments, preview):
        return build_permission_key(tool_name, arguments, preview)

    def request_tool_permission(self, tool_name, arguments, preview):
        decision = can_use_tool(
            tool_name,
            arguments,
            preview,
            permission_mode=self.permission_mode,
            approved_permission_keys=self.approved_permission_keys,
            allow_edits_for_session=self.allow_edits_for_session,
            workspace=self.chat_session.state.workspace,
        )
        key = decision.permission_key

        if decision.allowed:
            if decision.reason == "project_approval" and key:
                self.approved_permission_keys.add(key)
            return True

        if decision.denied:
            return False

        completed = Event()
        prompt_decision = {"value": "reject"}

        self.call_from_thread(
            self.show_inline_permission,
            tool_name,
            arguments,
            preview,
            key,
            completed,
            prompt_decision,
        )
        completed.wait()
        return prompt_decision["value"] in {"once", "session"}

    def command_is_allowed(self, arguments, preview):
        return self.request_tool_permission(
            "run_command",
            arguments,
            preview,
        )

    def show_inline_permission(
        self,
        tool_name,
        arguments,
        preview,
        key,
        completed,
        decision,
    ):
        chat = self.query_one("#chat", VerticalScroll)
        permission_message = PermissionMessage(
            tool_name,
            arguments,
            preview,
        )
        self.mount_before_thinking(permission_message)
        self.hide_thinking_label()

        self.active_permission = {
            "completed": completed,
            "decision": decision,
            "message": permission_message,
            "tool_name": tool_name,
            "key": key,
        }
        self.permission_index = 0
        self.query_one("#message-input", TextArea).styles.display = "none"
        self.query_one("#prompt", Static).styles.display = "none"
        self.query_one(
            "#permission-input",
            Label,
        ).styles.display = "block"
        input_row = self.query_one("#input-row", Horizontal)
        input_row.styles.layout = "vertical"
        input_row.styles.height = 5
        self.query_one("#permission-input", Label).styles.height = 5
        self.render_permission_options()
        self.schedule_chat_scroll()

    def render_permission_options(self):
        tool_name = (
            self.active_permission.get("tool_name")
            if self.active_permission
            else "tool"
        )
        session_label = (
            "Yes, don't ask again for file edits this session"
            if tool_name in {"edit_file", "write_file"}
            else "Yes, don't ask again in this project"
            if tool_name == "run_command"
            else "Yes, don't ask again for similar requests"
        )
        options = [
            "Yes, allow once",
            session_label,
            "No, reject this request",
        ]
        lines = []

        for index, option in enumerate(options):
            if index == self.permission_index:
                lines.append(f"[bold]❯ {option}[/bold]")
            else:
                lines.append(f"  [dim]{option}[/dim]")

        lines.append(
            "\n[dim]↑/↓ select  Enter confirm  Esc reject[/dim]"
        )
        self.query_one("#permission-input", Label).update(
            "\n".join(lines)
        )

    def resolve_inline_permission(self, decision=None):
        if self.active_permission is None:
            return

        decisions = ["once", "session", "reject"]
        selected_decision = decision or decisions[self.permission_index]
        permission = self.active_permission
        permission["decision"]["value"] = selected_decision

        if selected_decision == "session":
            if permission["tool_name"] in {"edit_file", "write_file"}:
                self.allow_edits_for_session = True

            if permission["tool_name"] == "run_command":
                approve_command(
                    self.chat_session.state.workspace,
                    permission["key"],
                )

            self.approved_permission_keys.add(permission["key"])

        permission["message"].finish(selected_decision)
        self.active_permission = None
        self.query_one(
            "#permission-input",
            Label,
        ).styles.display = "none"
        self.query_one("#message-input", TextArea).styles.display = "block"
        self.query_one("#prompt", Static).styles.display = "block"
        input_row = self.query_one("#input-row", Horizontal)
        input_row.styles.layout = "horizontal"
        input_row.styles.height = 1
        self.call_after_refresh(self.resize_message_input)
        self.query_one("#message-input", TextArea).focus()
        permission["completed"].set()
        if self.response_in_progress:
            self.show_thinking_label()
        self.schedule_chat_scroll()

    def handle_agent_event(self, event, response_id=None):
        if response_id is not None and response_id != self.active_response_id:
            return

        chat = self.query_one("#chat", VerticalScroll)
        event_type = event["type"]

        if event_type == "content":
            if self.active_thinking_label is not None:
                self.hide_thinking_label(
                    self.active_thinking_label
                )

            if self.active_assistant_message is None:
                self.active_assistant_content = ""
                self.active_assistant_message = Markdown(
                    "",
                    classes="assistant-message",
                )
                self.mount_before_thinking(
                    self.active_assistant_message
                )

            self.active_assistant_content += event["content"]
            self.active_assistant_message.update(
                self.active_assistant_content
            )

        elif event_type == "tool_started":
            self.hide_thinking_label()
            self.active_assistant_message = None
            self.active_assistant_content = ""
            tool_message = self.tool_messages.get(
                event["event_key"]
            )

            if tool_message is None:
                tool_message = ToolMessage(
                    event["tool"],
                    event["arguments"],
                )
                self.tool_messages[event["event_key"]] = tool_message
                self.mount_before_thinking(tool_message)
            else:
                tool_message.start(event["arguments"])

        elif event_type == "tool_finished":
            tool_message = self.tool_messages.pop(
                event["event_key"],
                None,
            )

            if tool_message is not None:
                tool_message.finish(event["result"])

            if event.get("awaiting_model", True):
                self.show_thinking_label()
            else:
                self.hide_thinking_label()

        elif event_type == "tool_update":
            self.hide_thinking_label()
            tool_message = self.tool_messages.get(event["event_key"])

            if tool_message is not None:
                tool_message.append_stream_output(
                    event.get("stream", "stdout"),
                    event.get("content", ""),
                    event.get("duration_ms"),
                )

        elif event_type == "usage":
            self.update_usage_bar(event["stats"])

        self.schedule_chat_scroll()

    def attachment_store_dir(self) -> Path:
        path = Path.home() / ".rectury" / "attachments"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def save_pasted_image(self, image_or_path, marker="[Image #1]"):
        attachment_id = uuid4().hex

        if isinstance(image_or_path, Image.Image):
            target_path = self.attachment_store_dir() / f"{attachment_id}.png"
            image_or_path.save(target_path, format="PNG")
            mime_type = "image/png"
        else:
            source_path = Path(image_or_path)
            suffix = source_path.suffix.lower() or ".png"
            target_path = self.attachment_store_dir() / f"{attachment_id}{suffix}"
            shutil.copy2(image_or_path, target_path)
            mime_type = mimetypes.guess_type(str(target_path))[0] or "image/png"

        return {
            "id": attachment_id,
            "kind": "image",
            "marker": marker,
            "path": str(target_path),
            "mime_type": mime_type,
        }

    def image_attachments_from_paths(self, image_paths):
        return [
            self.save_pasted_image(
                image_path,
                marker=f"[Image #{len(self.pending_attachments) + index + 1}]",
            )
            for index, image_path in enumerate(image_paths)
        ]

    def screenshot_candidate_paths(self):
        paths = []
        home = Path.home()
        desktop = home / "Desktop"

        if desktop.exists():
            for pattern in [
                "Captura de pantalla*.png",
                "Screenshot*.png",
                "Screen Shot*.png",
            ]:
                paths.extend(desktop.glob(pattern))

        temporary_items = Path("/var/folders")

        if temporary_items.exists():
            for path in temporary_items.glob(
                "*/*/*/T/TemporaryItems/NSIRD_screencaptureui_*/*.png"
            ):
                paths.append(path)

        return [
            path
            for path in paths
            if path.exists()
            and path.is_file()
            and path.suffix.lower() in IMAGE_SUFFIXES
        ]

    def snapshot_screenshot_paths(self):
        return {str(path) for path in self.screenshot_candidate_paths()}

    def poll_recent_screenshots(self) -> None:
        if self.response_in_progress:
            return

        if not self.focused or getattr(self.focused, "id", None) != "message-input":
            return

        if not isinstance(self.focused, MessageInput):
            return

        now = time.time()
        new_paths = []

        for path in self.screenshot_candidate_paths():
            path_key = str(path)

            if path_key in self.seen_screenshot_paths:
                continue

            self.seen_screenshot_paths.add(path_key)

            try:
                age = now - path.stat().st_mtime
            except OSError:
                continue

            if age <= 20:
                new_paths.append(path)

        if not new_paths:
            return

        new_paths.sort(key=lambda path: path.stat().st_mtime)
        self.focused.insert_attachments(
            self.image_attachments_from_paths(new_paths[-1:])
        )
        self.call_after_refresh(self.resize_message_input)

    def render_user_message(self, text: str, attachments=None):
        attachments = attachments or []
        lines = [text] if text else []

        if attachments:
            image_count = sum(
                1 for attachment in attachments
                if attachment.get("kind") == "image"
            )
            text_attachments = [
                attachment
                for attachment in attachments
                if attachment.get("kind") == "text"
            ]
            if image_count:
                noun = "image" if image_count == 1 else "images"
                lines.append(f"[{format_number(image_count)} {noun} attached]")
            for attachment in text_attachments:
                line_count = attachment.get("line_count", 0)
                char_count = attachment.get("char_count", 0)

                if line_count:
                    noun = "line" if line_count == 1 else "lines"
                    lines.append(f"[{format_number(line_count)} {noun} attached]")
                elif char_count:
                    lines.append(f"[{format_number(char_count)} characters attached]")

        return Label("\n".join(lines), classes="user-message")

    def update_spinner(self, thinking_label):
        if thinking_label is None:
            return

        thinking_label.update(self.thinking_markup())
        self.thinking_tick = (self.thinking_tick + 1) % len(
            self.THINKING_SYMBOLS
        )
        self.spinner_index = (self.spinner_index + 1) % len(self.SPINNER_FRAMES)
    
    def action_insert_newline(self) -> None:
        if self.active_permission is not None:
            return

        message_input = self.query_one("#message-input", TextArea)
        message_input.insert("\n")

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        if event.text_area.id == "message-input":
            if self.converting_dropped_images:
                self.converting_dropped_images = False
                self.call_after_refresh(self.resize_message_input)
                self.update_command_menu(event.text_area.text)
                return

            if isinstance(event.text_area, MessageInput):
                image_paths = event.text_area.image_paths_from_text(
                    event.text_area.text
                )

                if image_paths and event.text_area.visible_image_markers(
                    event.text_area.text
                ):
                    self.converting_dropped_images = True
                    event.text_area.keep_only_image_markers()
                    self.call_after_refresh(self.resize_message_input)
                    self.update_command_menu(event.text_area.text)
                    return

                if image_paths:
                    self.converting_dropped_images = True
                    event.text_area.set_attachments(
                        self.image_attachments_from_paths(image_paths)
                    )

            self.call_after_refresh(self.resize_message_input)
            self.update_command_menu(event.text_area.text)
            self.set_timer(0.05, self.convert_dropped_images_if_ready)

    def convert_dropped_images_if_ready(self) -> None:
        try:
            message_input = self.query_one("#message-input", MessageInput)
        except Exception:
            return

        if self.converting_dropped_images:
            return

        image_paths = message_input.image_paths_from_text(message_input.text)

        if not image_paths:
            return

        self.converting_dropped_images = True

        if message_input.visible_image_markers(message_input.text):
            message_input.keep_only_image_markers()
        else:
            message_input.set_attachments(
                self.image_attachments_from_paths(image_paths)
            )

        self.call_after_refresh(self.resize_message_input)
        self.update_command_menu(message_input.text)

    def on_paste(self, event: Paste) -> None:
        if not self.focused or getattr(self.focused, "id", None) != "message-input":
            return

        if not isinstance(self.focused, MessageInput):
            return

        image_paths = self.focused.image_paths_from_text(event.text)

        if not image_paths:
            return

        self.focused.set_attachments(
            self.image_attachments_from_paths(image_paths)
        )
        event.prevent_default()
        event.stop()

    def matching_commands(self, text: str):
        command_text = text.strip().lower()

        if not command_text.startswith("/") or " " in command_text:
            return []

        return [
            command
            for command in self.COMMANDS
            if command[0].startswith(command_text)
        ]

    def update_command_menu(self, text: str) -> None:
        command_menu_row = self.query_one("#command-menu-row", Horizontal)
        command_options = list(self.query(".command-option"))
        commands = self.matching_commands(text)
        command_text = text.strip().lower()

        if not commands:
            command_menu_row.styles.display = "none"
            self.command_index = 0
            self.command_scroll_offset = 0
            self.command_menu_text = ""
            return

        if command_text != self.command_menu_text:
            self.command_index = 0
            self.command_scroll_offset = 0
            self.command_menu_text = command_text

        self.command_index = min(self.command_index, len(commands) - 1)
        visible_rows = max(1, min(len(command_options), self.COMMAND_MENU_VISIBLE_ROWS))

        if self.command_index < self.command_scroll_offset:
            self.command_scroll_offset = self.command_index
        elif self.command_index >= self.command_scroll_offset + visible_rows:
            self.command_scroll_offset = self.command_index - visible_rows + 1

        max_offset = max(0, len(commands) - visible_rows)
        self.command_scroll_offset = max(
            0,
            min(self.command_scroll_offset, max_offset),
        )
        command_width = max(len(name) for name, _ in self.COMMANDS)

        for index, option in enumerate(command_options):
            command_index = self.command_scroll_offset + index

            if index >= visible_rows or command_index >= len(commands):
                option.styles.display = "none"
                option.remove_class("selected")
                continue

            name, description = commands[command_index]
            option.update(f"{name:<{command_width}}  {description}")
            option.styles.display = "block"

            if command_index == self.command_index:
                option.add_class("selected")
            else:
                option.remove_class("selected")

        command_menu_row.styles.display = "block"

    def selected_command(self):
        message_input = self.query_one("#message-input", TextArea)
        commands = self.matching_commands(message_input.text)

        if not commands:
            return None

        self.command_index = min(self.command_index, len(commands) - 1)
        return commands[self.command_index][0]

    def action_complete_command(self) -> None:
        if self.active_permission is not None:
            return

        message_input = self.query_one("#message-input", TextArea)
        command = self.selected_command()

        if command is None:
            return

        if command == "/open":
            command += " "

        message_input.clear()
        message_input.insert(command)

    def on_key(self, event: Key) -> None:
        if isinstance(self.screen, (ConversationScreen, ModelScreen)):
            return

        if event.key == "escape" and self.response_in_progress:
            self.action_cancel_response()
            event.prevent_default()
            event.stop()
            return

        if self.active_permission is not None:
            if event.key == "up":
                self.permission_index = (
                    self.permission_index - 1
                ) % 3
                self.render_permission_options()
            elif event.key == "down":
                self.permission_index = (
                    self.permission_index + 1
                ) % 3
                self.render_permission_options()
            elif event.key == "escape":
                self.resolve_inline_permission("reject")
            else:
                return

            event.prevent_default()
            event.stop()
            return

        message_input = self.query_one("#message-input", TextArea)

        if event.is_printable and not message_input.has_focus:
            message_input.focus()
            message_input.insert(event.character or "")
            event.prevent_default()
            event.stop()
            return

        command_menu_row = self.query_one("#command-menu-row", Horizontal)

        if command_menu_row.styles.display == "none":
            return

        commands = self.matching_commands(
            self.query_one("#message-input", TextArea).text
        )

        if event.key == "up":
            self.command_index = (self.command_index - 1) % len(commands)
        elif event.key == "down":
            self.command_index = (self.command_index + 1) % len(commands)
        elif event.key == "escape":
            command_menu_row.styles.display = "none"
            event.prevent_default()
            event.stop()
            return
        else:
            return

        self.update_command_menu(
            self.query_one("#message-input", TextArea).text
        )
        event.prevent_default()
        event.stop()

    def resize_message_input(self) -> None:
        if self.active_permission is not None:
            return

        message_input = self.query_one("#message-input", TextArea)
        input_row = self.query_one("#input-row", Horizontal)

        content_height = max(1, min(6, message_input.wrapped_document.height))

        message_input.styles.height = content_height
        input_row.styles.height = content_height

        if self.response_in_progress:
            self.schedule_chat_scroll(delayed=True)

    def show_system_message(self, content: str) -> None:
        chat = self.query_one("#chat", VerticalScroll)
        chat.mount(Markdown(content, classes="assistant-message"))
        self.schedule_chat_scroll()

    def clear_conversation_messages(self) -> None:
        chat = self.query_one("#chat", VerticalScroll)
        chat.remove_children(
            ".user-message, .assistant-message, .tool-message, .permission-message"
        )

    def render_conversation_messages(self) -> None:
        chat = self.query_one("#chat", VerticalScroll)
        saved_tool_messages = {}

        for message in self.chat_session.messages:
            role = message.get("role")
            content = message.get("content")

            if role == "user":
                attachments = message.get("attachments", []) or []

                if content or attachments:
                    chat.mount(
                        self.render_user_message(
                            str(content or ""),
                            attachments,
                        )
                    )
            elif role == "assistant":
                if content:
                    chat.mount(
                        Markdown(
                            content,
                            classes="assistant-message",
                        )
                    )

                for tool_call in message.get("tool_calls", []):
                    function = tool_call.get("function", {})

                    try:
                        arguments = json.loads(
                            function.get("arguments") or "{}"
                        )
                    except (TypeError, ValueError):
                        arguments = {}

                    tool_message = ToolMessage(
                        function.get("name", "tool"),
                        arguments,
                    )
                    saved_tool_messages[tool_call.get("id")] = tool_message
                    chat.mount(tool_message)
            elif role == "tool":
                tool_message = saved_tool_messages.pop(
                    message.get("tool_call_id"),
                    None,
                )

                if tool_message is None:
                    continue

                result = message.get("display_result")

                if result is None:
                    try:
                        result = json.loads(content or "{}")
                    except (TypeError, ValueError):
                        result = {"error": content or "Invalid saved tool result."}

                tool_message.finish(result)

        for tool_message in saved_tool_messages.values():
            tool_message.finish(
                {"error": "This saved tool call has no result."}
            )

        self.schedule_chat_scroll()

    def show_conversation_menu(self) -> None:
        conversations = self.chat_session.get_conversations()

        if not conversations:
            self.show_system_message("No saved conversations found.")
            return

        self.query_one(
            "#command-menu-row",
            Horizontal,
        ).styles.display = "none"
        screen = self.install_selection_bug_workaround(
            ConversationScreen(conversations)
        )
        self.push_screen(screen, self.open_selected_conversation)

    def show_model_menu(self) -> None:
        self.query_one(
            "#command-menu-row",
            Horizontal,
        ).styles.display = "none"
        screen = self.install_selection_bug_workaround(
            ModelScreen(current_model_env())
        )
        self.push_screen(screen, self.apply_model_config)

    def apply_model_config(self, values) -> None:
        self.query_one("#message-input", TextArea).focus()

        if values is None:
            return

        try:
            write_model_env(values)
            self.chat_session.reload_client()
        except Exception as error:
            self.show_system_message(f"Could not update model: {error}")
            return

        self.show_system_message(
            "Model updated: "
            f"{self.chat_session.config.provider} / "
            f"{self.chat_session.config.model}"
        )

    def open_selected_conversation(self, conversation_id) -> None:
        self.query_one("#message-input", TextArea).focus()

        if conversation_id is None:
            return

        if not self.chat_session.open_conversation(conversation_id):
            self.show_system_message("Conversation not found.")
            return

        self.clear_conversation_messages()
        self.query_one("#conversation-title", Label).update(
            self.chat_session.title
        )
        self.render_conversation_messages()

    def handle_command(self, user_message: str) -> bool:
        command_parts = user_message.split(maxsplit=1)
        command = command_parts[0].lower()

        if command in {"/exit", "/quit"}:
            self.exit()
            return True

        if command == "/help":
            command_width = max(len(name) for name, _ in self.COMMANDS)
            self.show_system_message(
                "Available commands:\n"
                + "\n".join(
                    f"{name:<{command_width}}  {description}"
                    for name, description in self.COMMANDS
                )
            )
            return True

        if command == "/conversations":
            self.show_conversation_menu()
            return True

        if command == "/models":
            self.show_model_menu()
            return True

        if command == "/new":
            self.chat_session.new_conversation()
            self.chat_session.set_permission_mode(self.permission_mode)
            self.clear_conversation_messages()
            self.query_one("#conversation-title", Label).update(
                self.chat_session.title
            )
            self.show_system_message("Started a new conversation.")
            return True

        if command == "/clear":
            self.clear_conversation_messages()
            return True

        if command == "/compact":
            success, message = self.chat_session.compact_conversation()

            if success:
                self.clear_conversation_messages()
                self.query_one("#conversation-title", Label).update(
                    self.chat_session.title
                )

            self.show_system_message(message)
            return True

        if command == "/init":
            memory_path = Path.cwd() / "RECTURY.md"

            if memory_path.exists():
                self.show_system_message("RECTURY.md already exists.")
                return True

            memory_path.write_text(
                "# RECTURY.md\n\n"
                "Project notes for Rectury.\n\n"
                "## Commands\n\n"
                "- Add build, lint, and test commands here.\n\n"
                "## Style\n\n"
                "- Add project conventions here.\n",
                encoding="utf-8",
            )
            self.chat_session.new_conversation()
            self.query_one("#conversation-title", Label).update(
                self.chat_session.title
            )
            self.show_system_message(
                "Created RECTURY.md and refreshed project context."
            )
            return True

        if command == "/index":
            args = shlex.split(command_parts[1]) if len(command_parts) > 1 else []
            action = args[0].lower() if args else "overview"

            if action in {"overview", "show"}:
                result = run_tool("project_overview", {}, self.chat_session.state)
                tool_message = ToolMessage("project_overview", {})
                self.query_one("#chat", VerticalScroll).mount(tool_message)
                tool_message.finish(result)
                self.schedule_chat_scroll()
                return True

            if action in {"build", "refresh"}:
                force = "--force" in args or "-f" in args
                result = run_tool(
                    "index_project",
                    {"force": force},
                    self.chat_session.state,
                )
                self.chat_session._refresh_system_message()
                self.chat_session._save()
                tool_message = ToolMessage("index_project", {"force": force})
                self.query_one("#chat", VerticalScroll).mount(tool_message)
                tool_message.finish(result)
                self.schedule_chat_scroll()
                return True

            if action == "changed":
                result = run_tool("index_changed_files", {}, self.chat_session.state)
                tool_message = ToolMessage("index_changed_files", {})
                self.query_one("#chat", VerticalScroll).mount(tool_message)
                tool_message.finish(result)
                self.schedule_chat_scroll()
                return True

            if action == "search":
                query = " ".join(args[1:]).strip()

                if not query:
                    self.show_system_message("Usage: /index search <query>")
                    return True

                result = run_tool(
                    "search_project",
                    {"query": query},
                    self.chat_session.state,
                )
                tool_message = ToolMessage("search_project", {"query": query})
                self.query_one("#chat", VerticalScroll).mount(tool_message)
                tool_message.finish(result)
                self.schedule_chat_scroll()
                return True

            self.show_system_message(
                "Usage: /index [overview] | /index build [--force] | "
                "/index changed | /index search <symbol>"
            )
            return True

        if command == "/mode":
            if len(command_parts) == 1:
                self.show_system_message(
                    "Current permission mode: "
                    f"{self.permission_mode}\n\n"
                    "Modes:\n"
                    "- auto: default; allow file edits with checkpoints and safe commands; ask for risky commands\n"
                    "- ask: ask before edits, unsafe commands, workspace changes, and undo\n"
                    "- plan: analysis only; file edits, commands, workspace changes, and undo are blocked\n"
                    "- danger: allow approved tool categories without prompts; command safety blocks still apply\n\n"
                    "Usage: /mode ask|auto|plan|danger"
                )
                return True

            mode = command_parts[1].strip().lower()

            if mode not in {"ask", "auto", "plan", "danger"}:
                self.show_system_message("Usage: /mode ask|auto|plan|danger")
                return True

            self.permission_mode = mode
            self.chat_session.set_permission_mode(mode)
            self.update_usage_bar()
            self.show_system_message(f"Permission mode set to {mode}.")
            return True

        if command == "/max":
            current = getattr(self.chat_session, "effort_mode", "normal")

            if len(command_parts) == 1:
                self.show_system_message(
                    "Current effort mode: "
                    f"{current}\n\n"
                    "Max effort makes Rectury more deliberate on long tasks:\n"
                    "- creates and updates todos for non-trivial work\n"
                    "- inspects/indexes/searches before editing existing projects\n"
                    "- uses architect/task for broad planning and investigation\n"
                    "- continues through implementation and validation\n\n"
                    "Usage: /max on|off|status"
                )
                return True

            value = command_parts[1].strip().lower()

            if value in {"status", "show"}:
                self.show_system_message(f"Current effort mode: {current}.")
                return True

            if value in {"on", "true", "yes", "max"}:
                self.chat_session.set_effort_mode("max")
                self.update_usage_bar()
                self.show_system_message(
                    "Max effort enabled. Rectury will organize long project "
                    "work with todos, workspace inspection, planning tools, "
                    "and validation."
                )
                return True

            if value in {"off", "false", "no", "normal"}:
                self.chat_session.set_effort_mode("normal")
                self.update_usage_bar()
                self.show_system_message("Max effort disabled.")
                return True

            self.show_system_message("Usage: /max on|off|status")
            return True

        if command == "/reference":
            args = shlex.split(command_parts[1]) if len(command_parts) > 1 else []
            action = args[0].lower() if args else "list"

            if action in {"list", "show"}:
                result = run_tool("reference_list", {}, self.chat_session.state)
                tool_message = ToolMessage("reference_list", {})
                self.query_one("#chat", VerticalScroll).mount(tool_message)
                tool_message.finish(result)
                self.schedule_chat_scroll()
                return True

            if action == "add":
                if len(args) < 2:
                    self.show_system_message("Usage: /reference add <path>")
                    return True

                path = " ".join(args[1:])
                result = run_tool(
                    "reference_add",
                    {"path": path},
                    self.chat_session.state,
                )
                self.chat_session._refresh_system_message()
                self.chat_session._save()
                tool_message = ToolMessage("reference_add", {"path": path})
                self.query_one("#chat", VerticalScroll).mount(tool_message)
                tool_message.finish(result)
                self.schedule_chat_scroll()
                return True

            if action == "remove":
                if len(args) < 2:
                    self.show_system_message(
                        "Usage: /reference remove <index-or-path>"
                    )
                    return True

                reference = " ".join(args[1:])
                result = run_tool(
                    "reference_remove",
                    {"reference": reference},
                    self.chat_session.state,
                )
                self.chat_session._refresh_system_message()
                self.chat_session._save()
                tool_message = ToolMessage(
                    "reference_remove",
                    {"reference": reference},
                )
                self.query_one("#chat", VerticalScroll).mount(tool_message)
                tool_message.finish(result)
                self.schedule_chat_scroll()
                return True

            if action == "clear":
                self.chat_session.state.set_reference_paths([])
                self.chat_session._refresh_system_message()
                self.chat_session._save()
                self.show_system_message("Cleared reference paths.")
                return True

            self.show_system_message(
                "Usage: /reference [list] | /reference add <path> | "
                "/reference remove <index-or-path> | /reference clear"
            )
            return True

        if command == "/hooks":
            action = (
                command_parts[1].strip().lower()
                if len(command_parts) > 1
                else "show"
            )

            if action == "init":
                path = create_default_hook_config(self.chat_session.state.workspace)
                self.show_system_message(
                    "Hooks config ready:\n"
                    f"{path}\n\n"
                    "Edit this file to enable project-specific hooks."
                )
                return True

            if action == "show":
                path = hook_config_path(self.chat_session.state.workspace)
                config = load_hook_config(self.chat_session.state.workspace)

                if not path.exists():
                    self.show_system_message(
                        "No hooks config found.\n"
                        "Run `/hooks init` to create .rectury/hooks.json."
                    )
                    return True

                hooks = config.get("hooks", {})
                lines = [f"Hooks config: {path}"]

                if config.get("error"):
                    lines.append(f"error: {config['error']}")

                for event_name in sorted(hooks):
                    event_hooks = hooks.get(event_name, [])
                    count = len(event_hooks) if isinstance(event_hooks, list) else 0
                    lines.append(f"- {event_name}: {count} hook(s)")

                    if isinstance(event_hooks, list):
                        for hook in event_hooks:
                            if isinstance(hook, dict):
                                status = (
                                    "enabled"
                                    if hook.get("enabled", True)
                                    else "disabled"
                                )
                                lines.append(
                                    f"  - {hook.get('name', hook.get('command', 'hook'))} [{status}]"
                                )

                self.show_system_message("\n".join(lines))
                return True

            self.show_system_message("Usage: /hooks init|show")
            return True

        if command == "/approved-tools":
            project_approvals = approved_command_keys(
                self.chat_session.state.workspace
            )

            if (
                not self.approved_permission_keys
                and not self.allow_edits_for_session
                and not project_approvals
            ):
                self.show_system_message("No session approvals yet.")
                return True

            approvals = sorted(self.approved_permission_keys)

            if self.allow_edits_for_session:
                approvals.insert(0, "file_write:workspace")

            approvals.extend(
                f"project:{approval}"
                for approval in sorted(project_approvals)
            )

            self.show_system_message(
                "Session approvals:\n"
                + "\n".join(f"- {approval}" for approval in approvals)
            )
            return True

        if command == "/history":
            result = run_tool(
                "checkpoint_history",
                {"limit": 20},
                self.chat_session.state,
            )
            tool_message = ToolMessage(
                "checkpoint_history",
                {"limit": 20},
            )
            self.query_one("#chat", VerticalScroll).mount(tool_message)
            tool_message.finish(result)
            self.schedule_chat_scroll()
            return True

        if command == "/undo":
            result = run_tool(
                "undo_last_change",
                {},
                self.chat_session.state,
            )
            self.chat_session._save()
            tool_message = ToolMessage("undo_last_change", {})
            self.query_one("#chat", VerticalScroll).mount(tool_message)
            tool_message.finish(result)
            self.schedule_chat_scroll()
            return True

        if command == "/doctor":
            config = current_model_env()
            self.show_system_message(
                "Rectury doctor:\n"
                f"- Workspace: {Path.cwd()}\n"
                f"- Provider: {config.get('AI_PROVIDER') or '(not set)'}\n"
                f"- Model: {config.get('AI_MODEL') or '(not set)'}\n"
                f"- Base URL: {config.get('AI_BASE_URL') or '(not set)'}\n"
                f"- API key: {'set' if config.get('AI_API_KEY') else 'missing'}\n"
                f"- Session approvals: {len(self.approved_permission_keys)}"
            )
            return True

        if command == "/cost":
            from core.cost_tracker import format_total_cost
            self.show_system_message(format_total_cost())
            return True

        if command == "/bug":
            if len(command_parts) < 2:
                self.show_system_message("Usage: /bug <description>")
                return True
            description = " ".join(command_parts[1:])
            from core.commands.bug import handle_bug_command
            result = handle_bug_command(description, [], str(Path.cwd()))
            self.show_system_message(result)
            return True

        if command == "/listen":
            from core.commands.listen import handle_listen_command, is_listen_enabled
            if is_listen_enabled():
                result = handle_listen_command()
                self.show_system_message(result)
            else:
                self.show_system_message("Listen is only available on macOS with iTerm.app or Apple Terminal")
            return True

        if command == "/pr-comments":
            from core.commands.pr_comments import handle_pr_comments_command
            prompt = handle_pr_comments_command()
            self.start_hidden_background_message(prompt)
            return True

        if command == "/review":
            args = " ".join(command_parts[1:]) if len(command_parts) > 1 else ""
            from core.commands.review import handle_review_command
            prompt = handle_review_command(args)
            self.start_hidden_background_message(prompt)
            return True

        if command == "/open":
            if len(command_parts) == 1:
                self.show_conversation_menu()
                return True

            conversation_id = command_parts[1].strip()

            if not self.chat_session.open_conversation(conversation_id):
                self.show_system_message("Conversation not found.")
                return True

            self.clear_conversation_messages()
            self.query_one("#conversation-title", Label).update(
                self.chat_session.title
            )
            self.render_conversation_messages()
            return True

        if user_message.startswith("/"):
            self.show_system_message(
                "Unknown command. Available commands: "
                + ", ".join(name for name, _ in self.COMMANDS)
            )
            return True

        return False

    def action_submit_message(self) -> None:
        if isinstance(self.screen, ConversationScreen):
            self.screen.action_open_selected()
            return
        if isinstance(self.screen, ModelScreen):
            self.screen.confirm_focused()
            return

        if self.active_permission is not None:
            self.resolve_inline_permission()
            return

        if self.response_in_progress:
            return

        message_input = self.query_one("#message-input", TextArea)
        user_message = message_input.text.strip()

        if isinstance(message_input, MessageInput):
            image_paths = message_input.image_paths_from_text(user_message)

            if image_paths:
                visible_markers = message_input.visible_image_markers(
                    user_message
                )

                if visible_markers:
                    user_message = " ".join(visible_markers)
                else:
                    attachments = self.image_attachments_from_paths(image_paths)
                    self.pending_attachments.extend(attachments)
                    user_message = " ".join(
                        attachment["marker"]
                        for attachment in attachments
                    )

        pending_attachments = [
            attachment
            for attachment in self.pending_attachments
            if (
                not attachment.get("marker")
                or attachment.get("marker", "") in user_message
            )
        ]
        self.pending_attachments = []

        if not user_message and not pending_attachments:
            return

        selected_command = self.selected_command()

        if selected_command is not None:
            user_message = selected_command

        message_input.clear()
        self.call_after_refresh(self.resize_message_input)

        if self.handle_command(user_message):
            return

        if user_message.startswith("!"):
            direct_command = user_message[1:].strip()

            if not direct_command:
                self.show_system_message("Usage: !<command>")
                return

            self.response_in_progress = True
            chat = self.query_one("#chat", VerticalScroll)
            chat.mount(
                self.render_user_message(
                    user_message,
                    pending_attachments,
                )
            )
            self.active_assistant_message = None
            self.active_assistant_content = ""
            self.tool_messages = {}

            thinking_label, spinner_timer = self.start_thinking_indicator(chat)

            self.schedule_chat_scroll()
            self.run_direct_command_in_background(
                direct_command,
                thinking_label,
                spinner_timer,
            )
            return

        self.response_in_progress = True
        chat = self.query_one("#chat", VerticalScroll)
        chat.mount(
            self.render_user_message(
                user_message,
                pending_attachments,
            )
        )
        self.active_assistant_message = None
        self.active_assistant_content = ""
        self.tool_messages = {}

        thinking_label, spinner_timer = self.start_thinking_indicator(chat)
        response_id = uuid4().hex
        self.active_response_id = response_id

        self.schedule_chat_scroll()
        self.active_response_worker = self.send_message_in_background(
            {
                "text": user_message,
                "attachments": pending_attachments,
            },
            thinking_label,
            spinner_timer,
            response_id,
        )

    def action_cancel_response(self) -> None:
        if self.active_permission is not None:
            self.resolve_inline_permission("reject")
            return

        if not self.response_in_progress:
            return

        if self.chat_session.cancel_active_command():
            self.show_system_message("Cancelling command...")
            return

        if self.active_response_worker is not None:
            self.active_response_worker.cancel()

        if self.active_spinner_timer is not None:
            self.active_spinner_timer.stop()
            self.active_spinner_timer = None

        self.active_response_id = None
        self.active_response_worker = None
        self.response_in_progress = False
        self.finish_thinking_label()
        self.show_system_message("Interrupted.")
        self.query_one("#message-input", TextArea).focus()
        self.schedule_chat_scroll()

    def on_mount(self) -> None:
        self.allow_edits_for_session = False
        self.approved_permission_keys = set()
        self.permission_mode = "auto"
        self.active_permission = None
        self.permission_index = 0
        self.response_in_progress = False
        self.converting_dropped_images = False
        self.pending_attachments = []
        self.seen_screenshot_paths = self.snapshot_screenshot_paths()
        self.chat_session = ChatSession(
            permission_handler=self.request_tool_permission
        )
        self.install_selection_bug_workaround()
        self.chat_session.set_permission_mode(self.permission_mode)
        self.command_index = 0
        self.command_scroll_offset = 0
        self.command_menu_text = ""
        self.active_assistant_message = None
        self.active_assistant_content = ""
        self.active_thinking_label = None
        self.thinking_started_at = None
        self.thinking_tick = 0
        self.active_response_id = None
        self.active_response_worker = None
        self.active_spinner_timer = None
        self.chat_scroll_queued = False
        self.chat_scroll_retry_queued = False
        self.last_copied_selection = ""
        self.tool_messages = {}
        self.query_one(
            "#command-menu-row",
            Horizontal,
        ).styles.display = "none"
        self.query_one(
            "#permission-input",
            Label,
        ).styles.display = "none"
        self.query_one("#conversation-title", Label).update(
            self.chat_session.title
        )
        self.update_usage_bar()

        self.render_conversation_messages()
        self.query_one("#message-input", TextArea).focus()
        self.set_interval(0.5, self.poll_recent_screenshots)
