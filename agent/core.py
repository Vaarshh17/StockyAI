"""
agent/core.py — The Agent Loop. Heart of Stocky AI.

Flow: user input → ILMU ilmu-glm-5.1 (Z.ai / YTL AI Labs) → tool calls → response

Model: ilmu-glm-5.1 via ILMU API (api.ilmu.ai/v1)
  MODEL_SMART → user-facing agent loop, morning brief, instinct (default)
  MODEL_FAST  → lightweight proactive scheduler jobs (currently same model)

Owner: Person 1
"""
import hashlib
import json
import logging
import time
import uuid

from services.glm import call_llm
from agent.tools import TOOLS, execute_tool
from agent.prompts import get_system_prompt
from agent.memory import get_history, save_turn, save_draft
from agent.persona import get_persona, load_persona

logger = logging.getLogger(__name__)
MAX_TOOL_ITERATIONS = 6

# ── Forwarded message dedup ───────────────────────────────────────────────────
# Stores (content_hash, timestamp) per user. Ignores re-forwards within 60s.
_forwarded_seen: dict[int, tuple[str, float]] = {}
FORWARD_DEDUP_WINDOW_SEC = 60


async def run_agent(
    user_id: int,
    input_text: str = None,
    input_forwarded: dict = None,
    input_type: str = "text",
    use_fast_model: bool = False,
    save_history: bool = True,  # False for scheduler/proactive briefs
) -> dict:
    """
    Run the agent for one user message.

    Args:
        save_history: Set False for proactive/scheduler calls so the scheduler
                      prompt doesn't pollute the user's conversation history.

    Returns:
        { "text": str, "needs_approval": bool, "draft_id": str | None }
    """
    history = get_history(user_id) if save_history else []

    # ── 0. Load persona (use cached or fetch from DB) ─────────────────────────
    persona = get_persona(user_id) or await load_persona(user_id)

    # ── 1. Build user message ─────────────────────────────────────────────────
    if input_type == "forwarded" and input_forwarded:
        raw_text = input_forwarded.get("text", "")

        # ── Dedup: ignore if same content forwarded within the window ─────────
        content_hash = hashlib.md5(raw_text.encode()).hexdigest()
        last_hash, last_ts = _forwarded_seen.get(user_id, ("", 0.0))
        now = time.time()
        if content_hash == last_hash and (now - last_ts) < FORWARD_DEDUP_WINDOW_SEC:
            logger.info(f"[agent] duplicate forwarded message from user={user_id} — ignored (within {FORWARD_DEDUP_WINDOW_SEC}s window)")
            return {"text": "", "needs_approval": False, "draft_id": None, "skip": True}
        _forwarded_seen[user_id] = (content_hash, now)

        # ── Force tool check before any response ─────────────────────────────
        # Prepend a mandatory instruction so the model ALWAYS queries live data
        # before commenting on the forwarded content (price quotes, etc.)
        text = (
            f"[Mesej dimajukan dari {input_forwarded['original_sender']} "
            f"pada {input_forwarded['original_date']}]\n{raw_text}\n\n"
            "INSTRUCTION: Before replying, you MUST call the relevant tools to "
            "check live data (inventory, supplier prices, FAMA benchmark, weather). "
            "Do NOT respond based on the forwarded text alone. "
            "Cross-reference with current stock and prices first, then give your analysis."
        )
        user_msg = {"role": "user", "content": text}
    else:
        user_msg = {"role": "user", "content": input_text or ""}

    # ── 2. Assemble messages ──────────────────────────────────────────────────
    messages = [{"role": "system", "content": get_system_prompt(persona)}] + history + [user_msg]
    logger.info(f"[agent] user={user_id} type={input_type} history={len(history)} persona={'yes' if persona else 'no'}")

    # ── 3. The tool-calling loop ──────────────────────────────────────────────
    response = {}
    iteration = 0
    for iteration in range(MAX_TOOL_ITERATIONS):
        logger.info(f"[agent] ── iteration {iteration + 1} ──────────────────────")
        response = await call_llm(messages, tools=TOOLS, use_fast_model=use_fast_model)
        tool_calls = response.get("tool_calls")

        if not tool_calls:
            logger.info(f"[agent] no tool calls → final answer ready")
            break  # Model has a final answer

        logger.info(f"[agent] model wants {len(tool_calls)} tool call(s):")
        messages.append({
            "role": "assistant",
            "content": response.get("content"),
            "tool_calls": tool_calls,
        })
        for tc in tool_calls:
            name = tc["function"]["name"]
            args = json.loads(tc["function"]["arguments"])
            logger.info(f"[agent]   → calling {name}({args})")
            result = await execute_tool(name, args)
            logger.info(f"[agent]   ← {name} returned: {str(result)[:120]}")
            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": json.dumps(result, ensure_ascii=False, default=str),
            })
    else:
        logger.warning(f"[agent] ⚠️  Max tool iterations ({MAX_TOOL_ITERATIONS}) hit for user {user_id}")

    # If max iterations hit, content may be None (last msg had tool_calls, no text)
    final_text = response.get("content") or ""
    if not final_text:
        final_text = "Maaf, saya menghadapi masalah teknikal. Sila cuba lagi."
        logger.warning(f"[agent] empty final content for user={user_id} — returning fallback")
    logger.info(f"[agent] final reply ({len(final_text)} chars): {final_text[:80]}...")

    # ── 4. Check for draft messages needing approval ──────────────────────────
    if "DRAFT_MESSAGE::" in final_text:
        logger.info(f"[agent] draft message detected → sending for approval")
        return _handle_draft(user_id, final_text)

    # ── 5. Save conversation turn (only for real user interactions) ───────────
    if save_history:
        assistant_msg = {"role": "assistant", "content": final_text}
        save_turn(user_id, user_msg, assistant_msg)
        logger.info(f"[agent] turn saved to memory")

    return {"text": final_text, "needs_approval": False, "draft_id": None}


async def run_proactive_brief(user_id: int, brief_type: str = "morning") -> str:
    """
    Entry point for all scheduler jobs.
    Uses ilmu-glm-5.1 (Z.ai / YTL AI Labs) via ILMU API.
    Does NOT save to conversation history — proactive prompts must never
    pollute the user's real conversation context.
    """
    # ── Load persona — check cache first, then DB ─────────────────────────────
    persona = get_persona(user_id) or await load_persona(user_id)
    lang = (persona or {}).get("language", "English")

    # Inject festival context into morning brief and weekly digest
    from services.festivals import get_upcoming_events, format_events_for_brief
    upcoming_events = get_upcoming_events(within_days=21)
    festival_block = format_events_for_brief(upcoming_events, language=lang)

    morning_extra = f"\n\n{festival_block}" if festival_block else ""

    prompts = {
        "morning": (
            "Jana briefing pagi untuk peniaga. "
            "Semak inventori, harga pembekal, cuaca, dan kredit tertunggak. "
            "Buat senarai belian untuk hari ini dengan sebab yang jelas. "
            "Format: cadang beli (🟢/🟡/🔴), hutang tertunggak, nota cuaca."
            + morning_extra
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
        "credit": (
            "Semak semua kredit tertunggak. "
            "Senaraikan pembayaran matang hari ini atau esok. "
            "Sediakan ringkasan ringkas."
        ),
        "digest": (
            "Jana digest perniagaan mingguan. "
            "Sertakan: pendapatan minggu ini vs minggu lalu, komoditi terbaik/terburuk, "
            "kredit tertunggak, dan SATU penemuan penting yang mungkin peniaga tidak perasan."
            + morning_extra
        ),
    }

    # Simple jobs (spoilage, velocity, credit) → fast model
    # Complex jobs (morning, digest) → smart model
    use_fast = brief_type in ("spoilage", "velocity", "credit")

    prompt = prompts.get(brief_type, prompts["morning"])
    result = await run_agent(
        user_id=user_id,
        input_text=prompt,
        input_type="text",
        use_fast_model=use_fast,
        save_history=False,   # ← do NOT pollute the user's conversation history
    )
    text = result["text"]

    # Append Stocky's Instinct for morning brief and weekly digest
    if brief_type in ("morning", "digest"):
        from agent.instinct import get_instinct
        instinct = await get_instinct(language=lang)
        if instinct:
            text += f"\n\n🔮 {instinct}"

    return text


async def extract_proposed_actions(brief_text: str, user_id: int) -> list[dict]:
    """
    After the morning brief is generated, run a second lightweight Z.ai call
    to extract structured buy recommendations as JSON.

    Stores them in pending_actions and returns the list.
    Returns [] if none found or extraction fails.
    """
    import json
    import re
    from services.glm import call_llm
    from agent.memory import save_pending_actions

    messages = [
        {
            "role": "system",
            "content": (
                "Extract buy recommendations from this morning brief. "
                "Return ONLY a valid JSON array — no explanation, no markdown, no other text. "
                'Format: [{"commodity": "tomato", "quantity_kg": 3000, '
                '"supplier_name": "Pak Ali", "price_per_kg": 2.60, "reason": "brief reason"}] '
                "If there are no specific buy recommendations with a named supplier and quantity, return []"
            ),
        },
        {"role": "user", "content": brief_text},
    ]

    try:
        response = await call_llm(messages, tools=None, use_fast_model=True)
        content = (response.get("content") or "").strip()

        # Pull out the JSON array even if there's surrounding noise
        match = re.search(r"\[.*\]", content, re.DOTALL)
        if not match:
            return []

        actions = json.loads(match.group())
        if not isinstance(actions, list) or not actions:
            return []

        # Validate each action has the minimum required fields
        valid = []
        for a in actions:
            if a.get("commodity") and a.get("quantity_kg") and a.get("supplier_name"):
                valid.append(a)

        if valid:
            save_pending_actions(user_id, valid)
            logger.info(f"[agent] extracted {len(valid)} proposed actions for user={user_id}")

        return valid

    except Exception as e:
        logger.error(f"[agent] action extraction failed: {e}")
        return []


def _handle_draft(user_id: int, text: str) -> dict:
    """Extract a DRAFT_MESSAGE and store for approval."""
    try:
        parts = text.split("DRAFT_MESSAGE::")[1].split("::", 2)
        recipient  = parts[0].strip()
        language   = parts[1].strip()
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
