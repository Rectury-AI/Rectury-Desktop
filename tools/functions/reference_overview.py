"""reference_overview tool – compact index summary for a reference path."""

from core.references import resolve_reference_root
from core.project_index import reference_overview as _reference_overview


def reference_overview(reference: str | None = None, state=None) -> dict:
    try:
        root = resolve_reference_root(state, reference)
        return _reference_overview(root)
    except Exception as error:
        return {"error": str(error)}
