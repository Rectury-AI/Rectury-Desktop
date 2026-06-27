# Generated from the Rectury tool catalog. Edit this file to change the
# prompt/schema for the `search_symbols` tool.

TOOL_NAME = 'search_symbols'
PROMPT = 'Search only for functions/classes/components in the project index without reading full files. Prefer search_project for general locating because it combines symbols, paths, imports, important files, and light content.'
PARAMETERS = {'type': 'object',
 'properties': {'query': {'type': 'string',
                          'description': 'Substring to match against symbol names'},
                'workspace': {'type': 'string',
                              'description': 'Directory inside the active workspace',
                              'default': '.'},
                'limit': {'type': 'integer',
                          'minimum': 1,
                          'maximum': 100,
                          'description': 'Maximum symbol matches to return',
                          'default': 50}},
 'required': ['query'],
 'additionalProperties': False}
