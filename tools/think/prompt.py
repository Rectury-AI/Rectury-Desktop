TOOL_NAME = 'think'
DESCRIPTION = (
    'No-op tool that records a reasoning note for difficult multi-step work.'
)
PROMPT = '''Use this tool to think through something. It does not obtain new
information or change the repository; it records a concise reasoning note.

Common uses:
1. Brainstorm several fixes after locating a bug.
2. Interpret failing tests and compare recovery paths.
3. Plan a complex refactor and note tradeoffs.
4. Work through architecture decisions for a new feature.
5. Organize hypotheses while debugging a complicated issue.

Do not use this for routine work where the next action is obvious.
'''
PARAMETERS = {'type': 'object',
 'properties': {'thought': {'type': 'string',
                            'description': 'Concise reasoning note for the current '
                                           'task'}},
 'required': ['thought'],
 'additionalProperties': False}
