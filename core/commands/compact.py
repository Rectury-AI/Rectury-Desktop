from core.cost_tracker import add_to_total_cost
from time import monotonic


COMPACT_PROMPT = """Provide a detailed but concise summary of our conversation above. Focus on information that would be helpful for continuing the conversation, including what we did, what we're doing, which files we're working on, and what we're going to do next."""


def generate_compact_summary(client, model: str, messages: list) -> str:
    """Generate a compact summary of the conversation."""
    if not client:
        return None

    # Build messages for summary request
    summary_messages = [
        {
            "role": "system",
            "content": "You are a helpful AI assistant tasked with summarizing conversations.",
        }
    ]

    # Add all messages + summary request
    for msg in messages:
        summary_messages.append(msg)

    summary_messages.append({
        "role": "user",
        "content": COMPACT_PROMPT,
    })

    try:
        start_time = monotonic()
        response = client.chat.completions.create(
            model=model,
            messages=summary_messages,
        )
        duration = monotonic() - start_time

        # Track the API call
        add_to_total_cost(0.0, duration)

        summary = response.choices[0].message.content or ""
        return summary.strip()
    except Exception as e:
        return None


def handle_compact_command(client=None, model: str = "", messages: list = None) -> dict:
    """
    Handle /compact command:
    1. Generate summary of conversation
    2. Clear messages
    3. Return summary to be used as new context
    """
    if not messages or len(messages) == 0:
        return {
            "success": False,
            "message": "No conversation to compact.",
        }

    if not client or not model:
        return {
            "success": False,
            "message": "Cannot compact: model not configured.",
        }

    # Generate summary
    summary = generate_compact_summary(client, model, messages)

    if not summary:
        return {
            "success": False,
            "message": "Failed to generate conversation summary.",
        }

    # Return the summary and cleared state
    return {
        "success": True,
        "summary": summary,
        "message": "Conversation compacted. Summary preserved in context.",
        "cleared_messages": [
            {
                "role": "user",
                "content": "Use the /compact command to clear the conversation history, and start a new conversation with the summary in context.",
            },
            {
                "role": "assistant",
                "content": summary,
            },
        ],
    }
