"""
services/glm.py — GLM API client (Z.AI / Zhipu).

Handles all communication with the GLM API.
Owner: Person 1
"""
import base64
import json
import logging
import httpx
from config import GLM_API_KEY, GLM_API_URL, GLM_MODEL, DEMO_MODE

logger = logging.getLogger(__name__)


async def call_glm(messages: list, tools: list = None) -> dict:
    """
    Send messages to GLM and return the assistant's response dict.

    Returns:
        dict with keys: 'content' (str | None), 'tool_calls' (list | None)
    """
    if DEMO_MODE:
        return await _mock_response(messages)

    payload = {
        "model": GLM_MODEL,
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 1024,
    }
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            GLM_API_URL,
            headers={
                "Authorization": f"Bearer {GLM_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()

    message = data["choices"][0]["message"]
    logger.debug(f"GLM response: {message}")
    return message


def encode_image_to_base64(image_bytes: bytes) -> str:
    """Convert raw image bytes to base64 string for GLM vision input."""
    return base64.b64encode(image_bytes).decode("utf-8")


def build_image_message(image_bytes: bytes, caption: str = "") -> dict:
    """Build a GLM-compatible user message containing an image."""
    b64 = encode_image_to_base64(image_bytes)
    content = [
        {
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
        }
    ]
    if caption:
        content.append({"type": "text", "text": caption})
    else:
        content.append({
            "type": "text",
            "text": "Baca gambar ini dan ekstrak maklumat berkaitan inventori atau harga.",
        })
    return {"role": "user", "content": content}


async def _mock_response(messages: list) -> dict:
    """Returns a canned response for demo/testing without hitting the API."""
    last = messages[-1]
    text = last.get("content", "") if isinstance(last.get("content"), str) else ""
    return {
        "content": f"[DEMO MODE] Saya terima: '{text[:60]}'. GLM API key belum dikonfigurasi.",
        "tool_calls": None,
    }
