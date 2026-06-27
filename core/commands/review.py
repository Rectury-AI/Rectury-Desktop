REVIEW_PROMPT = """
You are an expert code reviewer. Follow these steps:

1. If no PR number is provided in the args, use BashTool("gh pr list") to show open PRs
2. If a PR number is provided, use BashTool("gh pr view <number>") to get PR details
3. Use BashTool("gh pr diff <number>") to get the diff
4. Analyze the changes and provide a thorough code review that includes:
   - Overview of what the PR does
   - Analysis of code quality and style
   - Specific suggestions for improvements
"""


def handle_review_command(args: str = "") -> str:
    """
    Handle /review command
    Return a prompt that instructs the AI to review a pull request using gh CLI
    and provide code review feedback.
    """
    if args:
        return REVIEW_PROMPT + f"\n\nPR number provided: {args}"
    return REVIEW_PROMPT
