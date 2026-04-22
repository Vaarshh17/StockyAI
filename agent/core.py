"""
agent/core.py — The Agent Loop. Heart of Stocky AI.

Flow: user input → GLM (with tools) → tool calls → GLM → response
Owner: Person 1
"""
import json
import logging
import uuid

from services.glm import call_glm, build_image_message
from agent.tools import TOOLS, execute_tool
from agent.prompts import get_system_prompt
from agent.memory import get_history, save_turn, save_draft

logger = logging.getLogger(__name__)
MAX_TOOL_ITERATIONS = 6


async def run_agent(
    user_id: int,
    input_text: str = None,
    input_image: bytes = None,
    caption: str = "",
    input_forwarded: dict = None,
    input_type: str = "text",
) -> dict:
    """
    Run the agent for one user message.

    Returns:
        { "text": str, "needs_approval": bool, "draft_id": str | None }
    """
    history = get_history(user_id)

    # ── 1. Build user message ─────────────────────────────────────────────────
    if input_type == "image":
        user_msg = build_image_message(input_image, caption)
    elif input_type == "forwarded" and input_forwarded:
        text = (
            f"[Mesej dimajukan dari {input_forwarded['original_sender']} "
            f"pada {input_forwarded['original_date']}]\n{input_forwarded.get('text', '')}"
        )
        user_msg = {"role": "user", "content": text}
    else:
        user_msg = {"role": "user", "content": input_text or ""}

    # ── 2. Assemble messages ──────────────────────────────────────────────────
    messages = [{"role": "system", "content": get_system_prompt()}] + history + [user_msg]

    # ── 3. The tool-calling loop ──────────────────────────────────────────────
    response = {}
    for iteration in range(MAX_TOOL_ITERATIONS):
        response = await call_glm(messages, tools=TOOLS)
        tool_calls = response.get("tool_calls")

        if not tool_calls:
            break   # GLM has a final answer

        messages.append({
            "role": "assistant",
            "content": response.get("content"),
            "tool_calls": tool_calls,
        })
        for tc in tool_calls:
            args = json.loads(tc["function"]["arguments"])
            result = await execute_tool(tc["function"]["name"], args)
            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": json.dumps(result, ensure_ascii=False, default=str),
            })
    else:
        logger.warning(f"Max iterations hit for user {user_id}")

    final_text = response.get("content") or "Maaf, cuba lagi."

    # ── 4. Check for draft messages needing approval ──────────────────────────
    if "DRAFT_MESSAGE::" in final_text:
        return _handle_draft(user_id, final_text)

    # ── 5. Save conversation turn ─────────────────────────────────────────────
    assistant_msg = {"role": "assistant", "content": final_text}
    save_turn(user_id, user_msg, assistant_msg)

    return {"text": final_text, "needs_approval": False, "draft_id": None}


async def run_proactive_brief(user_id: int, brief_type: str = "morning") -> str:
    """
    Entry point for all scheduler jobs.
    For 'morning' and 'digest' types, appends Stocky's Instinct.
    """
    prompts = {
        "morning":  (
            "Jana briefing pagi untuk peniaga. "
            "Semak inventori, harga pembekal, cuaca, dan kredit tertunggak. "
            "Buat senarai belian untuk hari ini dengan sebab yang jelas. "
            "Format: cadang beli (🟢/🟡/🔴), hutang tertunggak, nota cuaca."
        ),
        "spoilage": (
            "Semak semua stok inventori dan ramalan cuaca. "
            "Kenal pasti komoditi berisiko rosak dalam 48 jam. "
            "Beri cadangan spesifik (turun harga / hantar ke pasar / jual segera)."
        ),
        "velocity": (
            "Semak kadar jualan semua komoditi. "
            "Kenal pasti anomali — jual terlalu laju (risiko kehabisan) atau terlalu lambat (risiko rosak). "
            "Alert sahaja jika ada anomali. Senyap jika semua normal."
        ),
        "credit":   (
            "Semak semua kredit tertunggak. "
            "Senaraikan pembayaran matang hari ini atau esok. "
            "Sediakan ringkasan ringkas."
        ),
        "digest":   (
            "Jana digest perniagaan mingguan. "
            "Sertakan: pendapatan minggu ini vs minggu lalu, komoditi terbaik/terburuk, "
            "kredit tertunggak, dan SATU penemuan penting yang mungkin peniaga tidak perasan."
        ),
    }

    prompt = prompts.get(brief_type, prompts["morning"])
    result = await run_agent(user_id=user_id, input_text=prompt, input_type="text")
    text = result["text"]

    # Append Stocky's Instinct for morning brief and weekly digest
    if brief_type in ("morning", "digest"):
        from agent.instinct import get_instinct
        instinct = await get_instinct()
        if instinct:
            text += f"\n\n🔮 {instinct}"

    return text


def _handle_draft(user_id: int, text: str) -> dict:
    """Extract a DRAFT_MESSAGE and store for approval."""
    try:
        parts = text.split("DRAFT_MESSAGE::")[1].split("::", 2)
        recipient = parts[0].strip()
        language  = parts[1].strip()
        draft_text = parts[2].strip()
    except (IndexError, ValueError):
        draft_text = text
        recipient  = "penerima"
        language   = "malay"

    draft_id = str(uuid.uuid4())[:8]
    save_draft(user_id, draft_id, {
        "recipient": recipient,
        "language":  language,
        "message":   draft_text,
    })

    display = (
        f"✉️ Draf mesej untuk *{recipient}*:\n\n"
        f"```\n{draft_text}\n```\n\n"
        f"Hantar atau edit?"
    )
    return {"text": display, "needs_approval": True, "draft_id": draft_id}
