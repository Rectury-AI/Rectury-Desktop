TOOL_NAME = 'mcp_call_tool'
DESCRIPTION = 'Call a tool on a configured MCP stdio server.'
PROMPT = '''Call a tool on a configured MCP stdio server. This requires
approval because MCP tools may read or mutate external state. Use
mcp_list_tools first when you need the available tool names or schemas. Pass
arguments as an object matching the MCP tool schema.'''
PARAMETERS = {'type': 'object',
 'properties': {'server': {'type': 'string',
                           'description': 'Configured MCP server name'},
                'tool': {'type': 'string', 'description': 'MCP tool name to call'},
                'arguments': {'type': 'object',
                              'description': 'Arguments object for the MCP tool',
                              'additionalProperties': True},
                'timeout': {'type': 'integer',
                            'minimum': 1,
                            'maximum': 60,
                            'description': 'Seconds to wait for the MCP server',
                            'default': 30}},
 'required': ['server', 'tool'],
 'additionalProperties': False}
