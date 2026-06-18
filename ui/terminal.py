from pathlib import Path

from textual.app import App, ComposeResult
from textual.widgets import Static, Label, TextArea
from textual.containers import Horizontal, VerticalScroll, Vertical
from core.chat import ChatSession
from ui.theme import APP_CSS
from textual import work
from textual.binding import Binding

class RecturyApp(App):
    CSS = APP_CSS
    ALLOW_SELECT = False
    SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    BINDINGS = [
        Binding("enter", "submit_message", "Send", show=False, priority=True),
        Binding("ctrl+l", "insert_newline", "New line", show=False, priority=True),
        Binding("ctrl+a", "select_input_all", "Select all", show=False, priority=True),
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
            Label("Workspace", id="agent-name"),
            Label(f"~ {Path.cwd()}", id="status"),
            id="welcome-panel",
        )
       
        yield VerticalScroll(
            welcome_panel,
            id="chat",
        )
        with Horizontal(id="input-row"):
            yield Static("❯", id="prompt")
            yield TextArea(
                placeholder="Ask anything...",
                id="message-input",
                soft_wrap=True,
                show_line_numbers=False,
                highlight_cursor_line=False,
            )

    def set_status(self, status: str) -> None:
        self.query_one("#status", Label).update(f"Status: {status}")

    @work(thread=True)

    def send_message_in_background(self, user_message, thinking_label, spinner_timer):
        assistant_message = ""
        started = False

        for chunk in self.chat_session.send_message(user_message):
            if not started:
                started = True
                self.call_from_thread(spinner_timer.stop)

            assistant_message += chunk
            self.call_from_thread(thinking_label.update, assistant_message)

        chat = self.query_one("#chat", VerticalScroll)
        self.call_from_thread(spinner_timer.stop)
        self.call_from_thread(chat.scroll_end, animate=False)

    def update_spinner(self, thinking_label):
        frame = self.SPINNER_FRAMES[self.spinner_index]
        thinking_label.update(f"{frame} Thinking...")
        self.spinner_index = (self.spinner_index + 1) % len(self.SPINNER_FRAMES)
    
    def action_insert_newline(self) -> None:
        message_input = self.query_one("#message-input", TextArea)
        message_input.insert("\n")

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        if event.text_area.id == "message-input":
            self.call_after_refresh(self.resize_message_input)

    def resize_message_input(self) -> None:
        message_input = self.query_one("#message-input", TextArea)
        input_row = self.query_one("#input-row", Horizontal)

        content_height = max(1, min(6, message_input.wrapped_document.height))

        message_input.styles.height = content_height
        input_row.styles.height = content_height

    def action_submit_message(self) -> None:
        message_input = self.query_one("#message-input", TextArea)
        user_message = message_input.text.strip()

        if not user_message:
            return

        message_input.clear()
        self.call_after_refresh(self.resize_message_input)

        chat = self.query_one("#chat", VerticalScroll)
        chat.mount(Label(user_message, classes="user-message"))

        thinking_label = Label("⠋ Thinking...", classes="assistant-message")
        chat.mount(thinking_label)

        self.spinner_index = 0
        spinner_timer = self.set_interval(
            0.08,
            lambda: self.update_spinner(thinking_label),
        )

        chat.scroll_end(animate=False)
        self.send_message_in_background(
            user_message,
            thinking_label,
            spinner_timer,
        )

    def on_mount(self) -> None:
        self.chat_session = ChatSession()
        self.query_one("#message-input", TextArea).focus()
