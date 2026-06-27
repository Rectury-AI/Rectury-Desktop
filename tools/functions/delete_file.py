from core.checkpoints import create_checkpoint
from core.project_index import build_index
from core.workspace import resolve_workspace_path
from tools.functions.edit_file import create_diff, create_diff_lines
from tools.functions.read_file import read_text_file


def prepare_delete_file(file_path, state):
    if not isinstance(file_path, str) or not file_path.strip():
        return {"error": "file_path must be a non-empty string."}

    try:
        path = resolve_workspace_path(state.workspace, file_path)
    except ValueError as error:
        return {"error": str(error), "code": "invalid_path"}

    if not path.exists():
        return {"error": f"file does not exist: {path}", "code": "missing_file"}

    if not path.is_file():
        return {
            "error": f"delete_file can only delete regular files: {path}",
            "code": "not_regular_file",
        }

    try:
        before = read_text_file(path)
    except Exception as error:
        return {"error": str(error), "code": "read_failed"}

    diff_lines = create_diff_lines(before, "")

    return {
        "success": True,
        "file_path": str(path),
        "path": path,
        "before_content": before,
        "diff": create_diff(path, before, ""),
        "diff_lines": diff_lines,
        "additions": 0,
        "removals": sum(row["type"] == "remove" for row in diff_lines),
    }


def preview_delete_file(file_path, state):
    prepared = prepare_delete_file(file_path, state)

    if not prepared.get("success"):
        return prepared

    return {
        "success": True,
        "file_path": prepared["file_path"],
        "diff": prepared["diff"],
        "diff_lines": prepared["diff_lines"],
        "additions": prepared["additions"],
        "removals": prepared["removals"],
    }


def delete_file(file_path, state):
    prepared = prepare_delete_file(file_path, state)

    if not prepared.get("success"):
        return prepared

    path = prepared["path"]

    try:
        path.unlink()
    except OSError as error:
        return {"error": str(error), "code": "delete_failed"}

    checkpoint = create_checkpoint(
        state,
        "delete_file",
        path,
        prepared["before_content"],
        "",
        False,
    )
    checkpoint["deleted"] = True
    state.forget_file(path)
    index_status = "skipped"

    try:
        build_index(state.workspace, force=False)
        index_status = "refreshed"
    except Exception:
        index_status = "error"

    return {
        "success": True,
        "file_path": str(path),
        "checkpoint_id": checkpoint["id"],
        "index_status": index_status,
        "diff": prepared["diff"],
        "diff_lines": prepared["diff_lines"],
        "additions": prepared["additions"],
        "removals": prepared["removals"],
        "summary": f"Deleted {path}.",
    }
