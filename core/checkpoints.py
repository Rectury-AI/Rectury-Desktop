import os
import stat
import tempfile
from datetime import datetime
from difflib import SequenceMatcher, unified_diff
from uuid import uuid4

from core.workspace import resolve_workspace_path
from tools.functions.read_file import get_content_hash, read_text_file


def create_diff(file_path, before, after):
    return "".join(
        unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=f"{file_path}:before",
            tofile=f"{file_path}:after",
        )
    )


def create_diff_lines(before, after, context_lines=3):
    before_lines = before.splitlines()
    after_lines = after.splitlines()
    matcher = SequenceMatcher(None, before_lines, after_lines)
    rows = []

    for group in matcher.get_grouped_opcodes(context_lines):
        if rows:
            rows.append({"type": "separator"})

        for tag, old_start, old_end, new_start, new_end in group:
            if tag == "equal":
                for offset, line in enumerate(before_lines[old_start:old_end]):
                    rows.append(
                        {
                            "type": "context",
                            "old_line": old_start + offset + 1,
                            "new_line": new_start + offset + 1,
                            "content": line,
                        }
                    )
                continue

            if tag in {"replace", "delete"}:
                for offset, line in enumerate(before_lines[old_start:old_end]):
                    rows.append(
                        {
                            "type": "remove",
                            "old_line": old_start + offset + 1,
                            "new_line": None,
                            "content": line,
                        }
                    )

            if tag in {"replace", "insert"}:
                for offset, line in enumerate(after_lines[new_start:new_end]):
                    rows.append(
                        {
                            "type": "add",
                            "old_line": None,
                            "new_line": new_start + offset + 1,
                            "content": line,
                        }
                    )

    return rows


def write_file_atomically(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    file_mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o644
    temporary_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            dir=path.parent,
            delete=False,
        ) as temporary_file:
            temporary_file.write(content)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
            temporary_path = temporary_file.name

        os.chmod(temporary_path, file_mode)
        os.replace(temporary_path, path)
    except OSError:
        if temporary_path:
            try:
                os.unlink(temporary_path)
            except OSError:
                pass
        raise


def current_timestamp():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def create_checkpoint(state, tool_name, file_path, before, after, created):
    checkpoint = {
        "id": uuid4().hex[:10],
        "created_at": current_timestamp(),
        "tool": tool_name,
        "file_path": str(file_path),
        "created": bool(created),
        "before": before,
        "after": after,
        "additions": sum(
            row["type"] == "add"
            for row in create_diff_lines(before, after)
        ),
        "removals": sum(
            row["type"] == "remove"
            for row in create_diff_lines(before, after)
        ),
    }
    state.add_checkpoint(checkpoint)
    return checkpoint


def summarize_checkpoint(checkpoint):
    if checkpoint.get("deleted"):
        action = "deleted"
    elif checkpoint.get("created"):
        action = "created"
    else:
        action = "modified"

    return {
        "id": checkpoint.get("id"),
        "created_at": checkpoint.get("created_at"),
        "tool": checkpoint.get("tool"),
        "file_path": checkpoint.get("file_path"),
        "action": action,
        "additions": checkpoint.get("additions", 0),
        "removals": checkpoint.get("removals", 0),
    }


def checkpoint_history(state, limit=20):
    try:
        limit = max(1, min(int(limit), 100))
    except (TypeError, ValueError):
        limit = 20

    checkpoints = state.get_checkpoints()
    visible = list(reversed(checkpoints))[:limit]

    return {
        "success": True,
        "total": len(checkpoints),
        "checkpoints": [
            summarize_checkpoint(checkpoint)
            for checkpoint in visible
        ],
    }


def preview_undo_last_change(state):
    checkpoints = state.get_checkpoints()

    if not checkpoints:
        return {
            "error": "There are no checkpoints to undo.",
            "code": "no_checkpoints",
        }

    checkpoint = checkpoints[-1]
    path = resolve_workspace_path(state.workspace, checkpoint["file_path"])
    before = checkpoint.get("before", "")
    after = checkpoint.get("after", "")

    if checkpoint.get("deleted"):
        current = read_text_file(path) if path.exists() else ""
        target = before
    elif checkpoint.get("created"):
        current = read_text_file(path) if path.exists() else ""
        target = ""
    else:
        current = read_text_file(path)
        target = before

    if current != after:
        return {
            "error": (
                "The file changed after the checkpoint was created. "
                "Read the file and decide how to proceed before undoing."
            ),
            "code": "stale_checkpoint",
            "file_path": str(path),
        }

    return {
        "success": True,
        "checkpoint": summarize_checkpoint(checkpoint),
        "file_path": str(path),
        "created": checkpoint.get("created", False),
        "diff": create_diff(path, current, target),
        "diff_lines": create_diff_lines(current, target),
        "additions": sum(
            row["type"] == "add"
            for row in create_diff_lines(current, target)
        ),
        "removals": sum(
            row["type"] == "remove"
            for row in create_diff_lines(current, target)
        ),
    }


def undo_last_change(state):
    preview = preview_undo_last_change(state)

    if not preview.get("success"):
        return preview

    checkpoint = state.pop_checkpoint()
    path = resolve_workspace_path(state.workspace, checkpoint["file_path"])

    try:
        if checkpoint.get("deleted"):
            write_file_atomically(path, checkpoint.get("before", ""))
            restored_hash = get_content_hash(checkpoint.get("before", ""))
        elif checkpoint.get("created"):
            if path.exists():
                path.unlink()
            restored_hash = None
        else:
            write_file_atomically(path, checkpoint.get("before", ""))
            restored_hash = get_content_hash(checkpoint.get("before", ""))
    except OSError as error:
        state.add_checkpoint(checkpoint)
        return {"error": str(error), "code": "undo_failed"}

    if restored_hash is not None:
        state.remember_file(path, restored_hash)
    else:
        state.forget_file(path)

    return {
        "success": True,
        "undone": preview["checkpoint"],
        "file_path": str(path),
        "deleted": bool(checkpoint.get("created")),
        "restored": bool(checkpoint.get("deleted")),
        "diff": preview["diff"],
        "diff_lines": preview["diff_lines"],
        "additions": preview["additions"],
        "removals": preview["removals"],
        "remaining_checkpoints": len(state.get_checkpoints()),
    }
