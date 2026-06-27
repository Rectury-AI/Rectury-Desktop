from core.references import remove_reference_path


def reference_remove(reference, state):
    """Remove a configured read-only reference path by index or path."""
    try:
        return remove_reference_path(state, reference)
    except Exception as error:
        return {"error": str(error)}
