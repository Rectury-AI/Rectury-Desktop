import json
from datetime import datetime
from uuid import uuid4

from core.client import create_client
from core.conversation_store import load_latest_conversation, save_conversation
from core.tool_runner import run_tool


SYSTEM_MESSAGE = {
    "role": "system",
    "content": (
        "Your name is Rectury. You are a helpful assistant that can "
        "execute tools to help the user. Never use Unicode or graphical "
    ),
}


def current_time():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def load_tools():
    with open("tools/schemas.json", "r", encoding="utf-8") as file:
        response_tools = json.load(file)["tools"]

    return [
        {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool.get("description", ""),
                "parameters": tool.get("parameters", {"type": "object"}),
            },
        }
        for tool in response_tools
    ]


class ChatSession:
    MAX_TOOL_ROUNDS = 8

    def __init__(self):
        self.client, self.config = create_client()
        self.tools = load_tools()

        saved_conversation = load_latest_conversation()

        if saved_conversation:
            self.conversation_id = saved_conversation["id"]
            self.title = saved_conversation.get("title", "New conversation")
            self.created_at = saved_conversation.get("created_at", current_time())
            self.updated_at = saved_conversation.get("updated_at", current_time())
            self.messages = saved_conversation.get("messages", [SYSTEM_MESSAGE])
        else:
            self.conversation_id = str(uuid4())
            self.title = "New conversation"
            self.created_at = current_time()
            self.updated_at = self.created_at
            self.messages = [SYSTEM_MESSAGE.copy()]

    def _conversation_data(self):
        return {
            "id": self.conversation_id,
            "title": self.title,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "messages": self.messages,
        }

    def _save(self):
        self.updated_at = current_time()
        save_conversation(self._conversation_data())

    def _fallback_title(self, user_input):
        words = user_input.strip().split()
        title = " ".join(words[:6])
        return title[:60] or "New conversation"

    def _generate_title(self, user_input, assistant_response):
        try:
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Create a short title of 3 to 7 words for this "
                            "conversation. Return only the title, without quotes."
                        ),
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

    def _stream_response(self):
        stream = self.client.chat.completions.create(
            model=self.config.model,
            messages=self.messages,
            tools=self.tools,
            stream=True,
        )

        content_parts = []
        tool_calls = {}

        for chunk in stream:
            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta

            if delta.content:
                content_parts.append(delta.content)
                yield delta.content

            for tool_call in delta.tool_calls or []:
                current = tool_calls.setdefault(
                    tool_call.index,
                    {
                        "id": "",
                        "type": "function",
                        "function": {"name": "", "arguments": ""},
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

        return "".join(content_parts), [
            tool_calls[index] for index in sorted(tool_calls)
        ]

    def send_message(self, user_input):
        self.messages.append({"role": "user", "content": user_input})
        final_content = ""

        for _ in range(self.MAX_TOOL_ROUNDS):
            stream = self._stream_response()

            try:
                while True:
                    yield next(stream)
            except StopIteration as completed:
                content, tool_calls = completed.value

            final_content += content
            assistant_message = {
                "role": "assistant",
                "content": content or None,
            }

            if tool_calls:
                assistant_message["tool_calls"] = tool_calls

            self.messages.append(assistant_message)

            if not tool_calls:
                if self.title == "New conversation":
                    self.title = self._generate_title(user_input, final_content)
                self._save()
                return

            for tool_call in tool_calls:
                function = tool_call["function"]

                try:
                    arguments = json.loads(function["arguments"] or "{}")
                    result = run_tool(function["name"], arguments)
                    output = json.dumps(result)
                except Exception as error:
                    output = json.dumps({"error": str(error)})

                self.messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": output,
                    }
                )

        self.messages.append(
            {
                "role": "assistant",
                "content": (
                    "Tool execution stopped after reaching the maximum number "
                    "of tool rounds."
                ),
            }
        )
        self._save()
