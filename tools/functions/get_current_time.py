from datetime import datetime

def get_current_time(state):
    """Return the current local date and time in ISO format."""
    return {"time": datetime.now().astimezone().isoformat()}
