from core.cost_tracker import format_total_cost


def handle_cost_command() -> str:
    """
    Handle /cost command
    Shows total cost and duration of current session
    """
    return format_total_cost()