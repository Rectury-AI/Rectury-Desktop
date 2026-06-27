# Generated from the Rectury tool catalog. Edit this file to change the
# prompt/schema for the `change_workspace` tool.

TOOL_NAME = 'change_workspace'
PROMPT = 'Change the current workspace directory (requires user approval).'
PARAMETERS = {'type': 'object',
 'properties': {'new_path': {'type': 'string',
                             'description': 'Path to the new workspace directory'}},
 'required': ['new_path'],
 'additionalProperties': False}
