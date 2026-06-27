INIT_PROMPT = """Please analyze this codebase and create a RECTURY.md file containing:
1. Build/lint/test commands - especially for running a single test
2. Code style guidelines including imports, formatting, types, naming conventions, error handling, etc.

The file you create will be given to agentic coding agents (such as yourself) that operate in this repository. Make it about 20 lines long.
If there's already a RECTURY.md, improve it.
If there are Cursor rules (in .cursor/rules/ or .cursorrules) or Copilot rules (in .github/copilot-instructions.md), make sure to include them."""


def handle_init_command(workspace: str = ".") -> str:
    """
    Handle /init command
    Return a prompt that instructs the AI to analyze the codebase and
    create/improve RECTURY.md.
    """
    return INIT_PROMPT
