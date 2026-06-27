import os


LOW_THINKING_TOKENS = 4_000
MEDIUM_THINKING_TOKENS = 10_000
HIGH_THINKING_TOKENS = 32_000 - 1

HIGH_THINKING_PHRASES = (
    "think harder",
    "think intensely",
    "think longer",
    "think really hard",
    "think super hard",
    "think very hard",
    "ultrathink",
)

MEDIUM_THINKING_PHRASES = (
    "think about it",
    "think a lot",
    "think hard",
    "think more",
    "megathink",
)

THINKING_ERROR_MARKERS = (
    "reasoning_effort",
    "reasoning",
    "max_tokens",
    "extra_body",
    "unsupported parameter",
    "unexpected keyword",
    "unknown parameter",
    "unrecognized request argument",
    "extra_forbidden",
)


def _positive_int(value):
    try:
        parsed = int(str(value).strip())
    except (TypeError, ValueError):
        return None

    return parsed if parsed > 0 else None


def configured_max_thinking_tokens():
    for env_name in ("RECTURY_MAX_THINKING_TOKENS", "MAX_THINKING_TOKENS"):
        parsed = _positive_int(os.getenv(env_name))

        if parsed is not None:
            return parsed

    return None


def content_text(content):
    if isinstance(content, str):
        return content

    if isinstance(content, dict):
        return str(content.get("text") or "")

    if isinstance(content, list):
        parts = []

        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                parts.append(str(item.get("text") or ""))

        return "\n".join(part for part in parts if part)

    return ""


def last_user_text(messages):
    for message in reversed(messages or []):
        if message.get("role") == "user":
            return content_text(message.get("content", ""))

    return ""


def get_max_thinking_tokens(messages, think_tool_enabled=False):
    configured_tokens = configured_max_thinking_tokens()

    if configured_tokens is not None:
        return configured_tokens

    if think_tool_enabled:
        return 0

    content = last_user_text(messages).lower()

    if any(phrase in content for phrase in HIGH_THINKING_PHRASES):
        return HIGH_THINKING_TOKENS

    if any(phrase in content for phrase in MEDIUM_THINKING_PHRASES):
        return MEDIUM_THINKING_TOKENS

    if "think" in content:
        return LOW_THINKING_TOKENS

    return 0


def reasoning_effort_for_tokens(token_count):
    if token_count >= HIGH_THINKING_TOKENS:
        return "high"

    if token_count >= MEDIUM_THINKING_TOKENS:
        return "medium"

    if token_count > 0:
        return "low"

    return None


def thinking_request_kwargs(provider, model, token_count):
    if token_count <= 0:
        return {}

    provider = str(provider or "").lower()
    model = str(model or "").lower()

    if provider == "openrouter":
        return {
            "extra_body": {
                "reasoning": {
                    "max_tokens": token_count,
                },
            },
        }

    effort = reasoning_effort_for_tokens(token_count)

    if not effort:
        return {}

    if provider in {"openai", "xai", "custom"} or model:
        return {"reasoning_effort": effort}

    return {}


def is_thinking_parameter_error(error):
    error_text = str(error).lower()
    return any(marker in error_text for marker in THINKING_ERROR_MARKERS)
