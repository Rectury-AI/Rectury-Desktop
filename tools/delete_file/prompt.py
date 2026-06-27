# Generated from the Rectury tool catalog. Edit this file to change the
# prompt/schema for the `delete_file` tool.

TOOL_NAME = 'delete_file'
PROMPT = 'Delete a regular file inside the active workspace. The tool previews the deletion diff, asks for approval, and creates a checkpoint so the deletion can be undone.'
PARAMETERS = {'type': 'object',
 'properties': {'file_path': {'type': 'string',
                              'description': 'Path to the file inside the active '
                                             'workspace'}},
 'required': ['file_path'],
 'additionalProperties': False}
