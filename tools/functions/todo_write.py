from uuid import uuid4


VALID_STATUSES = {"pending", "in_progress", "completed"}


def normalize_todo(todo, index):
    if not isinstance(todo, dict):
        raise ValueError(f"Todo #{index + 1} must be an object.")

    content = str(todo.get("content", "")).strip()
    status = str(todo.get("status", "")).strip()
    todo_id = str(todo.get("id", "")).strip() or uuid4().hex[:8]

    if not content:
        raise ValueError(f"Todo #{index + 1} must include non-empty content.")

    if status not in VALID_STATUSES:
        raise ValueError(
            f"Todo #{index + 1} has invalid status '{status}'. "
            "Use pending, in_progress, or completed."
        )

    return {
        "id": todo_id,
        "content": content,
        "status": status,
    }


def todo_write(todos, state):
    """Replace the current task list for this conversation."""
    if not isinstance(todos, list):
        raise ValueError("todos must be a list.")

    normalized = [
        normalize_todo(todo, index)
        for index, todo in enumerate(todos)
    ]

    in_progress = [
        todo for todo in normalized
        if todo["status"] == "in_progress"
    ]

    if len(in_progress) > 1:
        raise ValueError("Only one todo can be in_progress at a time.")

    state.set_todos(normalized)

    counts = {
        "pending": 0,
        "in_progress": 0,
        "completed": 0,
    }

    for todo in normalized:
        counts[todo["status"]] += 1

    return {
        "success": True,
        "todos": normalized,
        "total": len(normalized),
        "counts": counts,
    }
