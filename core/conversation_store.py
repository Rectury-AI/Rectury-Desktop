from pathlib import Path

RECTURY_HOME = Path.home() / ".rectury"
CONVERSATION_DIR = RECTURY_HOME / "conversations"

CONVERSATION_DIR.mkdir(parents=True, exist_ok=True)