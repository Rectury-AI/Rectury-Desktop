from hashlib import sha256

from core.workspace import resolve_workspace_path


DEFAULT_LINE_LIMIT = 2000
MAX_LINE_LIMIT = 2000
MAX_LINE_LENGTH = 2000
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}


def find_similar_file(path):
    parent = path.parent

    if not parent.exists():
        return None

    stem = path.stem.lower()

    try:
        for candidate in parent.iterdir():
            if candidate.is_file() and candidate.stem.lower() == stem:
                return str(candidate)
    except OSError:
        return None

    return None


def get_content_hash(content):
    return sha256(content.encode("utf-8")).hexdigest()


def read_text_file(path):
    with path.open("r", encoding="utf-8", newline="") as file:
        return file.read()


def read_file(file_path, state, offset=1, limit=DEFAULT_LINE_LIMIT):
    if offset is None:
        offset = 1

    if limit is None:
        limit = DEFAULT_LINE_LIMIT

    if not isinstance(offset, int) or offset < 0:
        return {"error": "offset must be a non-negative integer."}

    if not isinstance(limit, int) or limit < 1:
        return {"error": "limit must be a positive integer."}

    limit = min(limit, MAX_LINE_LIMIT)

    try:
        path = resolve_workspace_path(state.workspace, file_path)
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

    if path.suffix.lower() in IMAGE_EXTENSIONS:
        from tools.functions.read_image import read_image

        result = read_image(file_path, state, include_data=True)
        if result.get("success"):
            result["type"] = "image"
        return result

    try:
        content = read_text_file(path)
    except (OSError, UnicodeError) as error:
        return {"error": str(error)}

    lines = content.splitlines()
    start = 0 if offset == 0 else offset - 1
    selected_lines = lines[start : start + limit]
    display_start = 0 if offset == 0 else offset
    numbered_lines = [
        f"{line_number:>6} | "
        f"{line[:MAX_LINE_LENGTH]}"
        f"{' ... [line truncated]' if len(line) > MAX_LINE_LENGTH else ''}"
        for line_number, line in enumerate(selected_lines, start=display_start)
    ]

    state.remember_file(path, get_content_hash(content))

    return {
        "success": True,
        "file_path": str(path),
        "bytes": len(content.encode("utf-8")),
        "content": "\n".join(numbered_lines),
        "offset": offset,
        "returned_lines": len(selected_lines),
        "total_lines": len(lines),
        "truncated": start + len(selected_lines) < len(lines),
    }
