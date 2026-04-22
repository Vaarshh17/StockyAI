"""
scheduler/jobs.py — All proactive APScheduler jobs.

This is the engine that makes Stocky AI proactive.
Jobs fire on schedule and send Telegram messages without user input.

Owner: Person 4
"""
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from config import MORNING_BRIEF_HOUR, MORNING_BRIEF_MIN
from bot.handlers import ACTIVE_USERS

logger = logging.getLogger(__name__)
_scheduler = AsyncIOScheduler(timezone="Asia/Kuala_Lumpur")


def start_scheduler(bot):
    """Register all jobs and start the scheduler."""

    # 1. Morning Brief — 3:30 AM daily
    _scheduler.add_job(
        morning_brief_job,
        CronTrigger(hour=MORNING_BRIEF_HOUR, minute=MORNING_BRIEF_MIN),
        args=[bot],
        id="morning_brief",
        replace_existing=True,
    )

    # 2. Spoilage Check — 8 AM and 2 PM daily
    _scheduler.add_job(
        spoilage_check_job,
        CronTrigger(hour="8,14", minute=0),
        args=[bot],
        id="spoilage_check",
        replace_existing=True,
    )

    # 3. Velocity Alert — every 4 hours
    _scheduler.add_job(
        velocity_alert_job,
        CronTrigger(hour="6,10,14,18,22", minute=0),
        args=[bot],
        id="velocity_alert",
        replace_existing=True,
    )

    # 4. Credit Reminder — 9 AM daily
    _scheduler.add_job(
        credit_reminder_job,
        CronTrigger(hour=9, minute=0),
        args=[bot],
        id="credit_reminder",
        replace_existing=True,
    )

    # 5. Monday Digest — Monday 7 AM
    _scheduler.add_job(
        monday_digest_job,
        CronTrigger(day_of_week="mon", hour=7, minute=0),
        args=[bot],
        id="monday_digest",
        replace_existing=True,
    )

    _scheduler.start()
    logger.info("Scheduler started. Jobs registered: morning_brief, spoilage_check, velocity_alert, credit_reminder, monday_digest")


async def _send_to_all_users(bot, text: str):
    """Send a message to all active users."""
    for user_id in ACTIVE_USERS:
        try:
            await bot.send_message(chat_id=user_id, text=text, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Failed to send to user {user_id}: {e}")


async def morning_brief_job(bot):
    """3:30 AM — Generate and send the morning buy brief."""
    logger.info("Running morning brief job...")
    if not ACTIVE_USERS:
        return

    # Use first active user as context for the brief
    # In production, generate per-user. For hackathon, one user is fine.
    user_id = next(iter(ACTIVE_USERS))

    from agent.core import run_proactive_brief
    text = await run_proactive_brief(user_id, "morning")
    await _send_to_all_users(bot, text)


async def spoilage_check_job(bot):
    """8 AM + 2 PM — Check for spoilage risk. Only send if risk detected."""
    logger.info("Running spoilage check...")
    if not ACTIVE_USERS:
        return

    from db.queries import db_get_inventory
    from services.weather import get_forecast
    from datetime import date

    inventory = await db_get_inventory()
    forecast = await get_forecast()

    # Check if any items are within 2 days of expiry AND rain is coming
    rain_days = [f for f in forecast[:3] if f.get("is_rainy")]
    at_risk = [
        item for item in inventory
        if item["days_remaining"] <= 2 and item["quantity_kg"] > 100
    ]

    if not at_risk:
        return  # No alert needed

    lines = ["⚠️ *Amaran Risiko Rosak*\n"]
    for item in at_risk:
        lines.append(
            f"🔴 *{item['commodity'].title()}* — {item['quantity_kg']}kg, "
            f"{item['days_remaining']} hari lagi"
        )
    if rain_days:
        lines.append(f"\n🌧️ Hujan dijangka: {', '.join(r['date'] for r in rain_days[:2])}")
        lines.append("Cadang jual hari ini sebelum pasar perlahan.")

    await _send_to_all_users(bot, "\n".join(lines))


async def velocity_alert_job(bot):
    """Every 4 hours — Alert on unusual sell-through velocity."""
    logger.info("Running velocity check...")
    if not ACTIVE_USERS:
        return

    from db.queries import db_get_inventory, db_get_velocity
    inventory = await db_get_inventory()

    alerts = []
    for item in inventory:
        commodity = item["commodity"]
        velocity = await db_get_velocity(commodity)
        avg_daily = velocity["avg_daily_kg"]

        if avg_daily <= 0:
            continue

        # Calculate days until stockout
        days_to_stockout = item["quantity_kg"] / avg_daily if avg_daily > 0 else 999

        # Alert: stockout within 2 days
        if days_to_stockout < 2:
            alerts.append(
                f"⚡ *{commodity.title()}* jual {avg_daily:.0f}kg/hari. "
                f"Stok *habis dalam {days_to_stockout:.1f} hari*. Perlu restock segera."
            )

    if alerts:
        await _send_to_all_users(bot, "⚡ *Alert Kelajuan Stok*\n\n" + "\n".join(alerts))


async def credit_reminder_job(bot):
    """9 AM — Alert on credit due today or tomorrow."""
    logger.info("Running credit reminder check...")
    if not ACTIVE_USERS:
        return

    from db.queries import db_get_credit
    credits = await db_get_credit()

    urgent = [c for c in credits if c["due_today"] or c["days_overdue"] > 0]
    if not urgent:
        return

    lines = ["💸 *Peringatan Bayaran*\n"]
    for c in urgent:
        status = "🔴 LEWAT" if c["days_overdue"] > 0 else "🟡 Matang hari ini"
        lines.append(f"{status}: *{c['buyer_name']}* — RM{c['amount_rm']:.0f}")

    await _send_to_all_users(bot, "\n".join(lines))


async def monday_digest_job(bot):
    """Monday 7 AM — Weekly business digest."""
    logger.info("Running Monday digest...")
    if not ACTIVE_USERS:
        return

    user_id = next(iter(ACTIVE_USERS))
    from agent.core import run_proactive_brief
    text = await run_proactive_brief(user_id, "digest")
    await _send_to_all_users(bot, text)
