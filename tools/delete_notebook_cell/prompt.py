TOOL_NAME = 'delete_notebook_cell'
DESCRIPTION = 'Delete a specific cell from a Jupyter notebook.'
PROMPT = '''Delete one cell from an already-read Jupyter notebook (.ipynb)
inside the active workspace. The cell_index is zero-based. Use read_notebook
first so you can verify the target cell. This requires approval and creates a
checkpoint.'''
PARAMETERS = {'type': 'object',
 'properties': {'file_path': {'type': 'string',
                              'description': 'Path to a .ipynb file inside the active '
                                             'workspace'},
                'cell_index': {'type': 'integer',
                               'minimum': 0,
                               'description': 'Zero-based notebook cell index to '
                                              'delete'}},
 'required': ['file_path', 'cell_index'],
 'additionalProperties': False}
