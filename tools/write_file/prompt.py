TOOL_NAME = 'write_file'
DESCRIPTION = 'Write a complete UTF-8 file inside the active workspace.'
PROMPT = '''Create or overwrite a complete UTF-8 file inside the active
workspace. Use this when replacing the whole file is clearer than edit_file.
The tool previews the diff and asks for approval before writing.

Before using this tool:
1. If overwriting an existing file, use read_file to understand its contents and
   preserve unrelated user changes.
2. If creating a new file, use list_files_in_dir to verify the parent directory
   exists and is the intended location.

Prefer edit_file or multi_edit for focused changes. Use write_file for new
files, generated files, or intentional whole-file replacements.
'''
PARAMETERS = {'type': 'object',
 'properties': {'file_path': {'type': 'string',
                              'description': 'Path to the file inside the workspace'},
                'content': {'type': 'string',
                            'description': 'Complete file contents to write'}},
 'required': ['file_path', 'content'],
 'additionalProperties': False}
