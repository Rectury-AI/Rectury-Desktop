# Generated from the Rectury tool catalog. Edit this file to change the
# prompt/schema for the `read_reference_file` tool.

TOOL_NAME = 'read_reference_file'
PROMPT = 'Read a UTF-8 file from a configured read-only reference path. Use this for external source code or examples that should inform work in the active workspace. Reference files cannot be edited.'
PARAMETERS = {'type': 'object',
 'properties': {'reference': {'type': 'string',
                              'description': 'One-based reference index or exact '
                                             'configured reference path. May be '
                                             'omitted when only one reference path '
                                             'exists.'},
                'file_path': {'type': 'string',
                              'description': 'Path to a file inside the selected '
                                             'reference path'},
                'offset': {'type': 'integer',
                           'minimum': 1,
                           'description': 'First line to read, starting at 1'},
                'limit': {'type': 'integer',
                          'minimum': 1,
                          'maximum': 2000,
                          'description': 'Maximum number of lines to return'}},
 'required': ['file_path'],
 'additionalProperties': False}
