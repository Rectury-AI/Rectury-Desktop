TOOL_NAME = 'memory_read'
DESCRIPTION = 'Read project memory and instruction files.'
PROMPT = '''Read project memory and instruction files from the active
workspace, including RECTURY.md, .rectury.md, AGENTS.md,
.cursorrules, and GitHub Copilot instructions when present. Use this when
project guidance, durable local memory, or repository-specific instructions
matter. If file_path is provided, it must point to a memory or instruction file
inside the active workspace.'''
PARAMETERS = {'type': 'object',
 'properties': {'file_path': {'type': 'string',
                              'description': 'Optional specific memory or instruction '
                                             'file path inside the workspace'}},
 'additionalProperties': False}
