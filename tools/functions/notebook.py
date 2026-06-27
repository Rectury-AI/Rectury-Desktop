import json

from core.checkpoints import create_checkpoint
from core.workspace import resolve_workspace_path
from tools.functions.edit_file import (
    create_diff,
    create_diff_lines,
    write_file_atomically,
)
from tools.functions.read_file import get_content_hash, read_text_file


MAX_CELLS = 200
MAX_CELL_SOURCE_CHARS = 4000
MAX_OUTPUT_CHARS = 2000


def normalize_source(source):
    if isinstance(source, list):
        return "".join(str(part) for part in source)

    return str(source or "")


def source_like_existing(original_source, new_source):
    if isinstance(original_source, list):
        if not new_source:
            return []

        lines = new_source.splitlines(keepends=True)

        if new_source and not new_source.endswith(("\n", "\r")):
            return lines

        return lines

    return new_source


def load_notebook(path):
    raw = read_text_file(path)
    return raw, json.loads(raw)


def dump_notebook(notebook):
    return json.dumps(notebook, ensure_ascii=False, indent=2) + "\n"


def make_cell(cell_type, source):
    if cell_type not in {"code", "markdown", "raw"}:
        raise ValueError("cell_type must be code, markdown, or raw.")

    cell = {
        "cell_type": cell_type,
        "metadata": {},
        "source": source.splitlines(keepends=True),
    }

    if cell_type == "code":
        cell["execution_count"] = None
        cell["outputs"] = []

    return cell


def summarize_output(output):
    output_type = output.get("output_type", "output")

    if "text" in output:
        text = normalize_source(output.get("text"))
    elif "ename" in output or "evalue" in output:
        text = f"{output.get('ename', '')}: {output.get('evalue', '')}".strip()
    elif "data" in output:
        data = output.get("data") or {}
        text = ", ".join(sorted(str(key) for key in data.keys()))
    else:
        text = ""

    if len(text) > MAX_OUTPUT_CHARS:
        text = text[:MAX_OUTPUT_CHARS].rstrip() + "\n... output truncated ..."

    return {
        "type": output_type,
        "text": text,
    }


def notebook_cells_for_model(notebook):
    cells = []

    for index, cell in enumerate(notebook.get("cells", [])[:MAX_CELLS]):
        source = normalize_source(cell.get("source"))

        if len(source) > MAX_CELL_SOURCE_CHARS:
            source = (
                source[:MAX_CELL_SOURCE_CHARS].rstrip()
                + "\n... cell source truncated ..."
            )

        cells.append(
            {
                "index": index,
                "type": cell.get("cell_type", "unknown"),
                "source": source,
                "outputs": [
                    summarize_output(output)
                    for output in cell.get("outputs", [])[:10]
                ],
            }
        )

    return cells


def read_notebook(file_path, state):
    try:
        path = resolve_workspace_path(state.workspace, file_path)
    except ValueError as error:
        return {"error": str(error)}

    if path.suffix != ".ipynb":
        return {"error": "file_path must point to a .ipynb file."}

    if not path.exists():
        return {"error": f"notebook does not exist: {path}"}

    try:
        raw, notebook = load_notebook(path)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        return {"error": str(error)}

    state.remember_file(path, get_content_hash(raw))
    cells = notebook_cells_for_model(notebook)

    return {
        "success": True,
        "file_path": str(path),
        "cells": cells,
        "total_cells": len(notebook.get("cells", [])),
        "truncated": len(notebook.get("cells", [])) > len(cells),
    }


def prepare_edit_notebook(file_path, cell_index, new_source, state, cell_type=None):
    if not isinstance(cell_index, int) or cell_index < 0:
        return {"error": "cell_index must be a non-negative integer."}

    if not isinstance(new_source, str):
        return {"error": "new_source must be a string."}

    try:
        path = resolve_workspace_path(state.workspace, file_path)
    except ValueError as error:
        return {"error": str(error)}

    if path.suffix != ".ipynb":
        return {"error": "file_path must point to a .ipynb file."}

    if not path.exists():
        return {"error": f"notebook does not exist: {path}"}

    try:
        before, notebook = load_notebook(path)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        return {"error": str(error)}

    previous_hash = state.get_file_hash(path)

    if previous_hash is None:
        return {
            "error": "The notebook has not been read yet. Read it before editing.",
            "code": "file_not_read",
        }

    current_hash = get_content_hash(before)

    if previous_hash != current_hash:
        return {
            "error": (
                "The notebook changed after it was read. Read it again before "
                "editing."
            ),
            "code": "stale_read",
        }

    cells = notebook.get("cells", [])

    if cell_index >= len(cells):
        return {
            "error": f"cell_index {cell_index} is outside the notebook.",
            "code": "cell_not_found",
        }

    cell = cells[cell_index]
    old_source = normalize_source(cell.get("source"))

    if old_source == new_source:
        return {
            "error": "new_source is exactly the same as the current cell source.",
            "code": "no_changes",
        }

    cell["source"] = source_like_existing(cell.get("source"), new_source)
    if cell_type in {"code", "markdown", "raw"}:
        cell["cell_type"] = cell_type

    if cell.get("cell_type") == "code":
        cell["execution_count"] = None
        cell["outputs"] = []
    else:
        cell.pop("execution_count", None)
        cell.pop("outputs", None)

    after = dump_notebook(notebook)
    diff_lines = create_diff_lines(before, after)

    return {
        "success": True,
        "created": False,
        "file_path": str(path),
        "path": path,
        "before_content": before,
        "updated_content": after,
        "cell_index": cell_index,
        "old_source": old_source,
        "new_source": new_source,
        "diff": create_diff(path, before, after),
        "diff_lines": diff_lines,
        "additions": sum(row["type"] == "add" for row in diff_lines),
        "removals": sum(row["type"] == "remove" for row in diff_lines),
    }


def preview_edit_notebook(file_path, cell_index, new_source, state, cell_type=None):
    prepared = prepare_edit_notebook(
        file_path,
        cell_index,
        new_source,
        state,
        cell_type=cell_type,
    )

    if not prepared.get("success"):
        return prepared

    return {
        "success": True,
        "file_path": prepared["file_path"],
        "cell_index": prepared["cell_index"],
        "diff": prepared["diff"],
        "diff_lines": prepared["diff_lines"],
        "additions": prepared["additions"],
        "removals": prepared["removals"],
    }


def edit_notebook(file_path, cell_index, new_source, state, cell_type=None):
    prepared = prepare_edit_notebook(
        file_path,
        cell_index,
        new_source,
        state,
        cell_type=cell_type,
    )

    if not prepared.get("success"):
        return prepared

    path = prepared["path"]

    try:
        write_file_atomically(path, prepared["updated_content"])
    except OSError as error:
        return {"error": str(error)}

    checkpoint = create_checkpoint(
        state,
        "edit_notebook",
        path,
        prepared["before_content"],
        prepared["updated_content"],
        False,
    )
    state.remember_file(path, get_content_hash(prepared["updated_content"]))

    return {
        "success": True,
        "file_path": str(path),
        "checkpoint_id": checkpoint["id"],
        "cell_index": prepared["cell_index"],
        "diff": prepared["diff"],
        "diff_lines": prepared["diff_lines"],
        "additions": prepared["additions"],
        "removals": prepared["removals"],
        "summary": f"Updated notebook cell {prepared['cell_index']}.",
    }


def prepare_insert_notebook_cell(
    file_path,
    cell_index,
    cell_type,
    source,
    state,
):
    if not isinstance(cell_index, int) or cell_index < 0:
        return {"error": "cell_index must be a non-negative integer."}

    if not isinstance(source, str):
        return {"error": "source must be a string."}

    try:
        path = resolve_workspace_path(state.workspace, file_path)
    except ValueError as error:
        return {"error": str(error)}

    if path.suffix != ".ipynb":
        return {"error": "file_path must point to a .ipynb file."}

    if not path.exists():
        return {"error": f"notebook does not exist: {path}"}

    try:
        before, notebook = load_notebook(path)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        return {"error": str(error)}

    previous_hash = state.get_file_hash(path)

    if previous_hash is None:
        return {
            "error": "The notebook has not been read yet. Read it before editing.",
            "code": "file_not_read",
        }

    if previous_hash != get_content_hash(before):
        return {
            "error": (
                "The notebook changed after it was read. Read it again before "
                "editing."
            ),
            "code": "stale_read",
        }

    cells = notebook.setdefault("cells", [])

    if cell_index > len(cells):
        return {
            "error": f"cell_index {cell_index} is outside the notebook.",
            "code": "cell_not_found",
        }

    try:
        cell = make_cell(cell_type, source)
    except ValueError as error:
        return {"error": str(error)}

    cells.insert(cell_index, cell)
    after = dump_notebook(notebook)
    diff_lines = create_diff_lines(before, after)

    return {
        "success": True,
        "created": False,
        "file_path": str(path),
        "path": path,
        "before_content": before,
        "updated_content": after,
        "cell_index": cell_index,
        "cell_type": cell_type,
        "diff": create_diff(path, before, after),
        "diff_lines": diff_lines,
        "additions": sum(row["type"] == "add" for row in diff_lines),
        "removals": sum(row["type"] == "remove" for row in diff_lines),
    }


def preview_insert_notebook_cell(
    file_path,
    cell_index,
    cell_type,
    source,
    state,
):
    prepared = prepare_insert_notebook_cell(
        file_path,
        cell_index,
        cell_type,
        source,
        state,
    )

    if not prepared.get("success"):
        return prepared

    return {
        "success": True,
        "file_path": prepared["file_path"],
        "cell_index": prepared["cell_index"],
        "cell_type": prepared["cell_type"],
        "diff": prepared["diff"],
        "diff_lines": prepared["diff_lines"],
        "additions": prepared["additions"],
        "removals": prepared["removals"],
    }


def insert_notebook_cell(file_path, cell_index, cell_type, source, state):
    prepared = prepare_insert_notebook_cell(
        file_path,
        cell_index,
        cell_type,
        source,
        state,
    )

    if not prepared.get("success"):
        return prepared

    path = prepared["path"]

    try:
        write_file_atomically(path, prepared["updated_content"])
    except OSError as error:
        return {"error": str(error)}

    checkpoint = create_checkpoint(
        state,
        "insert_notebook_cell",
        path,
        prepared["before_content"],
        prepared["updated_content"],
        False,
    )
    state.remember_file(path, get_content_hash(prepared["updated_content"]))

    return {
        "success": True,
        "file_path": str(path),
        "checkpoint_id": checkpoint["id"],
        "cell_index": prepared["cell_index"],
        "cell_type": prepared["cell_type"],
        "diff": prepared["diff"],
        "diff_lines": prepared["diff_lines"],
        "additions": prepared["additions"],
        "removals": prepared["removals"],
        "summary": f"Inserted {prepared['cell_type']} cell at {prepared['cell_index']}.",
    }


def prepare_delete_notebook_cell(file_path, cell_index, state):
    if not isinstance(cell_index, int) or cell_index < 0:
        return {"error": "cell_index must be a non-negative integer."}

    try:
        path = resolve_workspace_path(state.workspace, file_path)
    except ValueError as error:
        return {"error": str(error)}

    if path.suffix != ".ipynb":
        return {"error": "file_path must point to a .ipynb file."}

    if not path.exists():
        return {"error": f"notebook does not exist: {path}"}

    try:
        before, notebook = load_notebook(path)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        return {"error": str(error)}

    previous_hash = state.get_file_hash(path)

    if previous_hash is None:
        return {
            "error": "The notebook has not been read yet. Read it before editing.",
            "code": "file_not_read",
        }

    if previous_hash != get_content_hash(before):
        return {
            "error": (
                "The notebook changed after it was read. Read it again before "
                "editing."
            ),
            "code": "stale_read",
        }

    cells = notebook.get("cells", [])

    if cell_index >= len(cells):
        return {
            "error": f"cell_index {cell_index} is outside the notebook.",
            "code": "cell_not_found",
        }

    deleted_cell = cells.pop(cell_index)
    after = dump_notebook(notebook)
    diff_lines = create_diff_lines(before, after)

    return {
        "success": True,
        "created": False,
        "file_path": str(path),
        "path": path,
        "before_content": before,
        "updated_content": after,
        "cell_index": cell_index,
        "cell_type": deleted_cell.get("cell_type", "unknown"),
        "diff": create_diff(path, before, after),
        "diff_lines": diff_lines,
        "additions": sum(row["type"] == "add" for row in diff_lines),
        "removals": sum(row["type"] == "remove" for row in diff_lines),
    }


def preview_delete_notebook_cell(file_path, cell_index, state):
    prepared = prepare_delete_notebook_cell(file_path, cell_index, state)

    if not prepared.get("success"):
        return prepared

    return {
        "success": True,
        "file_path": prepared["file_path"],
        "cell_index": prepared["cell_index"],
        "cell_type": prepared["cell_type"],
        "diff": prepared["diff"],
        "diff_lines": prepared["diff_lines"],
        "additions": prepared["additions"],
        "removals": prepared["removals"],
    }


def delete_notebook_cell(file_path, cell_index, state):
    prepared = prepare_delete_notebook_cell(file_path, cell_index, state)

    if not prepared.get("success"):
        return prepared

    path = prepared["path"]

    try:
        write_file_atomically(path, prepared["updated_content"])
    except OSError as error:
        return {"error": str(error)}

    checkpoint = create_checkpoint(
        state,
        "delete_notebook_cell",
        path,
        prepared["before_content"],
        prepared["updated_content"],
        False,
    )
    state.remember_file(path, get_content_hash(prepared["updated_content"]))

    return {
        "success": True,
        "file_path": str(path),
        "checkpoint_id": checkpoint["id"],
        "cell_index": prepared["cell_index"],
        "cell_type": prepared["cell_type"],
        "diff": prepared["diff"],
        "diff_lines": prepared["diff_lines"],
        "additions": prepared["additions"],
        "removals": prepared["removals"],
        "summary": f"Deleted {prepared['cell_type']} cell at {prepared['cell_index']}.",
    }
