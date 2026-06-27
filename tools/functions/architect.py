from datetime import datetime

from core.client import create_client
from core.context import build_context
from tools.architect.prompt import ARCHITECT_SYSTEM_PROMPT


def architect(task, state):
    if not isinstance(task, str) or not task.strip():
        return {"error": "task must be a non-empty string."}

    try:
        client, config = create_client()
    except ValueError as error:
        return {"error": str(error), "code": "model_not_configured"}

    response = client.chat.completions.create(
        model=config.model,
        messages=[
            {
                "role": "system",
                "content": (
                    f"{ARCHITECT_SYSTEM_PROMPT}\n\n"
                    f"Workspace: {state.workspace}\n"
                    f"Local time: {datetime.now().astimezone().isoformat(timespec='seconds')}\n\n"
                    "# Project context\n\n"
                    f"{build_context(str(state.workspace))}"
                ),
            },
            {"role": "user", "content": task.strip()},
        ],
    )
    plan = response.choices[0].message.content or ""

    return {
        "success": True,
        "plan": plan.strip(),
        "model": config.model,
    }
