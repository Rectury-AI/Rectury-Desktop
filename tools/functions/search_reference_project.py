"""search_reference_project tool – ranked search inside a reference index."""

from core.references import resolve_reference_root
from core.project_index import search_reference_project as _search_reference_project


def search_reference_project(
    query: str,
    reference: str | None = None,
    limit: int = 20,
    include_content: bool = True,
    state=None,
) -> dict:
    try:
        root = resolve_reference_root(state, reference)
        return _search_reference_project(
            query,
            root,
            limit=limit,
            include_content=include_content,
        )
    except Exception as error:
        return {"error": str(error)}
