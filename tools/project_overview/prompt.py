# Generated from the Rectury tool catalog. Edit this file to change the
# prompt/schema for the `project_overview` tool.

TOOL_NAME = 'project_overview'
PROMPT = 'Return a compact overview from the project index: important files, language counts, symbol count, and import count. Builds the index if it does not exist.'
PARAMETERS = {'type': 'object',
 'properties': {'workspace': {'type': 'string',
                              'description': 'Directory inside the active workspace',
                              'default': '.'}},
 'additionalProperties': False}
