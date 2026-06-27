TOOL_NAME = 'read_notebook'
DESCRIPTION = (
    'Extract and read cells, source, and compact outputs from a Jupyter notebook.'
)
PROMPT = '''Read a Jupyter notebook (.ipynb) inside the active workspace and
return its cells with source and compact output summaries. Jupyter notebooks are
interactive documents that combine code, text, and visualizations. Use this
instead of read_file for notebooks, and read the notebook before editing a cell.
The file_path argument may be workspace-relative or absolute inside the active
workspace.'''
PARAMETERS = {'type': 'object',
 'properties': {'file_path': {'type': 'string',
                              'description': 'Path to a .ipynb file inside the active '
                                             'workspace'}},
 'required': ['file_path'],
 'additionalProperties': False}
