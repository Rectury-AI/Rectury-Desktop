from core.checkpoints import create_checkpoint
from core.project_index import build_index
from core.workspace import resolve_workspace_path
from tools.functions.edit_file import (
    create_diff,
    create_diff_lines,
    create_snippet,
    write_file_atomically,
)
from tools.functions.read_file import get_content_hash, read_text_file


MAX_EDITS = 50


def prepare_multi_edit(file_path, edits, state):
    if not isinstance(file_path, str) or not file_path.strip():
        return {"error": "file_path must be a non-empty string."}

    if not isinstance(edits, list) or not edits:
        return {"error": "edits must be a non-empty list."}

    if len(edits) > MAX_EDITS:
        return {"error": f"multi_edit supports at most {MAX_EDITS} edits."}

    try:
        path = resolve_workspace_path(state.workspace, file_path)
    except ValueError as error:
        return {"error": str(error)}

    if not path.exists():
        return {
            "error": "File does not exist. Use edit_file or write_file to create it.",
            "code": "file_not_found",
        }

    try:
        content = read_text_file(path)
    except (OSError, UnicodeError) as error:
        return {"error": str(error)}

    previous_hash = state.get_file_hash(path)

    if previous_hash is None:
        return {
            "error": "The file has not been read yet. Read it before editing.",
            "code": "file_not_read",
        }

    current_hash = get_content_hash(content)

    if previous_hash != current_hash:
        return {
            "error": (
                "The file changed after it was read. Read it again before "
                "editing."
            ),
            "code": "stale_read",
        }

    updated_content = content
    normalized_edits = []

    for index, edit in enumerate(edits, start=1):
        if not isinstance(edit, dict):
            return {"error": f"edit {index} must be an object."}

        old_text = edit.get("old_text")
        new_text = edit.get("new_text")

        if not isinstance(old_text, str) or old_text == "":
            return {
                "error": f"edit {index} old_text must be a non-empty string.",
                "code": "invalid_edit",
            }

        if not isinstance(new_text, str):
            return {
                "error": f"edit {index} new_text must be a string.",
                "code": "invalid_edit",
            }

        if old_text == new_text:
            return {
                "error": f"edit {index} old_text and new_text are identical.",
                "code": "invalid_edit",
            }

        matches = updated_content.count(old_text)

        if matches == 0:
            return {
                "error": f"edit {index} text was not found.",
                "code": "text_not_found",
                "edit_index": index,
            }

        if matches > 1:
            return {
                "error": (
                    f"edit {index} text appears {matches} times. Include "
                    "more surrounding lines."
                ),
                "code": "ambiguous_edit",
                "edit_index": index,
                "matches": matches,
            }

        updated_content = updated_content.replace(old_text, new_text, 1)
        normalized_edits.append(
            {
                "old_text": old_text,
                "new_text": new_text,
            }
        )

    diff_lines = create_diff_lines(content, updated_content)
    first_edit = normalized_edits[0]

    return {
        "success": True,
        "created": False,
        "file_path": str(path),
        "path": path,
        "before_content": content,
        "updated_content": updated_content,
        "edits": normalized_edits,
        "edit_count": len(normalized_edits),
        "diff": create_diff(path, content, updated_content),
        "diff_lines": diff_lines,
        "snippet": create_snippet(
            content,
            first_edit["old_text"],
            first_edit["new_text"],
        ),
        "additions": sum(row["type"] == "add" for row in diff_lines),
        "removals": sum(row["type"] == "remove" for row in diff_lines),
    }


def preview_multi_edit(file_path, edits, state):
    prepared = prepare_multi_edit(file_path, edits, state)

    if not prepared.get("success"):
        return prepared

    return {
        "success": True,
        "file_path": prepared["file_path"],
        "edit_count": prepared["edit_count"],
        "diff": prepared["diff"],
        "diff_lines": prepared["diff_lines"],
        "snippet": prepared["snippet"],
        "additions": prepared["additions"],
        "removals": prepared["removals"],
    }


def multi_edit(file_path, edits, state):
    prepared = prepare_multi_edit(file_path, edits, state)

    if not prepared.get("success"):
        return prepared

    path = prepared["path"]
    updated_content = prepared["updated_content"]

    try:
        write_file_atomically(path, updated_content)
    except OSError as error:
        return {"error": str(error)}

    checkpoint = create_checkpoint(
        state,
        "multi_edit",
        path,
        prepared["before_content"],
        updated_content,
        False,
    )
    state.remember_file(path, get_content_hash(updated_content))
    index_status = "skipped"

    try:
        build_index(state.workspace, force=False)
        index_status = "refreshed"
    except Exception:
        index_status = "error"

    return {
        "success": True,
        "created": False,
        "file_path": str(path),
        "checkpoint_id": checkpoint["id"],
        "index_status": index_status,
        "edit_count": prepared["edit_count"],
        "diff": prepared["diff"],
        "diff_lines": prepared["diff_lines"],
        "snippet": prepared["snippet"],
        "additions": prepared["additions"],
        "removals": prepared["removals"],
    }
