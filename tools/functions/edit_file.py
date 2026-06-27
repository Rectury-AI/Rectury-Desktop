import os
import stat
import tempfile
from difflib import SequenceMatcher, unified_diff

from core.checkpoints import create_checkpoint
from core.project_index import build_index
from core.workspace import resolve_workspace_path
from tools.functions.read_file import get_content_hash, read_text_file


SNIPPET_CONTEXT_LINES = 4


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
                for offset, line in enumerate(
                    before_lines[old_start:old_end]
                ):
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
                for offset, line in enumerate(
                    before_lines[old_start:old_end]
                ):
                    rows.append(
                        {
                            "type": "remove",
                            "old_line": old_start + offset + 1,
                            "new_line": None,
                            "content": line,
                        }
                    )

            if tag in {"replace", "insert"}:
                for offset, line in enumerate(
                    after_lines[new_start:new_end]
                ):
                    rows.append(
                        {
                            "type": "add",
                            "old_line": None,
                            "new_line": new_start + offset + 1,
                            "content": line,
                        }
                    )

    return rows


def create_snippet(before, old_text, new_text):
    if old_text == "":
        selected_lines = new_text.splitlines()[
            : SNIPPET_CONTEXT_LINES * 2 + 1
        ]
        return "\n".join(
            f"{line_number:>6} | {line}"
            for line_number, line in enumerate(
                selected_lines,
                start=1,
            )
        )

    text_before_change = before.split(old_text, 1)[0]
    changed_line = len(text_before_change.splitlines())
    updated_content = before.replace(old_text, new_text, 1)
    updated_lines = updated_content.splitlines()
    new_line_count = max(1, len(new_text.splitlines()))
    start = max(0, changed_line - SNIPPET_CONTEXT_LINES)
    end = changed_line + new_line_count + SNIPPET_CONTEXT_LINES
    selected_lines = updated_lines[start:end]

    return "\n".join(
        f"{line_number:>6} | {line}"
        for line_number, line in enumerate(selected_lines, start=start + 1)
    )


def write_file_atomically(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    file_mode = (
        stat.S_IMODE(path.stat().st_mode)
        if path.exists()
        else 0o644
    )
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


def prepare_edit(file_path, old_text, new_text, state):
    if not isinstance(old_text, str):
        return {"error": "old_text must be a string."}

    if not isinstance(new_text, str):
        return {"error": "new_text must be a string."}

    if old_text == new_text:
        return {"error": "old_text and new_text are exactly the same."}

    try:
        path = resolve_workspace_path(state.workspace, file_path)
    except ValueError as error:
        return {"error": str(error)}

    if old_text == "":
        if path.exists():
            return {
                "error": (
                    "Cannot create the file because it already exists. "
                    "Read it and provide a unique old_text instead."
                ),
                "code": "file_already_exists",
            }

        content = ""
        updated_content = new_text
        created = True
    else:
        try:
            content = read_text_file(path)
        except (OSError, UnicodeError) as error:
            return {"error": str(error)}

        previous_hash = state.get_file_hash(path)

        if previous_hash is None:
            return {
                "error": (
                    "The file has not been read yet. "
                    "Read it before editing."
                ),
                "code": "file_not_read",
            }

        current_hash = get_content_hash(content)

        if previous_hash != current_hash:
            return {
                "error": (
                    "The file changed after it was read. Read it again "
                    "before editing."
                ),
                "code": "stale_read",
            }

        matches = content.count(old_text)

        if matches == 0:
            return {
                "error": (
                    "The exact text was not found. "
                    "Read the file again."
                ),
                "code": "text_not_found",
            }

        if matches > 1:
            return {
                "error": (
                    f"The exact text appears {matches} times. Include more "
                    "surrounding lines."
                ),
                "code": "ambiguous_edit",
                "matches": matches,
            }

        if new_text == "" and not old_text.endswith("\n"):
            text_to_replace = (
                old_text + "\n"
                if old_text + "\n" in content
                else old_text
            )
        else:
            text_to_replace = old_text

        updated_content = content.replace(
            text_to_replace,
            new_text,
            1,
        )
        created = False

    return {
        "success": True,
        "created": created,
        "file_path": str(path),
        "path": path,
        "before_content": content,
        "updated_content": updated_content,
        "diff": create_diff(path, content, updated_content),
        "diff_lines": create_diff_lines(content, updated_content),
        "snippet": create_snippet(content, old_text, new_text),
    }


def preview_edit_file(file_path, old_text, new_text, state):
    prepared = prepare_edit(file_path, old_text, new_text, state)

    if not prepared.get("success"):
        return prepared

    return {
        "success": True,
        "created": prepared["created"],
        "file_path": prepared["file_path"],
        "diff": prepared["diff"],
        "diff_lines": prepared["diff_lines"],
        "snippet": prepared["snippet"],
    }


def edit_file(file_path, old_text, new_text, state):
    prepared = prepare_edit(file_path, old_text, new_text, state)

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
        "edit_file",
        path,
        prepared["before_content"],
        updated_content,
        prepared["created"],
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
        "created": prepared["created"],
        "file_path": str(path),
        "checkpoint_id": checkpoint["id"],
        "index_status": index_status,
        "diff": prepared["diff"],
        "diff_lines": prepared["diff_lines"],
        "snippet": prepared["snippet"],
        "additions": sum(
            row["type"] == "add"
            for row in prepared["diff_lines"]
        ),
        "removals": sum(
            row["type"] == "remove"
            for row in prepared["diff_lines"]
        ),
    }
