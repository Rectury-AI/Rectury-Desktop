# Generated from the Rectury tool catalog. Edit this file to change the
# prompt/schema for the `list_reference_dir` tool.

TOOL_NAME = 'list_reference_dir'
PROMPT = 'List immediate files and directories inside a configured read-only reference path. Use this to inspect external projects without changing the active workspace.'
PARAMETERS = {'type': 'object',
 'properties': {'reference': {'type': 'string',
                              'description': 'One-based reference index or exact '
                                             'configured reference path. May be '
                                             'omitted when only one reference path '
                                             'exists.'},
                'directory': {'type': 'string',
                              'description': 'Directory inside the selected reference '
                                             'path',
                              'default': '.'}},
 'additionalProperties': False}
