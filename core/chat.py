import json

from core.tool_runner import run_tool
from core.client import create_client

from ui.terminal import ask_user, show_assistant_message

def load_tools():
    with open("tools/schemas.json", "r", encoding="utf-8") as f:
        return json.load(f)["tools"]
    
def run_chat():
    client = create_client()
    tools = load_tools()

    messages = [
        {"role": "system", "content": "Eres un asistente útil."}
    ]

    while True:
        user_input = ask_user()

        if user_input.lower() == "exit":
            break
        
        messages.append({"role": "user", "content": user_input})

        response = client.responses.create(
            model = "grok-4.3",
            input=messages,
            tools=tools
        )

        for item in response.output:
            if item.type == "function_call":
                arguments = json.loads(item.arguments)
                result = run_tool(item.name, arguments)

                messages.append(item.model_dump())
                messages.append({
                    "type": "function_call_output",
                    "call_id": item.call_id,
                    "output": json.dumps(result)
                })

                response = client.responses.create(
                    model = "grok-4.3",
                    input=messages,
                    tools=tools
                )

        show_assistant_message(response.output_text)
        messages.append({"role": "assistant", "content": response.output_text})