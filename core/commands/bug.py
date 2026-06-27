import json
from pathlib import Path
from datetime import datetime
import platform


BUG_REPORTS_PATH = Path.home() / ".rectury" / "bug_reports.json"


def get_system_info():
    return {
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "system": platform.system(),
        "release": platform.release(),
    }


def collect_bug_report(description: str, messages: list = None, workspace: str = ".") -> dict:
    """Collect local bug report data."""
    report = {
        "datetime": datetime.now().isoformat(),
        "description": description,
        "workspace": str(Path(workspace).resolve()),
        "system_info": get_system_info(),
        "message_count": len(messages) if messages else 0,
        "transcript": messages or [],
    }
    return report


def save_bug_report(report: dict) -> str:
    """
    Save bug report to local JSON file
    Returns the report ID
    """
    BUG_REPORTS_PATH.parent.mkdir(parents=True, exist_ok=True)

    reports = []
    if BUG_REPORTS_PATH.exists():
        try:
            with BUG_REPORTS_PATH.open("r", encoding="utf-8") as f:
                reports = json.load(f)
        except (json.JSONDecodeError, OSError):
            reports = []

    report_id = f"bug_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    report["id"] = report_id
    reports.append(report)

    with BUG_REPORTS_PATH.open("w", encoding="utf-8") as f:
        json.dump(reports, f, indent=2, ensure_ascii=False)

    return report_id


def handle_bug_command(description: str = "", messages: list = None, workspace: str = ".") -> str:
    """
    Handle /bug command
    Collects feedback and saves it locally
    """
    if not description or description.strip() == "":
        return """Bug Report

Please provide a description of the issue or feedback.

Usage: /bug <your description>

Example: /bug The tool is not recognizing my Python files correctly"""

    report = collect_bug_report(description, messages, workspace)
    report_id = save_bug_report(report)

    return f"""Bug report saved.

Report ID: {report_id}
Description: {description[:100]}{'...' if len(description) > 100 else ''}

Your feedback has been saved to: {BUG_REPORTS_PATH}

Thank you for helping improve Rectury."""
