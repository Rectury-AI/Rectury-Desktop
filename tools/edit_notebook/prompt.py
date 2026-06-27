TOOL_NAME = 'edit_notebook'
DESCRIPTION = 'Replace the contents of a specific cell in a Jupyter notebook.'
PROMPT = '''Replace the source of one cell in an already-read Jupyter notebook
(.ipynb) inside the active workspace. The cell_index is zero-based. Use
read_notebook first so you can choose the correct cell and the runtime can guard
against stale edits. This requires approval and creates a checkpoint. Use
insert_notebook_cell to add a new cell and delete_notebook_cell to remove one.'''
PARAMETERS = {'type': 'object',
 'properties': {'file_path': {'type': 'string',
                              'description': 'Path to a .ipynb file inside the active '
                                             'workspace'},
                'cell_index': {'type': 'integer',
                               'minimum': 0,
                               'description': 'Zero-based notebook cell index to '
                                              'replace'},
                'new_source': {'type': 'string',
                               'description': 'Complete replacement source for the '
                                              'selected cell'}},
 'required': ['file_path', 'cell_index', 'new_source'],
 'additionalProperties': False}
