from tools.registry import TOOLS_REGISTRY

def run_tool(tool_name, arguments):
    tool = TOOLS_REGISTRY.get(tool_name)

    if tool is None:
        raise ValueError(f"Tool '{tool_name}' not found in the registry.")

    return tool(**arguments)