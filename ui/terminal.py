from textual.app import App, ComposeResult
from textual.widgets import Input, Static, Label
from textual.containers import Horizontal, VerticalScroll
from core.chat import ChatSession
from ui.theme import APP_CSS
from textual import work
class RecturyApp(App):
    CSS = APP_CSS
    SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def compose(self) -> ComposeResult:
        yield VerticalScroll(id="chat")

        with Horizontal(id="input-row"):
            yield Static("❯", id="prompt")

            yield Input(
                placeholder="Ask anything... e.g., What is the capital of France?",
                id="message-input"
            )

    @work(thread=True)
    def send_message_in_background(self, user_message, thinking_label, spinner_timer):
        assistant_message = self.chat_session.send_message(user_message)
        spinner_timer.stop()
        thinking_label.update(assistant_message)

        chat = self.query_one("#chat", VerticalScroll)
        chat.scroll_end(animate=False)

    def update_spinner(self, thinking_label):
        frame = self.SPINNER_FRAMES[self.spinner_index]
        thinking_label.update(f"{frame} Thinking...")
        self.spinner_index = (self.spinner_index + 1) % len(self.SPINNER_FRAMES)
    
    def on_input_submitted(self, event: Input.Submitted):    
        user_message = event.value.strip()

        if not user_message:
            return
        
        event.input.value = ""

        chat = self.query_one("#chat", VerticalScroll)
        chat.mount(Label(user_message, classes="user-message"))
        thinking_label = Label("⠋ Thinking...", classes="assistant-message")
        chat.mount(thinking_label)

        self.spinner_index = 0
        spinner_timer = self.set_interval(
            0.08,
            lambda: self.update_spinner(thinking_label),
        )
        chat.mount(thinking_label)

        chat.scroll_end(animate=False)

        self.send_message_in_background(user_message, thinking_label, spinner_timer)       
    
    def on_mount(self) -> None:
        self.chat_session = ChatSession()
        self.query_one("#message-input", Input).focus()
