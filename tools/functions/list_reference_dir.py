import os

from core.references import resolve_reference_path


def list_reference_dir(state, reference=None, directory="."):
    """List a directory inside a configured read-only reference path."""
    try:
        root, path = resolve_reference_path(state, reference, directory)

        if not path.exists():
            return {"error": f"path does not exist: {path}"}

        if not path.is_dir():
            return {"error": f"path is not a directory: {path}"}

        files = sorted(os.listdir(path))

        return {
            "success": True,
            "reference": str(root),
            "directory": str(path),
            "relative_directory": str(path.relative_to(root)),
            "files": files,
        }
    except Exception as error:
        return {"error": str(error)}
