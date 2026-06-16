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

        response = self.client.responses.create(
            model="grok-4.3",
            input=self.messages,
            tools=self.tools,
        )

        for item in response.output:
            if item.type == "function_call":
                arguments = json.loads(item.arguments)
                result = run_tool(item.name, arguments)

                self.messages.append(item.model_dump())
                self.messages.append({"type": "function_call_output", "call_id": item.call_id, "output": json.dumps(result)})

                response = self.client.responses.create(
                    model="grok-4.3",
                    input=self.messages,
                    tools=self.tools,
                )
        self.messages.append({"role": "assistant", "content": response.output_text})
        return response.output_text