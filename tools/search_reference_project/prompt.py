# Generated from the Rectury tool catalog. Edit this file to change the
# prompt/schema for the `search_reference_project` tool.

TOOL_NAME = 'search_reference_project'
PROMPT = 'Unified smart search inside a configured read-only reference path. Searches indexed file paths, important files, symbols/classes/functions, imports, and optional light content snippets without reading the whole reference project.'
PARAMETERS = {'type': 'object',
 'properties': {'query': {'type': 'string',
                          'description': 'Natural search query, symbol name, feature '
                                         'name, file name, or dependency name'},
                'reference': {'type': 'string',
                              'description': 'Reference index number or exact '
                                             'configured reference path. If only one '
                                             'reference exists, this can be omitted.'},
                'limit': {'type': 'integer',
                          'minimum': 1,
                          'maximum': 50,
                          'description': 'Maximum ranked files to return',
                          'default': 20},
                'include_content': {'type': 'boolean',
                                    'description': 'Also search small/medium reference '
                                                   'file contents for matching lines. '
                                                   'Keep true unless you only want '
                                                   'metadata search.',
                                    'default': True}},
 'required': ['query'],
 'additionalProperties': False}
