from core.references import reference_entries


def reference_list(state):
    """List read-only external reference paths for this conversation."""
    references = reference_entries(state)

    return {
        "success": True,
        "total": len(references),
        "references": references,
    }
