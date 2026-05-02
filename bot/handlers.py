"""
bot/handlers.py — All Telegram message handlers.
Owner: Person 3
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from agent.core import run_agent, run_proactive_brief
from bot.keyboards import approval_keyboard
from bot.formatters import format_response
from agent.memory import clear_history
from agent.persona import (
    load_persona, get_persona, is_onboarded,
    get_onboarding_step, start_onboarding, process_onboarding_answer,
    ONBOARDING_QUESTIONS,
)
from services.voice import transcribe_voice

logger = logging.getLogger(__name__)

# Store user_id for scheduler to send proactive messages
# In production, store in DB. For hackathon, a module-level set is fine.
ACTIVE_USERS: set[int] = set()


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ACTIVE_USERS.add(user_id)
    clear_history(user_id)

    # Try loading existing persona from DB
    await load_persona(user_id)

    if is_onboarded(user_id):
        persona = get_persona(user_id)
        name = persona.get("name", "there")
        await update.message.reply_text(
            f"🌿 *Welcome back, {name}\\!*\n\nWhat's happening today?",
            parse_mode="MarkdownV2"
        )
    else:
        start_onboarding(user_id)
        await update.message.reply_text(
            "🌿 *Welcome to Stocky AI\\!*\n\n"
            "I'm your AI business partner for wholesale trading\\.\n"
            "Let me get to know you first — just 4 quick questions\\.\n\n"
            + ONBOARDING_QUESTIONS["name"],
            parse_mode="MarkdownV2"
        )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ACTIVE_USERS.add(user_id)
    message = update.message

    # ── Onboarding gate ───────────────────────────────────────────────────────
    if get_onboarding_step(user_id):
        await message.chat.send_action("typing")
        reply, complete = await process_onboarding_answer(user_id, message.text or "")
        await update.message.reply_text(reply, parse_mode="Markdown")
        return

    # If not onboarded and no active session, try DB then start onboarding
    if not is_onboarded(user_id):
        await load_persona(user_id)
        if not is_onboarded(user_id):
            start_onboarding(user_id)
            await update.message.reply_text(
                "👋 Let's get you set up first!\n\n" + ONBOARDING_QUESTIONS["name"],
                parse_mode="Markdown"
            )
            return

    await message.chat.send_action("typing")

    # Route by message type
    if message.voice:
        loading_msg = await update.message.reply_text(
            "_Loading... This may take a moment._",
            parse_mode="Markdown",
        )
        file = await message.voice.get_file()
        voice_bytes = bytes(await file.download_as_bytearray())
        transcript = await transcribe_voice(voice_bytes)
        if not transcript:
            await loading_msg.delete()
            await update.message.reply_text(
                "⚠️ Maaf, tidak dapat dengar nota suara itu. Cuba lagi atau taip mesej anda."
            )
            return
        await loading_msg.delete()
        # Echo back what was heard so user can confirm
        await update.message.reply_text(f'🎙️ _"{transcript}"_', parse_mode="Markdown")
        response = await run_agent(
            user_id=user_id,
            input_text=transcript,
            input_type="voice",
        )

    elif message.forward_origin:
        forward_info = {
            "original_sender": getattr(message.forward_origin, "sender_user_name", None)
                or getattr(getattr(message.forward_origin, "sender_user", None), "full_name", None)
                or "Unknown",
            "original_date": message.forward_origin.date.isoformat(),
            "text": message.text or message.caption or "",
        }
        response = await run_agent(
            user_id=user_id,
            input_forwarded=forward_info,
            input_type="forwarded",
        )

    else:
        # Plain text
        response = await run_agent(
            user_id=user_id,
            input_text=message.text,
            input_type="text",
        )

    await _send_response(update, response)


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline keyboard button presses (approve/edit draft messages)."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data.startswith("approve_"):
        draft_id = query.data.split("_", 1)[1]
        from agent.memory import get_draft
        draft = get_draft(user_id, draft_id)
        if draft:
            await query.edit_message_text(
                f"✅ *Mesej disediakan untuk dihantar:*\n\n"
                f"```\n{draft['message']}\n```\n\n"
                f"_Salin teks di atas dan hantar kepada {draft['recipient']}_",
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text("⚠️ Draf tidak dijumpai. Cuba lagi.")

    elif query.data.startswith("edit_"):
        await query.edit_message_text(
            "✏️ Balas mesej ini dengan versi yang diedit.\n"
            "_Atau taip mesej baharu anda._",
            parse_mode="Markdown"
        )


async def handle_command_trigger(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /trigger_brief — manually trigger any brief (for demo day).
    Usage: /trigger_brief morning | spoilage | velocity | credit | digest
    """
    user_id = update.effective_user.id
    args = context.args
    brief_type = args[0] if args else "morning"

    await update.message.chat.send_action("typing")
    await update.message.reply_text(f"⏳ Menjana {brief_type} brief...")

    text = await run_proactive_brief(user_id, brief_type)
    await update.message.reply_text(text, parse_mode="Markdown")


async def handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /help — Show all available features with example phrases.
    """
    text = (
        "🌿 *Stocky AI — Apa yang saya boleh buat*\n\n"

        "*📦 Inventori & Stok*\n"
        "• \"Stok aku macam mana?\" — semak semua stok sekarang\n"
        "• \"Tomato berapa hari lagi?\" — insight satu komoditi\n"
        "• \"Ada risiko rosak tak?\" — cek bahaya rosak + cuaca\n\n"

        "*🛒 Bekalan & Harga*\n"
        "• Forward mesej harga dari pembekal → dapat keputusan BELI / PASS\n"
        "• \"Nak beli cili, cadangkan pembekal\" — bandingkan harga pembekal\n\n"

        "*💸 Kredit & Hutang*\n"
        "• \"Sapa yang tak bayar lagi?\" — senarai hutang tertunggak\n"
        "• \"Draft peringatan untuk Ali\" — draf mesej tuntutan bayaran\n\n"

        "*💳 Kewangan & Pinjaman*\n"
        "• \"Profil kewangan saya\" — skor kredit dari data perniagaan\n"
        "• \"Mohon pinjaman\" — pakej permohonan Agrobank Digital Niaga\n"
        "• \"Takda modal\" — cek kelayakan + pilihan alternatif\n\n"

        "*📰 Berita & Festival*\n"
        "• \"Ada berita banjir?\" — carian berita pasaran terkini\n"
        "• \"Bila raya haji?\" — tarikh + komoditi yang akan naik permintaan\n\n"

        "*📈 Laporan & Dashboard*\n"
        "• \"Dashboard\" atau \"Laporan\" — pautan ke analytics penuh\n"
        "• \"Digest minggu ni\" — ringkasan perniagaan 7 hari\n\n"

        "*🎙️ Input Suara*\n"
        "• Hantar nota suara — Stocky faham Melayu, Inggeris, Mandarin\n\n"

        "*⚙️ Arahan*\n"
        "`/trigger_brief morning` — jana morning brief sekarang\n"
        "`/trigger_brief spoilage` — semak risiko rosak\n"
        "`/trigger_brief velocity` — semak kelajuan jualan\n"
        "`/trigger_brief credit` — semak pembayaran tertunggak\n"
        "`/trigger_brief digest` — digest mingguan\n"
        "`/trigger_finance` — profil kewangan & tawaran pinjaman"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def handle_command_finance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /trigger_finance — demo the financial profile + loan offer on demand.
    Shows creditworthiness score, savings from FAMA, and loan eligibility.
    """
    user_id = update.effective_user.id
    ACTIVE_USERS.add(user_id)

    await update.message.chat.send_action("typing")
    await update.message.reply_text("⏳ Mengira profil kewangan awak dari data perniagaan...")

    from agent.finance import calculate_financial_profile, format_profile_message
    from db.queries import db_get_persona

    profile = await calculate_financial_profile(user_id)
    persona = await db_get_persona(user_id)
    name = persona.get("name", "Peniaga") if persona else "Peniaga"

    text = format_profile_message(profile, name)
    await update.message.reply_text(text, parse_mode="Markdown")


async def _send_response(update: Update, response: dict):
    if response.get("needs_approval") and response.get("draft_id"):
        keyboard = approval_keyboard(response["draft_id"])
        try:
            await update.message.reply_text(
                response["text"], reply_markup=keyboard, parse_mode="Markdown"
            )
        except Exception:
            await update.message.reply_text(response["text"], reply_markup=keyboard)
    else:
        text = format_response(response["text"])
        try:
            await update.message.reply_text(text, parse_mode="Markdown")
        except Exception:
            # Markdown parse failed (unmatched * or _) — send as plain text
            await update.message.reply_text(text)
