from core.checkpoints import create_checkpoint
from core.context import PROJECT_INSTRUCTION_FILES
from core.project_index import build_index
from core.workspace import resolve_workspace_path
from tools.functions.edit_file import (
    create_diff,
    create_diff_lines,
    write_file_atomically,
)
from tools.functions.read_file import get_content_hash, read_text_file


WRITABLE_MEMORY_FILES = {"RECTURY.md", ".rectury.md"}


def memory_read(state, file_path=None):
    if file_path:
        try:
            path = resolve_workspace_path(state.workspace, file_path)
        except ValueError as error:
            return {"error": str(error)}

        if not path.exists() or not path.is_file():
            return {"error": f"memory file does not exist: {path}"}

        try:
            content = read_text_file(path)
        except (OSError, UnicodeError) as error:
            return {"error": str(error)}

        state.remember_file(path, get_content_hash(content))
        return {
            "success": True,
            "file_path": str(path),
            "files": [str(path.relative_to(state.workspace))],
            "content": content,
        }

    sections = []
    files = []

    for name in PROJECT_INSTRUCTION_FILES:
        path = state.workspace / name

        if not path.exists() or not path.is_file():
            continue

        try:
            content = read_text_file(path)
        except (OSError, UnicodeError):
            continue

        state.remember_file(path, get_content_hash(content))
        files.append(name)
        sections.append(f"## {name}\n\n{content}")

    return {
        "success": True,
        "files": files,
        "content": (
            "\n\n".join(sections)
            if sections
            else "No project memory or instruction files found."
        ),
    }


def resolve_memory_write_path(state, file_path):
    selected = file_path or "RECTURY.md"

    if selected not in WRITABLE_MEMORY_FILES:
        raise ValueError(
            "memory_write can only update RECTURY.md or .rectury.md."
        )

    return resolve_workspace_path(state.workspace, selected)


def prepare_memory_write(content, state, file_path="RECTURY.md", mode="append"):
    if not isinstance(content, str) or not content.strip():
        return {"error": "content must be a non-empty string."}

    if mode not in {"append", "replace"}:
        return {"error": "mode must be append or replace."}

    try:
        path = resolve_memory_write_path(state, file_path)
    except ValueError as error:
        return {"error": str(error)}

    try:
        before = read_text_file(path) if path.exists() else ""
    except (OSError, UnicodeError) as error:
        return {"error": str(error)}

    if mode == "append":
        prefix = "" if not before or before.endswith("\n") else "\n"
        suffix = "" if content.endswith("\n") else "\n"
        after = before + prefix + content + suffix
    else:
        after = content

    if before == after:
        return {
            "error": "content is exactly the same as the current memory file.",
            "code": "no_changes",
        }

    diff_lines = create_diff_lines(before, after)

    return {
        "success": True,
        "created": not path.exists(),
        "file_path": str(path),
        "path": path,
        "before_content": before,
        "updated_content": after,
        "mode": mode,
        "diff": create_diff(path, before, after),
        "diff_lines": diff_lines,
        "additions": sum(row["type"] == "add" for row in diff_lines),
        "removals": sum(row["type"] == "remove" for row in diff_lines),
    }


def preview_memory_write(content, state, file_path="RECTURY.md", mode="append"):
    prepared = prepare_memory_write(content, state, file_path, mode)

    if not prepared.get("success"):
        return prepared

    return {
        "success": True,
        "created": prepared["created"],
        "file_path": prepared["file_path"],
        "mode": prepared["mode"],
        "diff": prepared["diff"],
        "diff_lines": prepared["diff_lines"],
        "additions": prepared["additions"],
        "removals": prepared["removals"],
    }


def memory_write(content, state, file_path="RECTURY.md", mode="append"):
    prepared = prepare_memory_write(content, state, file_path, mode)

    if not prepared.get("success"):
        return prepared

    path = prepared["path"]

    try:
        write_file_atomically(path, prepared["updated_content"])
    except OSError as error:
        return {"error": str(error)}

    checkpoint = create_checkpoint(
        state,
        "memory_write",
        path,
        prepared["before_content"],
        prepared["updated_content"],
        prepared["created"],
    )
    state.remember_file(path, get_content_hash(prepared["updated_content"]))
    index_status = "skipped"

    try:
        build_index(state.workspace, force=False)
        index_status = "refreshed"
    except Exception:
        index_status = "error"

    return {
        "success": True,
        "created": prepared["created"],
        "file_path": str(path),
        "checkpoint_id": checkpoint["id"],
        "index_status": index_status,
        "mode": prepared["mode"],
        "diff": prepared["diff"],
        "diff_lines": prepared["diff_lines"],
        "additions": prepared["additions"],
        "removals": prepared["removals"],
        "summary": f"Updated project memory in {path.name}.",
    }
