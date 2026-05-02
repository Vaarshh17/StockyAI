"""
agent/core.py — The Agent Loop. Heart of Stocky AI.

Flow: user input → ILMU nemo-super (with tools) → tool calls → model → response

Two-model strategy:
  nemo-super     → user-facing agent loop, morning brief, instinct analysis
  ilmu-nemo-nano → lightweight proactive scheduler jobs

Owner: Person 1
"""
import json
import logging
import uuid
import time

from services.glm import call_llm
from agent.tools import TOOLS, execute_tool
from agent.prompts import get_system_prompt
from agent.memory import get_history, save_turn, save_draft
from agent.persona import get_persona, load_persona

logger = logging.getLogger(__name__)
MAX_TOOL_ITERATIONS = 10


async def run_agent(
    user_id: int,
    input_text: str = None,
    input_forwarded: dict = None,
    input_type: str = "text",
    use_fast_model: bool = False,
) -> dict:
    """
    Run the agent for one user message.

    Returns:
        { "text": str, "needs_approval": bool, "draft_id": str | None }
    """
    history = get_history(user_id)

    # ── 0. Load persona (use cached or fetch from DB) ─────────────────────────
    persona = get_persona(user_id) or await load_persona(user_id)

    # ── 1. Build user message ─────────────────────────────────────────────────
    if input_type == "forwarded" and input_forwarded:
        text = (
            f"[Mesej dimajukan dari {input_forwarded['original_sender']} "
            f"pada {input_forwarded['original_date']}]\n{input_forwarded.get('text', '')}"
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
            result = await execute_tool(name, args, user_id=user_id)
            logger.info(f"[agent]   ← {name} returned: {str(result)[:120]}")
            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": json.dumps(result, ensure_ascii=False, default=str),
            })
            # time.sleep(4)
    else:
        logger.warning(f"[agent] ⚠️  Max tool iterations ({MAX_TOOL_ITERATIONS}) hit for user {user_id}")

    final_text = response.get("content") or "Sorry, something went wrong. Please try again."
    logger.info(f"[agent] final reply ({len(final_text)} chars): {final_text[:80]}...")

    # ── 4. Check for draft messages needing approval ──────────────────────────
    if "DRAFT_MESSAGE::" in final_text:
        logger.info(f"[agent] draft message detected → sending for approval")
        return _handle_draft(user_id, final_text)

    # ── 5. Save conversation turn ─────────────────────────────────────────────
    assistant_msg = {"role": "assistant", "content": final_text}
    save_turn(user_id, user_msg, assistant_msg)
    logger.info(f"[agent] turn saved to memory")

    return {"text": final_text, "needs_approval": False, "draft_id": None}


async def run_proactive_brief(user_id: int, brief_type: str = "morning") -> str:
    """
    Entry point for all scheduler jobs.
    Simple jobs use ilmu-nemo-nano. Morning brief and digest use nemo-super.
    """
    prompts = {
        "morning": (
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
        "credit": (
            "Semak semua kredit tertunggak. "
            "Senaraikan pembayaran matang hari ini atau esok. "
            "Sediakan ringkasan ringkas."
        ),
        "digest": (
            "Jana digest perniagaan mingguan. "
            "Sertakan: pendapatan minggu ini vs minggu lalu, komoditi terbaik/terburuk, "
            "kredit tertunggak, dan SATU penemuan penting yang mungkin peniaga tidak perasan."
        ),
        "finance": (
            "Pengguna ingin tahu profil kewangan dan kelayakan pinjaman mereka. "
            "Panggil get_financial_profile, kemudian bentangkan keputusan dengan jelas: "
            "skor kewangan, jumlah jimat dari FAMA, dan sama ada mereka layak untuk AgroCash-i. "
            "Jika layak, nyatakan jumlah pinjaman dan jemput mereka untuk mohon."
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
    )
    text = result["text"]

    # Append Stocky's Instinct for morning brief and weekly digest (nemo-super only)
    if brief_type in ("morning", "digest"):
        from agent.instinct import get_instinct
        instinct = await get_instinct()
        if instinct:
            text += f"\n\n🔮 {instinct}"

    # Append savings footer to morning brief
    if brief_type == "morning":
        try:
            from db.queries import db_calc_financial_data
            from agent.finance import format_savings_footer
            fin = await db_calc_financial_data()
            footer = format_savings_footer(fin["total_savings_30d_rm"])
            if footer:
                text += footer
        except Exception:
            pass

    # Append dashboard link to weekly digest
    if brief_type == "digest":
        text += (
            "\n\n📈 *Dashboard Penuh:*"
            "\nhttps://stocky-ai-dashboard.lovable.app/"
        )

    return text


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
