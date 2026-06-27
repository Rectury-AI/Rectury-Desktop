TOOL_NAME = 'glob'
TOOL_NAME_FOR_PROMPT = 'glob'
DESCRIPTION = '''Fast file pattern matching tool for the active workspace. It
supports patterns like **/*.py, src/**/*.tsx, and **/package.json. Use this
when you know a filename or path pattern but not the exact location. For broad
open-ended searches that may need multiple rounds, prefer task or
search_project.'''
PROMPT = DESCRIPTION
PARAMETERS = {'type': 'object',
 'properties': {'pattern': {'type': 'string',
                            'description': 'Glob pattern such as **/*.py, '
                                           'src/**/*.tsx, or **/package.json'},
                'path': {'type': 'string',
                         'description': 'Directory inside the active workspace to '
                                        'search',
                         'default': '.'},
                'max_results': {'type': 'integer',
                                'minimum': 1,
                                'maximum': 500,
                                'description': 'Maximum number of file paths to return',
                                'default': 100}},
 'required': ['pattern'],
 'additionalProperties': False}
