TOOL_NAME = 'list_files_in_dir'
DESCRIPTION = (
    'List files and directories in a given workspace path. Prefer glob or grep '
    'when you already know which patterns to search.'
)
PROMPT = '''List the immediate files and directories in one directory inside
the active workspace. Use this to verify paths, check parent directories before
creating files, and understand local project structure before reading or
editing files. The directory argument may be workspace-relative or absolute, but
absolute paths must still be inside the active workspace.'''
PARAMETERS = {'type': 'object',
 'properties': {'directory': {'type': 'string',
                              'description': 'Directory inside the active workspace'}},
 'required': ['directory'],
 'additionalProperties': False}
