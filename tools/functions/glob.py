from core.context import IGNORED_DIRS
from core.workspace import resolve_workspace_path


DEFAULT_MAX_RESULTS = 100
MAX_RESULTS = 500


def is_ignored(path):
    return any(part in IGNORED_DIRS for part in path.parts)


def glob(pattern, state, path=".", max_results=DEFAULT_MAX_RESULTS):
    if not isinstance(pattern, str) or not pattern.strip():
        return {"error": "pattern must be a non-empty string."}

    try:
        limit = max(1, min(int(max_results), MAX_RESULTS))
    except (TypeError, ValueError):
        limit = DEFAULT_MAX_RESULTS

    try:
        root = resolve_workspace_path(state.workspace, path)
    except ValueError as error:
        return {"error": str(error)}

    if not root.exists():
        return {"error": f"path does not exist: {root}"}

    if not root.is_dir():
        return {"error": f"path is not a directory: {root}"}

    matches = []

    try:
        for candidate in root.glob(pattern):
            if len(matches) >= limit:
                break

            if not candidate.is_file():
                continue

            try:
                relative_to_root = candidate.relative_to(root)
                relative_to_workspace = candidate.relative_to(state.workspace)
            except ValueError:
                continue

            if is_ignored(relative_to_workspace):
                continue

            matches.append(
                {
                    "file": str(relative_to_workspace),
                    "mtime": candidate.stat().st_mtime,
                }
            )
    except ValueError as error:
        return {"error": f"invalid glob pattern: {error}"}
    except OSError as error:
        return {"error": str(error)}

    matches = sorted(matches, key=lambda item: (-item["mtime"], item["file"]))
    files = [item["file"] for item in matches[:limit]]
    truncated = len(matches) > len(files)

    return {
        "success": True,
        "pattern": pattern,
        "path": str(root),
        "relative_path": str(root.relative_to(state.workspace)),
        "files": files,
        "total": len(matches),
        "truncated": truncated,
    }
