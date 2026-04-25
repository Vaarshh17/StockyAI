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
from services.ocr import extract_text_from_image

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
        if response.get("skip"):
            return  # duplicate forward — stay silent

    else:
        # Plain text
        response = await run_agent(
            user_id=user_id,
            input_text=message.text,
            input_type="text",
        )

    await _send_response(update, response)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle incoming photos — delivery notes, invoices, price lists.
    OCR extracts text → Z.ai interprets and calls update_inventory automatically.
    No explicit instruction needed from the user.
    """
    user_id = update.effective_user.id
    ACTIVE_USERS.add(user_id)

    # Onboarding gate
    if get_onboarding_step(user_id) or not is_onboarded(user_id):
        await update.message.reply_text(
            "👋 Let's finish setting you up first!\n\n" + ONBOARDING_QUESTIONS["name"],
            parse_mode="Markdown"
        )
        return

    loading_msg = await update.message.reply_text(
        "📸 _Membaca gambar..._", parse_mode="Markdown"
    )

    # Download the highest-resolution photo
    photo = update.message.photo[-1]
    file = await photo.get_file()
    image_bytes = bytes(await file.download_as_bytearray())

    # Run OCR
    ocr_text = await extract_text_from_image(image_bytes)

    if not ocr_text:
        await loading_msg.edit_text(
            "⚠️ Tidak dapat membaca gambar ini. Cuba ambil gambar yang lebih jelas, "
            "atau taip butiran penghantaran secara manual."
        )
        return

    await loading_msg.edit_text("📸 _Menganalisis nota penghantaran..._", parse_mode="Markdown")
    logger.info(f"[photo] user={user_id} OCR text: {ocr_text[:120]}")

    # Pass OCR text to Z.ai with explicit instruction to parse and log
    instruction = (
        f"User sent a photo of a delivery note or invoice. "
        f"OCR extracted this text:\n\n{ocr_text}\n\n"
        "Parse this to identify: commodity name, quantity (kg), price per kg, supplier name. "
        "Then call update_inventory to log the delivery. "
        "If multiple commodities are listed, call update_inventory once per commodity. "
        "Confirm what was logged in a friendly, brief message."
    )

    response = await run_agent(
        user_id=user_id,
        input_text=instruction,
        input_type="photo",
    )

    await loading_msg.delete()
    await _send_response(update, response)


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline keyboard button presses."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    # ── Draft message approval (existing) ────────────────────────────────────
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

    # ── Action approval (morning brief / festival alert buy orders) ───────────
    elif query.data.startswith("exec_actions_"):
        await _execute_pending_actions(query, user_id)

    elif query.data.startswith("skip_actions_"):
        from agent.memory import clear_pending_actions
        clear_pending_actions(user_id)
        await query.edit_message_text(
            "👍 Ok, skipped. I'll check again tomorrow.",
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


async def _execute_pending_actions(query, user_id: int):
    """
    Execute approved buy orders from morning brief / festival alerts.
    Logs each buy to inventory, drafts WhatsApp messages to suppliers,
    and returns wa.me deep links for one-tap sending.
    """
    from agent.memory import get_pending_actions, clear_pending_actions
    from db.queries import db_update_inventory, db_get_supplier_by_name
    import urllib.parse

    actions = get_pending_actions(user_id)
    if not actions:
        await query.edit_message_text("⚠️ No pending actions found. Try triggering a new brief.")
        return

    await query.edit_message_text("⏳ _Executing orders..._", parse_mode="Markdown")

    results = []
    whatsapp_links = []

    for action in actions:
        commodity     = action.get("commodity", "")
        quantity_kg   = action.get("quantity_kg", 0)
        supplier_name = action.get("supplier_name", "")
        price_per_kg  = action.get("price_per_kg")
        reason        = action.get("reason", "")

        # Log buy to inventory
        try:
            await db_update_inventory(
                commodity=commodity,
                quantity_kg=quantity_kg,
                price_per_kg=price_per_kg,
                supplier_name=supplier_name,
                shelf_life_days=7,
            )
            results.append(f"✅ {commodity.title()} {quantity_kg:.0f}kg @ RM{price_per_kg}/kg — logged")
        except Exception as e:
            logger.error(f"Failed to log buy for {commodity}: {e}")
            results.append(f"⚠️ {commodity.title()} — failed to log: {e}")
            continue

        # Build WhatsApp deep link for supplier
        if supplier_name:
            supplier = await db_get_supplier_by_name(supplier_name)
            if supplier and supplier.get("phone"):
                phone = supplier["phone"].replace("-", "").replace(" ", "")
                if phone.startswith("0"):
                    phone = "6" + phone

                lang = supplier.get("language", "malay")
                if lang == "mandarin":
                    msg = (
                        f"您好 {supplier_name}，\n"
                        f"请准备 {quantity_kg:.0f}kg {commodity} @ RM{price_per_kg}/kg。\n"
                        f"明天送货。谢谢！"
                    )
                else:
                    msg = (
                        f"Salam {supplier_name},\n"
                        f"Boleh sediakan {quantity_kg:.0f}kg {commodity} "
                        f"@ RM{price_per_kg}/kg?\n"
                        f"Hantar esok. Terima kasih!"
                    )

                wa_url = f"https://wa.me/{phone}?text={urllib.parse.quote(msg)}"
                whatsapp_links.append(
                    f"📲 [WhatsApp {supplier_name} for {commodity.title()}]({wa_url})"
                )

    clear_pending_actions(user_id)

    # Build confirmation message
    text = "*✅ Orders Executed*\n\n"
    text += "\n".join(results)

    if whatsapp_links:
        text += "\n\n*Send to suppliers (one tap):*\n"
        text += "\n".join(whatsapp_links)

    await query.edit_message_text(text, parse_mode="Markdown", disable_web_page_preview=True)


async def _send_response(update: Update, response: dict):
    if response.get("needs_approval") and response.get("draft_id"):
        keyboard = approval_keyboard(response["draft_id"])
        await update.message.reply_text(
            response["text"],
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            format_response(response["text"]),
            parse_mode="Markdown"
        )
