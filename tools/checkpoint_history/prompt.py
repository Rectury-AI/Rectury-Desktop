# Generated from the Rectury tool catalog. Edit this file to change the
# prompt/schema for the `checkpoint_history` tool.

TOOL_NAME = 'checkpoint_history'
PROMPT = 'Show recent checkpointed file changes for this conversation. Use this before undoing or when the user asks what changed.'
PARAMETERS = {'type': 'object',
 'properties': {'limit': {'type': 'integer',
                          'minimum': 1,
                          'maximum': 100,
                          'description': 'Maximum number of recent checkpoints to '
                                         'return'}},
 'additionalProperties': False}
