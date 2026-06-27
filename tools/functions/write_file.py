from core.workspace import resolve_workspace_path
from core.checkpoints import create_checkpoint
from core.project_index import build_index
from tools.functions.edit_file import (
    create_diff,
    create_diff_lines,
    create_snippet,
    write_file_atomically,
)
from tools.functions.read_file import get_content_hash, read_text_file


def prepare_write(file_path, content, state):
    if not isinstance(file_path, str) or not file_path.strip():
        return {"error": "file_path must be a non-empty string."}

    if not isinstance(content, str):
        return {"error": "content must be a string."}

    try:
        path = resolve_workspace_path(state.workspace, file_path)
    except Exception as e:
        return {"error": str(e)}

    try:
        before = read_text_file(path) if path.exists() else ""
    except Exception as e:
        return {"error": str(e)}

    if path.exists():
        previous_hash = state.get_file_hash(path)

        if previous_hash is None:
            return {
                "error": (
                    "The file has not been read yet. Read it first before "
                    "writing to it."
                ),
                "code": "file_not_read",
            }

        current_hash = get_content_hash(before)

        if previous_hash != current_hash:
            return {
                "error": (
                    "The file has been modified since it was read. Read it "
                    "again before attempting to write it."
                ),
                "code": "stale_read",
            }

    if before == content:
        return {
            "error": "content is exactly the same as the current file.",
            "code": "no_changes",
        }

    created = not path.exists()
    diff_lines = create_diff_lines(before, content)

    return {
        "success": True,
        "created": created,
        "file_path": str(path),
        "path": path,
        "before_content": before,
        "content": content,
        "diff": create_diff(path, before, content),
        "diff_lines": diff_lines,
        "snippet": create_snippet(before, before if created else "", content),
        "additions": sum(row["type"] == "add" for row in diff_lines),
        "removals": sum(row["type"] == "remove" for row in diff_lines),
    }


def preview_write_file(file_path, content, state):
    prepared = prepare_write(file_path, content, state)

    if not prepared.get("success"):
        return prepared

    return {
        "success": True,
        "created": prepared["created"],
        "file_path": prepared["file_path"],
        "diff": prepared["diff"],
        "diff_lines": prepared["diff_lines"],
        "snippet": prepared["snippet"],
        "additions": prepared["additions"],
        "removals": prepared["removals"],
    }


def write_file(file_path, content, state):
    prepared = prepare_write(file_path, content, state)

    if not prepared.get("success"):
        return prepared

    path = prepared["path"]

    try:
        write_file_atomically(path, prepared["content"])
    except Exception as e:
        return {"error": str(e)}

    checkpoint = create_checkpoint(
        state,
        "write_file",
        path,
        prepared["before_content"],
        prepared["content"],
        prepared["created"],
    )
    state.remember_file(path, get_content_hash(prepared["content"]))
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
        "bytes_written": len(content.encode("utf-8")),
        "created": prepared["created"],
        "diff": prepared["diff"],
        "diff_lines": prepared["diff_lines"],
        "snippet": prepared["snippet"],
        "additions": prepared["additions"],
        "removals": prepared["removals"],
        "summary": (
            f"{'Created' if prepared['created'] else 'Updated'} "
            f"{path} with {prepared['additions']} additions and "
            f"{prepared['removals']} removals."
        ),
    }
