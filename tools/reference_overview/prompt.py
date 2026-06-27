# Generated from the Rectury tool catalog. Edit this file to change the
# prompt/schema for the `reference_overview` tool.

TOOL_NAME = 'reference_overview'
PROMPT = 'Return a compact overview from a configured read-only reference path index: important files, language counts, symbol count, and import count. Builds or refreshes the external cache when needed.'
PARAMETERS = {'type': 'object',
 'properties': {'reference': {'type': 'string',
                              'description': 'Reference index number or exact '
                                             'configured reference path. If only one '
                                             'reference exists, this can be omitted.'}},
 'additionalProperties': False}
