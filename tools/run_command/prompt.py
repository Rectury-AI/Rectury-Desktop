TOOL_NAME = 'run_command'
MAX_OUTPUT_LENGTH = 30000
MAX_RENDERED_LINES = 50
BANNED_COMMANDS = [
    'alias',
    'curl',
    'curlie',
    'wget',
    'axel',
    'aria2c',
    'nc',
    'telnet',
    'lynx',
    'w3m',
    'links',
    'httpie',
    'xh',
    'http-prompt',
    'chrome',
    'firefox',
    'safari',
]

PROMPT = f'''Executes a given bash command in a persistent shell session with
optional timeout, ensuring proper handling and security measures.

Before executing the command, follow these steps:

1. Directory verification:
   - If the command will create new directories or files, first use
     list_files_in_dir to verify the parent directory exists and is the correct
     location.

2. Security check:
   - Some commands may require approval. If a command is rejected, explain the
     error to the user.
   - Avoid commands such as: {', '.join(BANNED_COMMANDS)}.

3. Command execution:
   - After ensuring proper quoting, execute the command and capture output.

4. Output processing:
   - If output exceeds {MAX_OUTPUT_LENGTH} characters, it may be truncated.
   - Prepare the output for display to the user.

Usage notes:
- The command argument is required.
- timeout is in seconds.
- All commands share the same shell session. Shell state such as current
  directory and simple environment changes may persist between commands.
- When issuing multiple commands, use ';' or '&&' to separate them.
'''
PARAMETERS = {'type': 'object',
 'properties': {'command': {'type': 'string', 'description': 'Shell command to run'},
                'cwd': {'type': 'string',
                        'description': 'Working directory (relative to workspace)',
                        'default': '.'},
                'timeout': {'type': 'integer',
                            'description': 'Maximum seconds to wait',
                            'default': 30}},
 'required': ['command'],
 'additionalProperties': False}
