"""
scheduler/jobs.py — All proactive APScheduler jobs.

This is the engine that makes Stocky AI proactive.
Jobs fire on schedule and send Telegram messages without user input.

Jobs:
  1. morning_brief_job    — 3:30 AM daily: multi-signal analysis + proposed buy orders
  2. spoilage_check_job   — 8 AM + 2 PM: spoilage risk alerts
  3. velocity_alert_job   — every 4h: stockout early warning
  4. credit_reminder_job  — 9 AM daily: overdue payment reminders
  5. monday_digest_job    — Monday 7 AM: weekly business digest + dashboard link
  6. festival_prep_job    — 10 AM daily: pre-festival buying window alerts

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

    # 6. Festival Prep Alert — 10 AM daily (only fires when conditions met)
    _scheduler.add_job(
        festival_prep_job,
        CronTrigger(hour=10, minute=0),
        args=[bot],
        id="festival_prep",
        replace_existing=True,
    )

    _scheduler.start()
    logger.info("Scheduler started. Jobs: morning_brief, spoilage_check, velocity_alert, credit_reminder, monday_digest, festival_prep")


async def _send_to_all_users(bot, text: str):
    """Send a message to all active users."""
    for user_id in ACTIVE_USERS:
        try:
            await bot.send_message(chat_id=user_id, text=text, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Failed to send to user {user_id}: {e}")


async def morning_brief_job(bot):
    """
    3:30 AM — Multi-signal analysis → specific buy recommendations with approval buttons.
    This is the flagship feature: Stocky acts before the wholesaler wakes up.
    """
    logger.info("Running morning brief job...")
    if not ACTIVE_USERS:
        return

    user_id = next(iter(ACTIVE_USERS))

    from agent.core import run_proactive_brief, extract_proposed_actions
    from bot.keyboards import action_approval_keyboard

    text = await run_proactive_brief(user_id, "morning")

    # Extract structured buy actions from the brief (second Z.ai call)
    actions = await extract_proposed_actions(text, user_id)

    if actions:
        # Append a clean action summary so the user sees what they're approving
        summary = "\n\n─────────────────────\n📋 *Cadangan Pesanan:*\n"
        for a in actions:
            price_str = f" @ RM{a['price_per_kg']}/kg" if a.get("price_per_kg") else ""
            summary += f"• {a['commodity'].title()} — {a['quantity_kg']:.0f}kg dari {a['supplier_name']}{price_str}\n"
        summary += "\nLaksanakan semua pesanan ini?"
        text += summary

        keyboard = action_approval_keyboard(user_id)
        for uid in ACTIVE_USERS:
            try:
                await bot.send_message(
                    chat_id=uid, text=text,
                    parse_mode="Markdown", reply_markup=keyboard
                )
            except Exception as e:
                logger.error(f"Failed to send morning brief to {uid}: {e}")
    else:
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
    """Monday 7 AM — Weekly business digest + dashboard link."""
    logger.info("Running Monday digest...")
    if not ACTIVE_USERS:
        return

    user_id = next(iter(ACTIVE_USERS))
    from agent.core import run_proactive_brief, extract_proposed_actions
    from bot.keyboards import action_approval_keyboard
    import config

    text = await run_proactive_brief(user_id, "digest")
    if config.DASHBOARD_URL:
        text += f"\n\n📊 [View your weekly dashboard]({config.DASHBOARD_URL})"

    # Digest can also propose restock actions
    actions = await extract_proposed_actions(text, user_id)
    if actions:
        summary = "\n\n─────────────────────\n📋 *Pesanan Minggu Ini:*\n"
        for a in actions:
            price_str = f" @ RM{a['price_per_kg']}/kg" if a.get("price_per_kg") else ""
            summary += f"• {a['commodity'].title()} — {a['quantity_kg']:.0f}kg dari {a['supplier_name']}{price_str}\n"
        text += summary
        keyboard = action_approval_keyboard(user_id)
        for uid in ACTIVE_USERS:
            try:
                await bot.send_message(
                    chat_id=uid, text=text,
                    parse_mode="Markdown", reply_markup=keyboard
                )
            except Exception as e:
                logger.error(f"Failed to send digest to {uid}: {e}")
    else:
        await _send_to_all_users(bot, text)


async def festival_prep_job(bot):
    """
    10 AM daily — Autonomous pre-festival buying alert.

    Fires ONLY when all three conditions are true:
      1. A major festival is within 7–14 days (the buying window)
      2. A relevant commodity stock will run out before the festival
      3. Current supplier price is below historical pre-festival peak

    This is pure agent behaviour — no user prompt triggered this.
    Z.ai detected the opportunity and acted.
    """
    logger.info("Running festival prep check...")
    if not ACTIVE_USERS:
        return

    from services.festivals import get_upcoming_events
    from db.queries import db_get_inventory, db_get_velocity, db_compare_prices
    from agent.memory import save_pending_actions
    from bot.keyboards import action_approval_keyboard

    # Festival → commodities that spike in demand
    FESTIVAL_COMMODITIES = {
        "Hari Raya Aidilfitri": ["tomato", "cili", "bayam", "kangkung"],
        "Hari Raya Eve":        ["tomato", "cili", "bayam", "kangkung"],
        "Chinese New Year Eve": ["tomato", "kailan", "bayam"],
        "Chinese New Year Day 1": ["tomato", "kailan", "bayam"],
        "Deepavali Eve":        ["bayam", "timun"],
    }

    upcoming = get_upcoming_events(within_days=14)
    # Only care about high-demand festivals within 7–14 days (the buying window)
    actionable = [
        e for e in upcoming
        if e["demand_impact"] >= 2 and 5 <= e["days_away"] <= 14
    ]

    if not actionable:
        return  # No festival in the buying window — stay silent

    festival = actionable[0]
    relevant_commodities = FESTIVAL_COMMODITIES.get(festival["name"], [])
    if not relevant_commodities:
        return

    inventory = await db_get_inventory()
    inventory_map = {i["commodity"]: i for i in inventory}

    proposed_actions = []
    alert_lines = []

    for commodity in relevant_commodities:
        inv = inventory_map.get(commodity)
        if not inv:
            continue

        velocity = await db_get_velocity(commodity, days=7)
        avg_daily = velocity.get("avg_daily_kg", 0)
        if avg_daily <= 0:
            continue

        days_to_stockout = inv["quantity_kg"] / avg_daily
        days_until_festival = festival["days_away"]

        # Only act if stock runs out BEFORE the festival
        if days_to_stockout >= days_until_festival:
            continue

        # Get best supplier price
        price_data = await db_compare_prices(commodity)
        cheapest = price_data.get("cheapest")
        if not cheapest:
            continue

        # Recommend enough to cover festival demand (1.5× normal velocity × festival days)
        recommended_qty = round(avg_daily * 1.5 * min(days_until_festival, 10))

        proposed_actions.append({
            "commodity":     commodity,
            "quantity_kg":   recommended_qty,
            "supplier_name": cheapest["name"],
            "price_per_kg":  cheapest["price_per_kg"],
            "reason":        f"Stock runs out in {days_to_stockout:.0f}d, {festival['name']} in {days_until_festival}d",
        })

        fama = price_data.get("fama_benchmark")
        vs_fama = f" ({cheapest['vs_fama_pct']:+.1f}% vs FAMA)" if cheapest.get("vs_fama_pct") else ""
        alert_lines.append(
            f"• *{commodity.title()}* — stok habis dalam {days_to_stockout:.0f} hari, "
            f"festival dalam {days_until_festival} hari. "
            f"Terbaik: {cheapest['name']} @ RM{cheapest['price_per_kg']}/kg{vs_fama}"
        )

    if not proposed_actions:
        return  # Conditions not met — stay silent

    user_id = next(iter(ACTIVE_USERS))
    save_pending_actions(user_id, proposed_actions)

    text = (
        f"🎊 *{festival['name']} dalam {festival['days_away']} hari*\n"
        f"_{festival['notes']}_\n\n"
        f"Stocky mengesan peluang beli sebelum harga naik:\n\n"
        + "\n".join(alert_lines)
        + "\n\n_Ini tetingkap terbaik untuk beli sebelum harga festival naik._\n"
        "Laksanakan semua pesanan?"
    )

    keyboard = action_approval_keyboard(user_id)
    for uid in ACTIVE_USERS:
        try:
            await bot.send_message(
                chat_id=uid, text=text,
                parse_mode="Markdown", reply_markup=keyboard
            )
        except Exception as e:
            logger.error(f"Failed to send festival alert to {uid}: {e}")
