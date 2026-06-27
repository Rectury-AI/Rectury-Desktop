from core.references import add_reference_path


def reference_add(path, state):
    """Add a read-only external directory as a reference path."""
    try:
        return add_reference_path(state, path)
    except Exception as error:
        return {"error": str(error)}
