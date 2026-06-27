# Generated from the Rectury tool catalog. Edit this file to change the
# prompt/schema for the `grep_reference` tool.

TOOL_NAME = 'grep_reference'
PROMPT = 'Search for a regex pattern inside a configured read-only reference path.'
PARAMETERS = {'type': 'object',
 'properties': {'pattern': {'type': 'string',
                            'description': 'Regex pattern to search for'},
                'reference': {'type': 'string',
                              'description': 'One-based reference index or exact '
                                             'configured reference path. May be '
                                             'omitted when only one reference path '
                                             'exists.'},
                'path': {'type': 'string',
                         'description': 'Directory to search in relative to the '
                                        'selected reference path',
                         'default': '.'},
                'glob': {'type': 'string',
                         'description': 'Glob pattern to filter files',
                         'default': '**/*'},
                'ignore_case': {'type': 'boolean',
                                'description': 'Case-insensitive search',
                                'default': True},
                'max_results': {'type': 'integer',
                                'description': 'Maximum number of matches to return',
                                'default': 100},
                'context': {'type': 'integer',
                            'description': 'Number of context lines before and after '
                                           'each match',
                            'default': 0},
                'whole_word': {'type': 'boolean',
                               'description': 'Match whole words only',
                               'default': False},
                'multiline': {'type': 'boolean',
                              'description': 'Allow . to match newlines (DOTALL)',
                              'default': False}},
 'required': ['pattern'],
 'additionalProperties': False}
