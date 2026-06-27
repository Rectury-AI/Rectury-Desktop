# Generated from the Rectury tool catalog. Edit this file to change the
# prompt/schema for the `git_status` tool.

TOOL_NAME = 'git_status'
PROMPT = 'Read git repository state for the active workspace: branch, short status, unstaged/staged diff stats, and latest commit. Use this before edits, reviews, commits, or when user asks what changed.'
PARAMETERS = {'type': 'object',
 'properties': {'path': {'type': 'string',
                         'description': 'Directory inside the active workspace to '
                                        'inspect',
                         'default': '.'}},
 'additionalProperties': False}
