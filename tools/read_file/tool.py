from typing import Optional
from tools.functions.read_file import DEFAULT_LINE_LIMIT, read_file


TOOL = read_file

# Schema de input (equivalente a z.strictObject de Zod)
input_schema = {
    "type": "object",
    "properties": {
        "file_path": {
            "type": "string",
            "description": "The absolute path to the file to read"
        },
        "offset": {
            "type": "integer",
            "description": "The line number to start reading from. Only provide if the file is too large to read at once"
        },
        "limit": {
            "type": "integer",
            "description": "The number of lines to read. Only provide if the file is too large to read at once."
        }
    },
    "required": ["file_path"],
    "additionalProperties": False
}


def ReadFileTool(state):
    """Compact-style wrapper for reading files."""
    return {
        "name": "read_file",
        "description": lambda: "Read a file from the local filesystem.",
        "prompt": lambda: "Reads a file from the local filesystem...",
        "input_schema": input_schema,
        "is_read_only": lambda: True,
        "user_facing_name": lambda: "Read",
        "is_enabled": lambda: True,
        "needs_permissions": lambda args: False,
        "call": lambda args: read_file(
            args["file_path"],
            state,
            args.get("offset", 1),
            args.get("limit", DEFAULT_LINE_LIMIT)
        ),
        "render_result_for_assistant": lambda data: data
    }
