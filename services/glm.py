"""
services/glm.py — ILMU API client (Z.ai / YTL AI Labs).

Uses the OpenAI-compatible endpoint at api.ilmu.ai/v1.
Model: ilmu-glm-5.1 (both MODEL_SMART and MODEL_FAST on Claw Free plan).

Owner: Person 1
"""
import os
import logging
from openai import AsyncOpenAI
import config  # import module, not values — so we always get the live value

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    """Lazy-init the ILMU client (OpenAI-compatible)."""
    global _client
    if _client is None:
        key = config.ILMU_API_KEY or os.getenv("ILMU_API_KEY", "")
        url = config.ILMU_API_URL or os.getenv("ILMU_API_URL", "https://api.ilmu.ai/v1")
        logger.info(f"Creating ILMU client — key={key[:12]}... url={url}")
        _client = AsyncOpenAI(api_key=key, base_url=url)
    return _client


async def call_llm(
    messages: list,
    tools: list = None,
    use_fast_model: bool = False,
) -> dict:
    """
    Send messages to ILMU and return the assistant's response.

    Args:
        messages:       Full conversation history including system prompt.
        tools:          Tool schemas. If provided, model may call them.
        use_fast_model: If True, uses MODEL_FAST (currently ilmu-glm-5.1).
                        Use for proactive scheduler jobs. Default False → MODEL_SMART.

    Returns:
        dict with keys:
            'content'    (str | None)  — final text response
            'tool_calls' (list | None) — list of tool call dicts
    """
    if config.DEMO_MODE:
        return _mock_response(messages)

    model = config.MODEL_FAST if use_fast_model else config.MODEL_SMART
    client = _get_client()

    kwargs: dict = {
        "model": model,
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 2048,
    }
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"

    logger.debug(f"Calling ILMU [{model}] with {len(messages)} messages")
    response = await client.chat.completions.create(**kwargs)
    msg = response.choices[0].message

    # Normalise tool_calls to plain dicts (same shape our dispatcher expects)
    tool_calls = None
    if msg.tool_calls:
        tool_calls = [
            {
                "id": tc.id,
                "type": "function",   # required by ILMU/GLM API
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                },
            }
            for tc in msg.tool_calls
        ]

    logger.debug(f"ILMU [{model}] → content={bool(msg.content)} tools={len(tool_calls or [])}")
    return {"content": msg.content, "tool_calls": tool_calls}


def _mock_response(messages: list) -> dict:
    """Canned response for DEMO_MODE — no API call made."""
    last = messages[-1]
    text = last.get("content", "") if isinstance(last.get("content"), str) else ""
    return {
        "content": f"[DEMO MODE] Received: '{text[:60]}'. Set DEMO_MODE=False and add ILMU_API_KEY to go live.",
        "tool_calls": None,
    }
