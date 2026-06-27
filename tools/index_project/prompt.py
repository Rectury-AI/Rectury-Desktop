# Generated from the Rectury tool catalog. Edit this file to change the
# prompt/schema for the `index_project` tool.

TOOL_NAME = 'index_project'
PROMPT = 'Build or refresh an incremental workspace index with important files, symbols, imports, language counts, and changed/reused cache stats. Use this before broad project analysis so you do not read the entire project.'
PARAMETERS = {'type': 'object',
 'properties': {'force': {'type': 'boolean',
                          'description': 'Rebuild from scratch instead of using cache',
                          'default': False},
                'workspace': {'type': 'string',
                              'description': 'Directory inside the active workspace to '
                                             'index',
                              'default': '.'}},
 'additionalProperties': False}
