import json

from core.tool_runner import run_tool
from core.client import create_client

def load_tools():
    with open("tools/schemas.json", "r", encoding="utf-8") as f:
        return json.load(f)["tools"]

class ChatSession: 

    def __init__(self):
        self.client = create_client()
        self.tools = load_tools()
        self.messages = [
            {"role": "system", "content": "Your name is Rectury, you are a helpful assistant that can execute tools to help the user."}
        ]

    def send_message(self, user_input):
        self.messages.append({"role": "user", "content": user_input})
        full_response = ""
        tool_calls = []

        response = self.client.responses.create(
            model="grok-4.3",
            input=self.messages,
            tools=self.tools,
            stream=True
        )

        for event in response:
            if event.type == "response.output_text.delta":
                full_response += event.delta
                yield event.delta
            elif event.type == "response.output_item.done":
                item = event.item
                if item.type == "function_call":
                    tool_calls.append(item)

        for tool_call in tool_calls:
            arguments = json.loads(tool_call.arguments)
            result = run_tool(tool_call.name, arguments)

            self.messages.append(tool_call.model_dump())
            self.messages.append({"type": "function_call_output", "call_id": tool_call.call_id, "output": json.dumps(result)})

        if tool_calls:
            response = self.client.responses.create(
                model="grok-4.3",
                input=self.messages,
                tools=self.tools,
                stream=True
            )

            for event in response:
                if event.type == "response.output_text.delta":
                    full_response += event.delta
                    yield event.delta

        self.messages.append({"role": "assistant", "content": full_response})
