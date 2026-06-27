"""index_reference tool – build/refresh reference index (read-only cache)."""

from core.references import resolve_reference_root
from core.project_index import index_reference as _index_reference


def index_reference(reference: str | None = None, force: bool = False, state=None) -> dict:
    try:
        root = resolve_reference_root(state, reference)
        return _index_reference(root, force=force)
    except Exception as error:
        return {"error": str(error)}
