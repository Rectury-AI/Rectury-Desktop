TOOL_NAME = 'mcp_list_tools'
DESCRIPTION = 'Start a configured MCP stdio server and list its tools.'
PROMPT = '''Start a configured MCP stdio server from .rectury/mcp.json and list
the tools it exposes. This requires approval because it launches a local
process. Use mcp_list_servers first if you do not know the configured server
name.'''
PARAMETERS = {'type': 'object',
 'properties': {'server': {'type': 'string',
                           'description': 'Configured MCP server name'},
                'timeout': {'type': 'integer',
                            'minimum': 1,
                            'maximum': 60,
                            'description': 'Seconds to wait for the MCP server',
                            'default': 15}},
 'required': ['server'],
 'additionalProperties': False}
