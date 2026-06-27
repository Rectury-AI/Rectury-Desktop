def self_reflect(state):
    """Return information about the agent's own tools and structure."""
    from tools.registry import TOOLS_REGISTRY

    return {
        "success": True,
        "available_tools": sorted(TOOLS_REGISTRY.keys()),
        "description": (
            "Rectury is an interactive local CLI agent for software "
            "engineering tasks. It can keep a per-conversation task list "
            "with todo_read and todo_write when work has multiple steps. "
            "File edits are checkpointed and can be inspected or undone. "
            "It supports focused subagents, architecture planning, MCP "
            "servers, project memory, notebooks, images, indexed search, "
            "git status inspection, glob/grep, and streamed shell commands "
            "with persistent cwd and simple environment updates."
        ),
    }
