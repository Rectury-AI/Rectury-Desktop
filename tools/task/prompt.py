# Generated from the Rectury tool catalog. Edit this file to change the
# prompt/schema for the `task` tool.

from core.prompts import PRODUCT_NAME, create_env_info


TOOL_NAME = 'task'
PROMPT = '''Launch a focused read-only subagent with its own context and tool
loop. Use this when searching for a keyword, locating relevant files, or
summarizing architecture and you are not confident a single glob/grep/read will
find the right answer.

Usage notes:
1. Give the subagent a detailed, self-contained investigation prompt.
2. Ask for exact file paths and evidence in the final report.
3. The subagent is stateless and cannot be messaged again after it returns.
4. In normal permission modes it can only use read-only tools, so it cannot
   modify files or run commands. Use direct tools when edits or commands are
   required.
5. The subagent result is not shown directly to the user; summarize the useful
   findings in your own final response.
'''
PARAMETERS = {'type': 'object',
 'properties': {'prompt': {'type': 'string',
                           'description': 'Focused investigation task for the '
                                          'subagent'},
                'max_rounds': {'type': 'integer',
                               'minimum': 1,
                               'maximum': 12,
                               'description': 'Maximum subagent tool rounds',
                               'default': 6}},
 'required': ['prompt'],
 'additionalProperties': False}


def create_agent_prompt(
    workspace,
    local_time,
    project_context="",
    provider="",
    model="",
):
    context_section = (
        f"\n\n# Project context\n\n{project_context}"
        if project_context
        else ""
    )
    return (
        f"You are a focused read-only subagent for {PRODUCT_NAME}. "
        "Investigate the requested topic using available read-only tools, then "
        "return a concise report with relevant file paths and evidence. Do not "
        "modify files, run commands, or ask the user questions. If evidence is "
        "missing, say exactly what is missing.\n\n"
        "Any file paths in your final report must be absolute.\n\n"
        f"{create_env_info(workspace, local_time, provider, model)}"
        f"{context_section}"
    )
