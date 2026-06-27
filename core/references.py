from pathlib import Path


def normalize_reference_path(path):
    if not isinstance(path, str) or not path.strip():
        raise ValueError("path must be a non-empty string.")

    resolved = Path(path).expanduser().resolve()

    if not resolved.exists():
        raise ValueError(f"reference path does not exist: {resolved}")

    if not resolved.is_dir():
        raise ValueError(f"reference path must be a directory: {resolved}")

    return resolved


def reference_entries(state):
    return [
        {
            "index": index,
            "path": path,
        }
        for index, path in enumerate(state.get_reference_paths(), 1)
    ]


def add_reference_path(state, path):
    resolved = normalize_reference_path(path)
    state.add_reference_path(str(resolved))
    return {
        "success": True,
        "path": str(resolved),
        "references": reference_entries(state),
    }


def resolve_reference_root(state, reference=None):
    references = state.get_reference_paths()

    if not references:
        raise ValueError(
            "No reference paths are configured. Add one with reference_add "
            "or /reference add <path>."
        )

    if reference in {None, ""}:
        if len(references) == 1:
            return Path(references[0]).resolve()

        raise ValueError(
            "Multiple reference paths are configured. Provide a reference "
            "index or absolute reference path."
        )

    if isinstance(reference, int) or (
        isinstance(reference, str) and reference.strip().isdigit()
    ):
        index = int(reference)

        if index < 1 or index > len(references):
            raise ValueError(f"reference index out of range: {index}")

        return Path(references[index - 1]).resolve()

    requested = Path(str(reference)).expanduser().resolve()

    for path in references:
        configured = Path(path).resolve()

        if requested == configured:
            return configured

    raise ValueError(f"reference path is not configured: {requested}")


def remove_reference_path(state, reference):
    root = resolve_reference_root(state, reference)
    removed = state.remove_reference_path(str(root))

    if removed is None:
        raise ValueError(f"reference path is not configured: {root}")

    return {
        "success": True,
        "removed": removed,
        "references": reference_entries(state),
    }


def resolve_reference_path(state, reference, requested_path="."):
    root = resolve_reference_root(state, reference)
    relative = Path(requested_path or ".").expanduser()

    if relative.is_absolute():
        resolved = relative.resolve()
    else:
        resolved = (root / relative).resolve()

    if resolved != root and root not in resolved.parents:
        raise ValueError("Path is outside the selected reference path.")

    return root, resolved
