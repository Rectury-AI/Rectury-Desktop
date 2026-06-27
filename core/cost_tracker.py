import time
from datetime import timedelta


class CostTracker:
    """
    Track API costs and durations for the current session
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.total_cost = 0.0
        self.total_api_duration = 0.0  # in seconds
        self.start_time = time.time()
        self._initialized = True

    def add_to_total_cost(self, cost: float, duration: float):
        """Add cost and API duration to totals"""
        self.total_cost += cost
        self.total_api_duration += duration

    def get_total_cost(self) -> float:
        return self.total_cost

    def get_total_duration(self) -> float:
        """Wall clock duration in seconds"""
        return time.time() - self.start_time

    def get_total_api_duration(self) -> float:
        return self.total_api_duration

    def format_duration(self, seconds: float) -> str:
        """Format a duration for terminal display."""
        td = timedelta(seconds=int(seconds))
        hours, remainder = divmod(td.seconds, 3600)
        minutes, secs = divmod(remainder, 60)

        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"

    def format_cost(self, cost: float) -> str:
        """Format cost with appropriate precision"""
        if cost > 0.5:
            return f"${round(cost, 2):.2f}"
        else:
            return f"${cost:.4f}"

    def format_total_cost(self) -> str:
        """Format a total cost summary."""
        return (
            f"Total cost: {self.format_cost(self.total_cost)}\n"
            f"Total duration (API): {self.format_duration(self.total_api_duration)}\n"
            f"Total duration (wall): {self.format_duration(self.get_total_duration())}"
        )

    def reset(self):
        """Reset all tracking (for new session)"""
        self.total_cost = 0.0
        self.total_api_duration = 0.0
        self.start_time = time.time()


# Singleton instance
cost_tracker = CostTracker()


def add_to_total_cost(cost: float, duration: float):
    cost_tracker.add_to_total_cost(cost, duration)


def get_total_cost() -> float:
    return cost_tracker.get_total_cost()


def format_total_cost() -> str:
    return cost_tracker.format_total_cost()
