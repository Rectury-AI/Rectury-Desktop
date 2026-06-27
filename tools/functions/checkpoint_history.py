from core.checkpoints import checkpoint_history as get_checkpoint_history


def checkpoint_history(state, limit=20):
    """Return recent file-edit checkpoints for this conversation."""
    return get_checkpoint_history(state, limit=limit)
