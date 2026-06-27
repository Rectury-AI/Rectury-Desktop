import json
from datetime import datetime

from core.client import create_client
from core.context import build_context
from core.tool_results import result_for_model
from tools.task.prompt import create_agent_prompt


READ_ONLY_TOOLS = {
    "checkpoint_history",
    "get_current_time",
    "glob",
    "grep",
    "grep_reference",
    "index_changed_files",
    "list_files_in_dir",
    "list_reference_dir",
    "memory_read",
    "project_overview",
    "read_file",
    "read_image",
    "read_notebook",
    "read_reference_file",
    "reference_list",
    "reference_overview",
    "search_project",
    "search_reference_project",
    "search_symbols",
    "self_reflect",
    "think",
    "todo_read",
}


def local_time():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def load_read_only_tools():
    from tools.catalog import load_response_tools

    return load_response_tools(READ_ONLY_TOOLS)


def tool_calls_from_message(message):
    return list(getattr(message, "tool_calls", None) or [])


def task(prompt, state, max_rounds=6):
    from core.tool_runner import run_tool

    if not isinstance(prompt, str) or not prompt.strip():
        return {"error": "prompt must be a non-empty string."}

    try:
        max_rounds = max(1, min(int(max_rounds), 12))
    except (TypeError, ValueError):
        max_rounds = 6

    try:
        client, config = create_client()
    except ValueError as error:
        return {"error": str(error), "code": "model_not_configured"}

    tools = load_read_only_tools()
    messages = [
        {
            "role": "system",
            "content": create_agent_prompt(
                state.workspace,
                local_time(),
                build_context(str(state.workspace)),
                config.provider,
                config.model,
            ),
        },
        {"role": "user", "content": prompt.strip()},
    ]

    final_text = ""
    tool_use_count = 0
    errors = []

    for _ in range(max_rounds):
        response = client.chat.completions.create(
            model=config.model,
            messages=messages,
            tools=tools,
            parallel_tool_calls=False,
        )
        assistant_message = response.choices[0].message
        content = assistant_message.content or ""
        tool_calls = tool_calls_from_message(assistant_message)

        messages.append(
            {
                "role": "assistant",
                "content": content or None,
                "tool_calls": [
                    {
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments,
                        },
                    }
                    for tool_call in tool_calls
                ]
                if tool_calls
                else None,
            }
        )

        if content.strip():
            final_text = content.strip()

        if not tool_calls:
            break

        for tool_call in tool_calls:
            name = tool_call.function.name

            if name not in READ_ONLY_TOOLS:
                result = {
                    "error": f"Subagent cannot use mutating tool: {name}",
                    "code": "tool_not_allowed",
                }
            else:
                try:
                    arguments = json.loads(tool_call.function.arguments or "{}")
                except ValueError as error:
                    arguments = {}
                    result = {"error": str(error), "code": "invalid_arguments"}
                else:
                    try:
                        result = run_tool(name, arguments, state)
                    except Exception as error:
                        result = {"error": str(error)}

            if result.get("error"):
                errors.append({"tool": name, "error": result.get("error")})

            tool_use_count += 1
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result_for_model(name, arguments, result),
                }
            )

    return {
        "success": True,
        "summary": final_text or "The subagent completed without a final report.",
        "tool_uses": tool_use_count,
        "model": config.model,
        "errors": errors,
    }
