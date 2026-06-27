# Generated from the Rectury tool catalog. Edit this file to change the
# prompt/schema for the `index_changed_files` tool.

TOOL_NAME = 'index_changed_files'
PROMPT = 'Show files that changed or disappeared since the last project index build. Use this to know when cached project knowledge may be stale.'
PARAMETERS = {'type': 'object',
 'properties': {'workspace': {'type': 'string',
                              'description': 'Directory inside the active workspace',
                              'default': '.'}},
 'additionalProperties': False}
