"""
main.py — Entry point. Starts the Telegram bot and scheduler.

Run with: python main.py
"""
import asyncio
import logging
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, filters, CommandHandler

from config import BOT_TOKEN, validate
from bot.handlers import handle_message, handle_callback, handle_start, handle_command_trigger, handle_command_finance, handle_help, ACTIVE_USERS
from db.models import init_db
from db.seed import seed_demo_data
from scheduler.jobs import start_scheduler

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def post_init(application):
    """Runs after bot starts — init DB, seed data, restore users, start scheduler."""
    logger.info("Initialising database...")
    await init_db()

    logger.info("Seeding demo data (skips if already seeded)...")
    await seed_demo_data()

    # Restore ACTIVE_USERS from DB so the scheduler has targets even after a restart
    from db.queries import db_get_all_user_ids
    persisted = await db_get_all_user_ids()
    ACTIVE_USERS.update(persisted)
    if persisted:
        logger.info(f"✅ Restored {len(persisted)} active user(s) from DB: {persisted}")

    logger.info("Starting proactive scheduler...")
    start_scheduler(application.bot)

    logger.info("✅ Stocky AI is ready.")


def main():
    validate()

    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    # Commands
    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(CommandHandler("help", handle_help))
    app.add_handler(CommandHandler("trigger_brief", handle_command_trigger))    # demo shortcut
    app.add_handler(CommandHandler("trigger_finance", handle_command_finance))  # finance demo

    # Messages (photo removed — ILMU models don't support vision)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.VOICE, handle_message))
    app.add_handler(MessageHandler(filters.FORWARDED, handle_message))

    # Inline keyboard callbacks (approve/edit)
    app.add_handler(CallbackQueryHandler(handle_callback))

    logger.info("Starting bot (polling)...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
