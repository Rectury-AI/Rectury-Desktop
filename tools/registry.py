from tools.manifest import TOOL_MODULES


TOOLS_REGISTRY = {
    tool.name: tool.function
    for tool in TOOL_MODULES
}
