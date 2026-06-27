MAX_LINES_TO_READ = 2000
MAX_LINE_LENGTH = 2000

DESCRIPTION = 'Read a file from the local filesystem.'
TOOL_NAME = 'read_file'
PROMPT = (
    'Read a UTF-8 file from the active workspace. The file_path parameter may '
    'be workspace-relative or absolute, but absolute paths must still be inside '
    f'the active workspace. By default, it reads up to {MAX_LINES_TO_READ} '
    'lines starting from the beginning of the file. You can optionally specify '
    'a line offset and limit for long files. Any lines longer than '
    f'{MAX_LINE_LENGTH} characters will be truncated. Use read_image for image '
    'files and read_notebook for Jupyter notebooks (.ipynb). Existing files '
    'must be read before edit_file, multi_edit, or notebook edit tools can '
    'modify them.'
)
PARAMETERS = {
    'type': 'object',
    'properties': {
        'file_path': {
            'type': 'string',
            'description': 'Path to a file inside the active workspace',
        },
        'offset': {
            'type': 'integer',
            'description': 'First line to read, starting at 1',
            'default': 1,
        },
        'limit': {
            'type': 'integer',
            'description': 'Maximum number of lines to return',
            'default': 500,
            'maximum': MAX_LINES_TO_READ,
        },
    },
    'required': ['file_path'],
    'additionalProperties': False,
}
