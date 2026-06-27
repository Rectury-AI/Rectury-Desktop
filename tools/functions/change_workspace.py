from pathlib import Path


def change_workspace(new_path, state):
    if not isinstance(new_path, str) or not new_path.strip():
        return {"error": "new_path must be a non-empty string."}

    target = Path(new_path).expanduser().resolve()

    if not target.exists() or not target.is_dir():
        return {"error": f"directory does not exist: {target}"}

    # Update the active workspace.
    state.workspace = target

    return {
        "success": True,
        "new_workspace": str(target),
    }
