# Generated from the Rectury tool catalog. Edit this file to change the
# prompt/schema for the `reference_remove` tool.

TOOL_NAME = 'reference_remove'
PROMPT = 'Remove a configured read-only reference path by one-based index or exact path.'
PARAMETERS = {'type': 'object',
 'properties': {'reference': {'type': 'string',
                              'description': 'One-based reference index or exact '
                                             'configured reference path'}},
 'required': ['reference'],
 'additionalProperties': False}
