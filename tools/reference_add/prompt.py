# Generated from the Rectury tool catalog. Edit this file to change the
# prompt/schema for the `reference_add` tool.

TOOL_NAME = 'reference_add'
PROMPT = 'Add a read-only external directory as a reference path for this conversation. Use this when the user points to another project or source tree that should be inspected without changing the active workspace. Reference paths are never edited.'
PARAMETERS = {'type': 'object',
 'properties': {'path': {'type': 'string',
                         'description': 'Absolute or home-relative directory path to '
                                        'add as a read-only reference'}},
 'required': ['path'],
 'additionalProperties': False}
