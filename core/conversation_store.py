import json
from pathlib import Path

RECTURY_HOME = Path.home() / ".rectury"
CONVERSATION_DIR = RECTURY_HOME / "conversations"


def save_conversation(conversation):
    CONVERSATION_DIR.mkdir(parents=True, exist_ok=True)
    file_path = CONVERSATION_DIR / f"{conversation['id']}.json"

    with file_path.open("w", encoding="utf-8") as file:
        json.dump(
            conversation,
            file,
            indent=2,
            ensure_ascii=False,
        )

    return file_path


def load_latest_conversation():
    if not CONVERSATION_DIR.exists():
        return None

    conversation_files = sorted(
        CONVERSATION_DIR.glob("*.json"),
        key=lambda file_path: file_path.stat().st_mtime,
        reverse=True,
    )

    for file_path in conversation_files:
        try:
            with file_path.open("r", encoding="utf-8") as file:
                return json.load(file)
        except (OSError, json.JSONDecodeError):
            continue

    return None
