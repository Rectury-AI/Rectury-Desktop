import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


MODEL_ENV_PATH = Path(".env")


@dataclass(frozen=True)
class ClientConfig:
    provider: str
    model: str
    base_url: str | None


def model_env_version():
    try:
        stat = MODEL_ENV_PATH.stat()
    except FileNotFoundError:
        return None

    return stat.st_mtime_ns, stat.st_size


def create_client() -> tuple[OpenAI, ClientConfig]:
    load_dotenv(override=True)

    provider = os.getenv("AI_PROVIDER", "").strip().lower()
    model = os.getenv("AI_MODEL", "").strip()
    api_key = os.getenv("AI_API_KEY", "").strip()
    base_url = os.getenv("AI_BASE_URL", "").strip()

    if provider == "xai":
        api_key = api_key or os.getenv("XAI_API_KEY", "").strip()
        base_url = base_url or "https://api.x.ai/v1"

    if not provider:
        raise ValueError("AI_PROVIDER environment variable is not set.")
    if not api_key:
        raise ValueError("AI_API_KEY environment variable is not set.")
    if not model:
        raise ValueError("AI_MODEL environment variable is not set.")
    if not base_url:
        raise ValueError("AI_BASE_URL environment variable is not set.")

    return OpenAI(api_key=api_key, base_url=base_url), ClientConfig(
        provider=provider,
        model=model,
        base_url=base_url,
    )
