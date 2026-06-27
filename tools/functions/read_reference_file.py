from tools.functions.read_file import (
    DEFAULT_LINE_LIMIT,
    MAX_LINE_LENGTH,
    MAX_LINE_LIMIT,
    find_similar_file,
    read_text_file,
)
from core.references import resolve_reference_path


def read_reference_file(file_path, state, reference=None, offset=1, limit=DEFAULT_LINE_LIMIT):
    """Read a UTF-8 file from a configured read-only reference path."""
    if not isinstance(offset, int) or offset < 1:
        return {"error": "offset must be a positive integer."}

    if not isinstance(limit, int) or limit < 1:
        return {"error": "limit must be a positive integer."}

    limit = min(limit, MAX_LINE_LIMIT)

    try:
        root, path = resolve_reference_path(state, reference, file_path)
    except ValueError as error:
        return {"error": str(error)}

    if not path.exists():
        message = f"file does not exist: {path}"
        similar_file = find_similar_file(path)

        if similar_file:
            message += f". Did you mean {similar_file}?"

        return {
            "error": message,
            "code": "file_not_found",
            "similar_file": similar_file,
        }

    if not path.is_file():
        return {"error": f"path is not a file: {path}"}

    try:
        content = read_text_file(path)
    except (OSError, UnicodeError) as error:
        return {"error": str(error)}

    lines = content.splitlines()
    start = offset - 1
    selected_lines = lines[start : start + limit]
    numbered_lines = [
        f"{line_number:>6} | "
        f"{line[:MAX_LINE_LENGTH]}"
        f"{' ... [line truncated]' if len(line) > MAX_LINE_LENGTH else ''}"
        for line_number, line in enumerate(selected_lines, start=offset)
    ]

    return {
        "success": True,
        "reference": str(root),
        "file_path": str(path),
        "relative_file_path": str(path.relative_to(root)),
        "bytes": len(content.encode("utf-8")),
        "content": "\n".join(numbered_lines),
        "offset": offset,
        "returned_lines": len(selected_lines),
        "total_lines": len(lines),
        "truncated": start + len(selected_lines) < len(lines),
    }
