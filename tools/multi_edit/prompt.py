# Generated from the Rectury tool catalog. Edit this file to change the
# prompt/schema for the `multi_edit` tool.

TOOL_NAME = 'multi_edit'
PROMPT = 'Apply multiple exact text replacements to one already-read UTF-8 file inside the active workspace in a single atomic write. Use this when several unique replacements belong together. Each old_text must match exactly once in the current file state after previous replacements. Do not use this to create files.'
PARAMETERS = {'type': 'object',
 'properties': {'file_path': {'type': 'string',
                              'description': 'Path to an existing file inside the '
                                             'active workspace. The file must be read '
                                             'first.'},
                'edits': {'type': 'array',
                          'description': 'Ordered exact replacements to apply '
                                         'atomically.',
                          'items': {'type': 'object',
                                    'properties': {'old_text': {'type': 'string',
                                                                'description': 'Exact '
                                                                               'non-empty '
                                                                               'text '
                                                                               'to '
                                                                               'replace. '
                                                                               'Include '
                                                                               'enough '
                                                                               'context '
                                                                               'to '
                                                                               'make '
                                                                               'it '
                                                                               'unique.'},
                                                   'new_text': {'type': 'string',
                                                                'description': 'Replacement '
                                                                               'text. '
                                                                               'Use an '
                                                                               'empty '
                                                                               'string '
                                                                               'only '
                                                                               'to '
                                                                               'delete '
                                                                               'the '
                                                                               'matched '
                                                                               'block.'}},
                                    'required': ['old_text', 'new_text'],
                                    'additionalProperties': False},
                          'minItems': 1,
                          'maxItems': 50}},
 'required': ['file_path', 'edits'],
 'additionalProperties': False}
