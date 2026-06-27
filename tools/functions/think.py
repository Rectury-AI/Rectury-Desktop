MAX_THOUGHT_CHARS = 8000


def think(thought, state):
    if not isinstance(thought, str) or not thought.strip():
        return {"error": "thought must be a non-empty string."}

    value = thought.strip()
    truncated = len(value) > MAX_THOUGHT_CHARS

    return {
        "success": True,
        "thought": value[:MAX_THOUGHT_CHARS],
        "truncated": truncated,
        "summary": "Thought logged for this reasoning step.",
    }
