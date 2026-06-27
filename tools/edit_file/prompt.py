TOOL_NAME = 'edit_file'
DESCRIPTION = 'Edit one UTF-8 file inside the active workspace.'
PROMPT = '''Edit one UTF-8 file inside the active workspace. For moving or
renaming files, use run_command with mv when appropriate. For larger rewrites,
use write_file. For Jupyter notebooks, use read_notebook and the notebook edit
tools instead.

Before using this tool:
1. Use read_file to understand the current file contents and context.
2. When creating a new file, use list_files_in_dir to verify the parent
   directory exists and is the intended location.

Arguments:
1. file_path: workspace-relative or absolute path inside the active workspace.
2. old_text: exact text to replace. It must match the file exactly, including
   whitespace and indentation.
3. new_text: replacement text.

Critical requirements:
- old_text must uniquely identify one instance. Include enough surrounding
  context, normally 3-5 lines before and after the change point.
- This tool changes one occurrence per call. For several replacements in one
  file, use multi_edit when the edits belong together.
- If the file has not been read, read_file first so the runtime can detect stale
  edits.
- To create a new file, use a path that does not exist, an empty old_text, and
  the complete new file contents in new_text.
- Ensure the result is idiomatic and does not leave the project broken.
'''
PARAMETERS = {'type': 'object',
 'properties': {'file_path': {'type': 'string',
                              'description': 'Path inside the active workspace. '
                                             'Existing files must be read first; new '
                                             'paths can be created with empty '
                                             'old_text.'},
                'old_text': {'type': 'string',
                             'description': 'Exact text to replace in an existing '
                                            'file. Include enough surrounding lines so '
                                            'it occurs once. Use an empty string only '
                                            'to create a new file.'},
                'new_text': {'type': 'string',
                             'description': 'Replacement text. Use an empty string '
                                            'only when intentionally deleting the '
                                            'matched block.'}},
 'required': ['file_path', 'old_text', 'new_text'],
 'additionalProperties': False}
