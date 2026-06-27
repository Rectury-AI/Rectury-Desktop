import sys
import os
import subprocess


def is_listen_enabled() -> bool:
    """Check if listen command should be enabled."""
    if sys.platform != "darwin":
        return False

    term_program = os.getenv("TERM_PROGRAM", "")
    return term_program in ["iTerm.app", "Apple_Terminal"]


def handle_listen_command() -> str:
    """
    Handle /listen command
    Activates macOS speech recognition (dictation)
    """
    if not is_listen_enabled():
        return "Listen command is only available on macOS with iTerm.app or Apple Terminal."

    # AppleScript to trigger Start Dictation from menu bar
    script = '''tell application "System Events" to tell ¬
(the first process whose frontmost is true) to tell ¬
menu bar 1 to tell ¬
menu bar item "Edit" to tell ¬
menu "Edit" to tell ¬
menu item "Start Dictation" to ¬
if exists then click it'''

    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            return f"Failed to start dictation: {result.stderr.strip()}"

        return "Dictation started. Press esc to stop."

    except subprocess.TimeoutExpired:
        return "Failed to start dictation: timeout"
    except Exception as e:
        return f"Failed to start dictation: {str(e)}"
