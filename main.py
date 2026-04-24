"""
main.py — Entry point. Starts the Telegram bot and scheduler.

Run with: python main.py
"""
import asyncio
import logging
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, filters, CommandHandler

from config import BOT_TOKEN, validate
from bot.handlers import handle_message, handle_callback, handle_start, handle_command_trigger
from db.models import init_db
from db.seed import seed_demo_data
from scheduler.jobs import start_scheduler

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def post_init(application):
    """Runs after bot starts — init DB, seed data, start scheduler."""
    logger.info("Initialising database...")
    await init_db()

    logger.info("Seeding demo data (skips if already seeded)...")
    await seed_demo_data()

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
    app.add_handler(CommandHandler("trigger_brief", handle_command_trigger))  # demo shortcut

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
