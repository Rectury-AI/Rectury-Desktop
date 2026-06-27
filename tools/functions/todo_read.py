def todo_read(state):
    """Return the current task list for this conversation."""
    todos = state.get_todos()

    counts = {
        "pending": 0,
        "in_progress": 0,
        "completed": 0,
    }

    for todo in todos:
        status = todo.get("status")
        if status in counts:
            counts[status] += 1

    return {
        "success": True,
        "todos": todos,
        "total": len(todos),
        "counts": counts,
    }
