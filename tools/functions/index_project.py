from core.project_index import (
    build_index,
    changed_files,
    ensure_fresh_index,
    get_index,
    search_project_index,
    search_symbols_in_index,
)
from core.workspace import resolve_workspace_path


def resolve_root(state, workspace="."):
    base = state.workspace if state is not None else "."
    return resolve_workspace_path(base, workspace)


def index_project(force: bool = False, workspace: str = ".", state=None) -> dict:
    """Build or refresh the workspace index."""
    try:
        root = resolve_root(state, workspace)
        data = build_index(root, force=force)
        summary = data.get("summary", {})
        stats = data.get("stats", {})

        return {
            "success": True,
            "root": str(root),
            "index_path": str(root / ".rectury/index.json"),
            "force": force,
            "index_status": "rebuilt" if force else "refreshed",
            "files_indexed": summary.get("files", 0),
            "languages": summary.get("languages", {}),
            "symbols": summary.get("symbols", 0),
            "imports": summary.get("imports", 0),
            "important_files": summary.get("important_files", [])[:15],
            "stats": stats,
            "removed": data.get("removed", [])[:30],
        }
    except Exception as error:
        return {"error": str(error)}


def search_symbols(
    query: str,
    workspace: str = ".",
    limit: int = 50,
    state=None,
) -> dict:
    """Search indexed symbols without reading full files."""
    if not isinstance(query, str) or not query.strip():
        return {"error": "query must be a non-empty string."}

    try:
        root = resolve_root(state, workspace)
        data, index_status = ensure_fresh_index(root)
        matches = search_symbols_in_index(data, query, limit=limit)

        return {
            "success": True,
            "query": query,
            "root": str(root),
            **index_status,
            "matches": matches,
            "total": len(matches),
        }
    except Exception as error:
        return {"error": str(error)}


def search_project(
    query: str,
    workspace: str = ".",
    limit: int = 20,
    include_content: bool = True,
    state=None,
) -> dict:
    """Search project index across files, symbols, imports, and light content."""
    if not isinstance(query, str) or not query.strip():
        return {"error": "query must be a non-empty string."}

    try:
        root = resolve_root(state, workspace)
        data, index_status = ensure_fresh_index(root)
        results = search_project_index(
            root,
            data,
            query,
            limit=limit,
            include_content=include_content,
        )

        return {
            "success": True,
            "query": query,
            "root": str(root),
            **index_status,
            "results": results,
            "total": len(results),
            "include_content": include_content,
        }
    except Exception as error:
        return {"error": str(error)}


def index_changed_files(workspace: str = ".", state=None) -> dict:
    """Show files that changed since the last project index build."""
    try:
        root = resolve_root(state, workspace)
        freshness = changed_files(root)

        if freshness.get("changed") or freshness.get("missing"):
            build_index(root, force=False)
            freshness["index_status"] = "refreshed"
        else:
            freshness["index_status"] = "reused"

        return freshness
    except Exception as error:
        return {"error": str(error)}


def project_overview(workspace: str = ".", state=None) -> dict:
    """Return a compact project overview from the existing index."""
    try:
        root = resolve_root(state, workspace)
        data, index_status = ensure_fresh_index(root)
        summary = data.get("summary", {})

        return {
            "success": True,
            "root": str(root),
            **index_status,
            "generated_at": data.get("generated_at", ""),
            "files_indexed": summary.get("files", 0),
            "languages": summary.get("languages", {}),
            "symbols": summary.get("symbols", 0),
            "imports": summary.get("imports", 0),
            "important_files": summary.get("important_files", [])[:20],
        }
    except Exception as error:
        return {"error": str(error)}
