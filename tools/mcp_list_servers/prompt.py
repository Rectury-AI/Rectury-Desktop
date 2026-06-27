TOOL_NAME = 'mcp_list_servers'
DESCRIPTION = 'List configured MCP servers without starting them.'
PROMPT = '''List MCP servers configured in .rectury/mcp.json. This does not
start server processes and does not call external tools. Use this first when
you need to know which MCP servers are available.'''
PARAMETERS = {'type': 'object', 'properties': {}, 'additionalProperties': False}
