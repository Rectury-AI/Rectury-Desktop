TOOL_NAME = 'insert_notebook_cell'
DESCRIPTION = 'Insert a new cell in a Jupyter notebook.'
PROMPT = '''Insert a code, markdown, or raw cell into an already-read Jupyter
notebook (.ipynb) inside the active workspace. The cell_index is zero-based;
use the total cell count from read_notebook to append. Use read_notebook first
so you can choose the correct insertion point. This requires approval and
creates a checkpoint.'''
PARAMETERS = {'type': 'object',
 'properties': {'file_path': {'type': 'string',
                              'description': 'Path to a .ipynb file inside the active '
                                             'workspace'},
                'cell_index': {'type': 'integer',
                               'minimum': 0,
                               'description': 'Zero-based insertion index. Use total '
                                              'cell count to append.'},
                'cell_type': {'type': 'string',
                              'enum': ['code', 'markdown', 'raw'],
                              'description': 'Type of cell to insert'},
                'source': {'type': 'string',
                           'description': 'Complete source for the new cell'}},
 'required': ['file_path', 'cell_index', 'cell_type', 'source'],
 'additionalProperties': False}
