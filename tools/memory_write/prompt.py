TOOL_NAME = 'memory_write'
DESCRIPTION = 'Update project memory.'
PROMPT = '''Update project memory in RECTURY.md or .rectury.md.
Use this only for stable project guidance, durable local facts, or explicit
instructions the user wants remembered. Do not store secrets, transient
debugging notes, or facts that only matter to the current turn. This requires
approval and creates a checkpoint.'''
PARAMETERS = {'type': 'object',
 'properties': {'content': {'type': 'string',
                            'description': 'Memory text to append or write'},
                'file_path': {'type': 'string',
                              'enum': ['RECTURY.md', '.rectury.md'],
                              'description': 'Memory file to update',
                              'default': 'RECTURY.md'},
                'mode': {'type': 'string',
                         'enum': ['append', 'replace'],
                         'description': 'Append to existing memory or replace the '
                                        'whole file',
                         'default': 'append'}},
 'required': ['content'],
 'additionalProperties': False}
