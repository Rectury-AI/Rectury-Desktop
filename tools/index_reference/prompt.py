# Generated from the Rectury tool catalog. Edit this file to change the
# prompt/schema for the `index_reference` tool.

TOOL_NAME = 'index_reference'
PROMPT = "Build or refresh an incremental index for a configured read-only reference path. The cache is stored locally, not inside the reference path."
PARAMETERS = {'type': 'object',
 'properties': {'reference': {'type': 'string',
                              'description': 'Reference index number or exact '
                                             'configured reference path. If only one '
                                             'reference exists, this can be omitted.'},
                'force': {'type': 'boolean',
                          'description': 'Rebuild from scratch instead of using the '
                                         'reference cache',
                          'default': False}},
 'additionalProperties': False}
