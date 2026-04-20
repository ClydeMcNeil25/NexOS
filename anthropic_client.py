from __future__ import annotations

import os
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parent
ENV_FILE = ROOT_DIR / ".env"

DEFAULT_MODEL = "claude-sonnet-4-6"


def load_environment() -> str:
    load_dotenv(ENV_FILE, override=True)

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            f"ANTHROPIC_API_KEY not found. Expected it in: {ENV_FILE}"
        )

    return api_key


def get_client() -> Anthropic:
    api_key = load_environment()
    return Anthropic(api_key=api_key)


def call_claude(
    *,
    system_prompt: str,
    user_prompt: str,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 1800,
) -> str:
    client = get_client()

    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[
            {
                "role": "user",
                "content": user_prompt,
            }
        ],
    )

    parts: list[str] = []
    for block in response.content:
        text = getattr(block, "text", None)
        if text:
            parts.append(text)

    result = "\n".join(parts).strip()
    if not result:
        raise RuntimeError("Claude returned an empty response.")

    return result
