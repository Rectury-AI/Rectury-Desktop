from pathlib import Path


def resolve_workspace_path(workspace, requested_path):
    workspace_path = Path(workspace).expanduser().resolve()
    path = Path(requested_path).expanduser()

    if not path.is_absolute():
        path = workspace_path / path

    resolved_path = path.resolve()

    if (
        resolved_path != workspace_path
        and workspace_path not in resolved_path.parents
    ):
        raise ValueError("Path is outside the active workspace.")

    return resolved_path
