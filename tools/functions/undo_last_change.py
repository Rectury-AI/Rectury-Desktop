from core.checkpoints import undo_last_change as undo_checkpoint


def undo_last_change(state):
    """Undo the latest checkpointed file change."""
    return undo_checkpoint(state)
