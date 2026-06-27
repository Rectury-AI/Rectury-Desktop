from tools.manifest import TOOL_MODULES
from tools.compact_compat import COMPACT_TOOL_SCHEMAS


def load_tool_schemas(tool_names=None):
    allowed = set(tool_names) if tool_names is not None else None
    schemas = []

    for tool in TOOL_MODULES:
        if allowed is not None and tool.name not in allowed:
            continue

        schemas.append(
            {
                "name": tool.name,
                "description": tool.prompt_module.PROMPT,
                "parameters": tool.prompt_module.PARAMETERS,
            }
        )

    for schema in COMPACT_TOOL_SCHEMAS:
        if allowed is not None and schema["name"] not in allowed:
            continue

        schemas.append(schema)

    return schemas


def load_response_tools(tool_names=None):
    return [
        {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool.get("description", ""),
                "parameters": tool.get("parameters", {"type": "object"}),
            },
        }
        for tool in load_tool_schemas(tool_names)
    ]
