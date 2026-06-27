# Generated from the Rectury tool catalog. Edit this file to change the
# prompt/schema for the `todo_write` tool.

TOOL_NAME = 'todo_write'
PROMPT = 'Replace the current per-conversation task list. Use this for non-trivial multi-step work so progress is explicit. Keep exactly one task in_progress at a time. Use pending for not started work and completed for finished work.'
PARAMETERS = {'type': 'object',
 'properties': {'todos': {'type': 'array',
                          'description': 'Complete replacement task list for this '
                                         'conversation.',
                          'items': {'type': 'object',
                                    'properties': {'id': {'type': 'string',
                                                          'description': 'Stable task '
                                                                         'id. Reuse '
                                                                         'the existing '
                                                                         'id when '
                                                                         'updating a '
                                                                         'task.'},
                                                   'content': {'type': 'string',
                                                               'description': 'Short '
                                                                              'concrete '
                                                                              'task '
                                                                              'description.'},
                                                   'status': {'type': 'string',
                                                              'enum': ['pending',
                                                                       'in_progress',
                                                                       'completed'],
                                                              'description': 'Current '
                                                                             'task '
                                                                             'status.'}},
                                    'required': ['content', 'status'],
                                    'additionalProperties': False}}},
 'required': ['todos'],
 'additionalProperties': False}
