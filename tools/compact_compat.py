import math


MAX_COMPACT_BASH_TIMEOUT_MS = 600000


COMPACT_TOOL_SCHEMAS = [
    {
        "name": "dispatch_agent",
        "description": (
            "Launch a focused read-only subagent. This is a compact alias for "
            "the task tool."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "Detailed task for the subagent",
                },
                "max_rounds": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 12,
                    "description": "Maximum subagent tool rounds",
                    "default": 6,
                },
            },
            "required": ["prompt"],
            "additionalProperties": False,
        },
    },
    {
        "name": "Architect",
        "description": (
            "Analyze requirements and break them into clear implementation "
            "steps. Compact Architect-compatible alias."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "Architecture or implementation planning task",
                },
            },
            "required": ["task"],
            "additionalProperties": False,
        },
    },
    {
        "name": "Bash",
        "description": "Execute a bash command in the workspace.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The command to execute",
                },
                "timeout": {
                    "type": "number",
                    "description": (
                        "Optional timeout in milliseconds, max 600000"
                    ),
                },
            },
            "required": ["command"],
            "additionalProperties": False,
        },
    },
    {
        "name": "View",
        "description": "Read a file from the local filesystem.",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "The absolute path to the file to read",
                },
                "offset": {
                    "type": "number",
                    "description": (
                        "The line number to start reading from. Only provide "
                        "if the file is too large to read at once"
                    ),
                },
                "limit": {
                    "type": "number",
                    "description": (
                        "The number of lines to read. Only provide if the file "
                        "is too large to read at once."
                    ),
                },
            },
            "required": ["file_path"],
            "additionalProperties": False,
        },
    },
    {
        "name": "Edit",
        "description": "A tool for editing files.",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "The absolute path to the file to modify",
                },
                "old_string": {
                    "type": "string",
                    "description": "The text to replace",
                },
                "new_string": {
                    "type": "string",
                    "description": "The text to replace it with",
                },
            },
            "required": ["file_path", "old_string", "new_string"],
            "additionalProperties": False,
        },
    },
    {
        "name": "Replace",
        "description": "Write a file to the local filesystem.",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": (
                        "The absolute path to the file to write"
                    ),
                },
                "content": {
                    "type": "string",
                    "description": "The content to write to the file",
                },
            },
            "required": ["file_path", "content"],
            "additionalProperties": False,
        },
    },
    {
        "name": "GlobTool",
        "description": (
            "Fast file pattern matching tool that works with any codebase size."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "The glob pattern to match files against",
                },
                "path": {
                    "type": "string",
                    "description": (
                        "The directory to search in. Defaults to the current "
                        "working directory."
                    ),
                },
            },
            "required": ["pattern"],
            "additionalProperties": False,
        },
    },
    {
        "name": "GrepTool",
        "description": "Fast content search tool that works with any codebase size.",
        "parameters": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": (
                        "The regular expression pattern to search for in file "
                        "contents"
                    ),
                },
                "path": {
                    "type": "string",
                    "description": (
                        "The directory to search in. Defaults to the current "
                        "working directory."
                    ),
                },
                "include": {
                    "type": "string",
                    "description": (
                        "File pattern to include in the search, e.g. *.js"
                    ),
                },
            },
            "required": ["pattern"],
            "additionalProperties": False,
        },
    },
    {
        "name": "LS",
        "description": "Lists files and directories in a given path.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": (
                        "The absolute path to the directory to list"
                    ),
                },
            },
            "required": ["path"],
            "additionalProperties": False,
        },
    },
    {
        "name": "ReadNotebook",
        "description": "Read source and outputs from a Jupyter notebook.",
        "parameters": {
            "type": "object",
            "properties": {
                "notebook_path": {
                    "type": "string",
                    "description": "The absolute path to the Jupyter notebook",
                },
            },
            "required": ["notebook_path"],
            "additionalProperties": False,
        },
    },
    {
        "name": "NotebookEditCell",
        "description": "Replace, insert, or delete a Jupyter notebook cell.",
        "parameters": {
            "type": "object",
            "properties": {
                "notebook_path": {
                    "type": "string",
                    "description": "The absolute path to the notebook",
                },
                "cell_number": {
                    "type": "number",
                    "description": "The zero-based cell index",
                },
                "new_source": {
                    "type": "string",
                    "description": "The new source for the cell",
                },
                "cell_type": {
                    "type": "string",
                    "enum": ["code", "markdown"],
                    "description": "Required for insert mode",
                },
                "edit_mode": {
                    "type": "string",
                    "enum": ["replace", "insert", "delete"],
                    "description": "Defaults to replace",
                },
            },
            "required": ["notebook_path", "cell_number", "new_source"],
            "additionalProperties": False,
        },
    },
    {
        "name": "MemoryRead",
        "description": "Read project memory files.",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Optional memory file path",
                },
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "MemoryWrite",
        "description": "Write project memory.",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the memory file to write",
                },
                "content": {
                    "type": "string",
                    "description": "Content to write to the file",
                },
            },
            "required": ["file_path", "content"],
            "additionalProperties": False,
        },
    },
    {
        "name": "Think",
        "description": "No-op tool that logs a thought.",
        "parameters": {
            "type": "object",
            "properties": {
                "thought": {
                    "type": "string",
                    "description": "The reasoning note to record",
                },
            },
            "required": ["thought"],
            "additionalProperties": False,
        },
    },
    {
        "name": "StickerRequest",
        "description": "Compatibility tool for sticker/swag requests.",
        "parameters": {
            "type": "object",
            "properties": {
                "trigger": {
                    "type": "string",
                    "description": "The user phrase requesting stickers",
                },
            },
            "required": ["trigger"],
            "additionalProperties": False,
        },
    },
]


def timeout_ms_to_seconds(value):
    try:
        milliseconds = float(value)
    except (TypeError, ValueError):
        return 120

    milliseconds = max(1, min(milliseconds, MAX_COMPACT_BASH_TIMEOUT_MS))
    return max(1, int(math.ceil(milliseconds / 1000)))


def normalize_compact_tool_call(tool_name, arguments):
    if tool_name == "dispatch_agent":
        return "task", arguments

    if tool_name == "Architect":
        return "architect", arguments

    if tool_name == "Bash":
        normalized = dict(arguments)
        if "timeout" in normalized:
            normalized["timeout"] = timeout_ms_to_seconds(normalized["timeout"])
        return "run_command", normalized

    if tool_name == "View":
        return "read_file", arguments

    if tool_name == "Edit":
        return (
            "edit_file",
            {
                "file_path": arguments.get("file_path"),
                "old_text": arguments.get("old_string", ""),
                "new_text": arguments.get("new_string", ""),
            },
        )

    if tool_name == "Replace":
        return "write_file", arguments

    if tool_name == "GlobTool":
        return "glob", arguments

    if tool_name == "GrepTool":
        normalized = {
            "pattern": arguments.get("pattern"),
            "path": arguments.get("path", "."),
            "files_only": True,
        }
        if arguments.get("include"):
            normalized["glob"] = arguments["include"]
        return "grep", normalized

    if tool_name == "LS":
        return (
            "list_files_in_dir",
            {
                "directory": arguments.get("path", "."),
                "recursive": True,
            },
        )

    if tool_name == "ReadNotebook":
        return "read_notebook", {"file_path": arguments.get("notebook_path")}

    if tool_name == "NotebookEditCell":
        mode = arguments.get("edit_mode") or "replace"
        cell_number = arguments.get("cell_number")

        if mode == "insert":
            return (
                "insert_notebook_cell",
                {
                    "file_path": arguments.get("notebook_path"),
                    "cell_index": cell_number,
                    "cell_type": arguments.get("cell_type") or "code",
                    "source": arguments.get("new_source", ""),
                },
            )

        if mode == "delete":
            return (
                "delete_notebook_cell",
                {
                    "file_path": arguments.get("notebook_path"),
                    "cell_index": cell_number,
                },
            )

        return (
            "edit_notebook",
            {
                "file_path": arguments.get("notebook_path"),
                "cell_index": cell_number,
                "new_source": arguments.get("new_source", ""),
                "cell_type": arguments.get("cell_type"),
            },
        )

    if tool_name == "MemoryRead":
        return "memory_read", arguments

    if tool_name == "MemoryWrite":
        normalized = {
            "content": arguments.get("content", ""),
            "mode": "replace",
        }
        if arguments.get("file_path") in {"RECTURY.md", ".rectury.md"}:
            normalized["file_path"] = arguments["file_path"]
        return "memory_write", normalized

    if tool_name == "Think":
        return "think", arguments

    if tool_name == "StickerRequest":
        return "sticker_request", arguments

    return tool_name, arguments
