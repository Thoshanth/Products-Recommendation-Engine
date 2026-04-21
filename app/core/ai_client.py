"""
ai_client.py — OpenRouter client wrapping Nemotron (OpenAI-compatible API).
Used for embeddings-style scoring and AI-powered recommendations.
"""
from openai import OpenAI
from app.core.config import get_settings

settings = get_settings()

_client: OpenAI | None = None


def get_ai_client() -> OpenAI:
    """Returns a singleton OpenAI-compatible client pointed at OpenRouter."""
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
        )
    return _client


def chat_completion(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.3,
    max_tokens: int = 1024,
) -> str:
    """
    Single-turn chat via Nemotron on OpenRouter.
    Returns the assistant message text.
    """
    client = get_ai_client()
    response = client.chat.completions.create(
        model=settings.nemotron_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
        extra_headers={
            "HTTP-Referer": "https://shopmind-ai.app",
            "X-Title": "ShopMind AI",
        },
    )
    return response.choices[0].message.content.strip()


def ping_ai() -> bool:
    """Health-check: confirm OpenRouter key is set."""
    return bool(settings.openrouter_api_key)