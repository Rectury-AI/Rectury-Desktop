import re

from core.workspace import resolve_workspace_path


def grep(pattern, state, path=".", glob="**/*", ignore_case=True,
         max_results=100, context=0, whole_word=False, multiline=False,
         files_only=False):
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
    except re.error as e:
        return {"error": f"invalid regex: {e}"}

    try:
        root = resolve_workspace_path(state.workspace, path)
    except Exception as e:
        return {"error": str(e)}

    if not root.exists():
        return {"error": f"path does not exist: {root}"}

    matches = []
    matching_files = []
    try:
        for file in root.glob(glob):
            if not file.is_file():
                continue
            try:
                text = file.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            lines = text.splitlines()
            for i, line in enumerate(lines, 1):
                if regex.search(line):
                    if files_only:
                        try:
                            relative_file = str(file.relative_to(state.workspace))
                        except ValueError:
                            relative_file = str(file.relative_to(root))

                        matching_files.append(
                            {
                                "file": relative_file,
                                "mtime": file.stat().st_mtime,
                            }
                        )
                        break

                    entry = {
                        "file": str(file.relative_to(root)),
                        "line": i,
                        "text": line.strip()
                    }
                    if context > 0:
                        start = max(0, i - 1 - context)
                        end = min(len(lines), i + context)
                        entry["context"] = [
                            {"line": j + 1, "text": lines[j].strip()}
                            for j in range(start, end)
                        ]
                    matches.append(entry)
                    if len(matches) >= max_results:
                        return {
                            "success": True,
                            "matches": matches,
                            "truncated": True
                        }
    except Exception as e:
        return {"error": str(e)}

    if files_only:
        matching_files = sorted(
            matching_files,
            key=lambda item: (-item["mtime"], item["file"]),
        )
        files = [item["file"] for item in matching_files[:max_results]]
        return {
            "success": True,
            "files": files,
            "total": len(matching_files),
            "truncated": len(matching_files) > len(files),
        }

    return {
        "success": True,
        "matches": matches,
        "truncated": False
    }
