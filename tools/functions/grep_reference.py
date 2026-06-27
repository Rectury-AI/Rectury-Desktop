import re

from core.references import resolve_reference_path


def grep_reference(pattern, state, reference=None, path=".", glob="**/*",
                   ignore_case=True, max_results=100, context=0,
                   whole_word=False, multiline=False):
    """Search for a regex pattern inside a configured read-only reference path."""
    if not isinstance(pattern, str) or not pattern:
        return {"error": "pattern must be a non-empty string."}

    flags = 0

    if ignore_case:
        flags |= re.IGNORECASE

    if multiline:
        flags |= re.DOTALL

    if whole_word:
        pattern = rf"\b(?:{pattern})\b"

    try:
        regex = re.compile(pattern, flags)
    except re.error as error:
        return {"error": f"invalid regex: {error}"}

    try:
        root, search_root = resolve_reference_path(state, reference, path)
    except Exception as error:
        return {"error": str(error)}

    if not search_root.exists():
        return {"error": f"path does not exist: {search_root}"}

    matches = []

    try:
        for file in search_root.glob(glob):
            if not file.is_file():
                continue

            try:
                text = file.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            lines = text.splitlines()

            for index, line in enumerate(lines, 1):
                if not regex.search(line):
                    continue

                entry = {
                    "file": str(file.relative_to(root)),
                    "line": index,
                    "text": line.strip(),
                }

                if context > 0:
                    start = max(0, index - 1 - context)
                    end = min(len(lines), index + context)
                    entry["context"] = [
                        {"line": line_index + 1, "text": lines[line_index].strip()}
                        for line_index in range(start, end)
                    ]

                matches.append(entry)

                if len(matches) >= max_results:
                    return {
                        "success": True,
                        "reference": str(root),
                        "matches": matches,
                        "truncated": True,
                    }
    except Exception as error:
        return {"error": str(error)}

    return {
        "success": True,
        "reference": str(root),
        "matches": matches,
        "truncated": False,
    }
