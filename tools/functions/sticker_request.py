def sticker_request(trigger, state):
    if not isinstance(trigger, str) or not trigger.strip():
        return {"error": "trigger must be a non-empty string."}

    return {
        "success": True,
        "available": False,
        "trigger": trigger.strip(),
        "message": (
            "Sticker request forms are not available in this runtime. Explain "
            "to the user that shipping details cannot be collected and "
            "stickers cannot be sent from here."
        ),
    }
