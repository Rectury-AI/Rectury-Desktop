TOOL_NAME = 'grep'
TOOL_NAME_FOR_PROMPT = 'grep'
DESCRIPTION = '''Fast content search tool for the active workspace. It searches
file contents using regular expressions, supports file filtering with glob, and
can return context lines. Use this when you need files containing a specific
pattern. For broad open-ended searches that may need multiple rounds, prefer
task or search_project.'''
PROMPT = DESCRIPTION
PARAMETERS = {'type': 'object',
 'properties': {'pattern': {'type': 'string',
                            'description': 'Regex pattern to search for'},
                'path': {'type': 'string',
                         'description': 'Directory to search in (relative to '
                                        'workspace)',
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
