"""
services/festivals.py — Malaysian festival & school holiday calendar.

Hardcoded key dates. No API needed — these dates change yearly but are
announced in advance. Update the FESTIVALS list each year.

Owner: Person 4

Why this matters for wholesalers:
- Hari Raya / CNY: 2–3x demand spike 2 weeks before, dead market on the day
- Deepavali: moderate spike in vegetables (banana leaf, herbs)
- School holidays: families eat out less → wet market demand dips
- Eve of any major festival: last buying rush — get stock early
"""
from datetime import date, timedelta
from typing import Optional

# ── 2025–2026 Malaysian Key Dates ─────────────────────────────────────────────
# Format: (date, name_english, name_malay, demand_impact, notes)
# demand_impact: +2 = very high, +1 = high, 0 = neutral, -1 = lower demand

FESTIVALS: list[tuple] = [
    # ── 2025 ──────────────────────────────────────────────────────────────────
    (date(2025, 1, 29), "Chinese New Year Eve",     "Eve Tahun Baru Cina",   +2, "Last buying rush. Prices spike."),
    (date(2025, 1, 30), "Chinese New Year Day 1",   "Tahun Baru Cina Hari 1", -1, "Market closed. No trading."),
    (date(2025, 1, 31), "Chinese New Year Day 2",   "Tahun Baru Cina Hari 2", -1, "Market closed."),
    (date(2025, 3, 28), "Hari Raya Eve",            "Malam Raya",             +2, "Huge buying rush. Restock now."),
    (date(2025, 3, 30), "Hari Raya Aidilfitri",     "Hari Raya Aidilfitri",   -1, "Market quiet. Plan ahead."),
    (date(2025, 3, 31), "Hari Raya Day 2",          "Raya Hari 2",            -1, "Slow trading."),
    (date(2025, 6,  6), "Hari Raya Aidiladha Eve",  "Eve Korban",             +1, "Moderate demand increase."),
    (date(2025, 6,  7), "Hari Raya Aidiladha",      "Hari Raya Korban",       -1, "Market closed."),
    (date(2025, 10, 20), "Deepavali Eve",           "Eve Deepavali",          +1, "Banana leaf, herbs, marigold."),
    (date(2025, 10, 21), "Deepavali",               "Deepavali",              0,  "Moderate activity."),
    (date(2025, 12, 25), "Christmas",               "Krismas",                0,  "Minimal impact on wet market."),

    # ── School Holidays 2025 (Peninsular Malaysia) ────────────────────────────
    (date(2025,  3, 15), "School Mid-term Break",   "Cuti Pertengahan Penggal 1", -1, "14–22 Mac. Slower market traffic."),
    (date(2025,  5, 31), "School Term 2 Break",     "Cuti Pertengahan Tahun",     -1, "31 Mei–15 Jun. Slow period."),
    (date(2025,  8, 23), "School Mid-term Break",   "Cuti Pertengahan Penggal 2", -1, "23–31 Ogos. Quiet."),
    (date(2025, 11, 22), "School Year-End Break",   "Cuti Akhir Tahun",           -1, "22 Nov–4 Jan. Long slow season."),

    # ── 2026 ──────────────────────────────────────────────────────────────────
    (date(2026, 1, 17), "Chinese New Year Eve",     "Eve Tahun Baru Cina",   +2, "Last buying rush. Prices spike. Buy early."),
    (date(2026, 1, 18), "Chinese New Year Day 1",   "Tahun Baru Cina Hari 1", -1, "Market closed."),
    (date(2026, 1, 19), "Chinese New Year Day 2",   "Tahun Baru Cina Hari 2", -1, "Market closed."),
    (date(2026, 3, 19), "Hari Raya Eve",            "Malam Raya",             +2, "Huge buying rush. Restock 1 week before."),
    (date(2026, 3, 20), "Hari Raya Aidilfitri",     "Hari Raya Aidilfitri",   -1, "Market quiet."),
    (date(2026, 3, 21), "Hari Raya Day 2",          "Raya Hari 2",            -1, "Slow trading."),
    (date(2026, 5, 27), "Hari Raya Aidiladha Eve",  "Eve Korban",             +1, "Moderate demand increase."),
    (date(2026, 5, 28), "Hari Raya Aidiladha",      "Hari Raya Korban",       -1, "Market closed."),
    (date(2026, 11,  9), "Deepavali Eve",           "Eve Deepavali",          +1, "Banana leaf, herbs, marigold."),
    (date(2026, 11, 10), "Deepavali",               "Deepavali",              0,  "Moderate activity."),
    (date(2026, 12, 25), "Christmas",               "Krismas",                0,  "Minimal impact."),

    # ── School Holidays 2026 (Peninsular Malaysia, approx) ────────────────────
    (date(2026,  3, 14), "School Mid-term Break",   "Cuti Pertengahan Penggal 1", -1, "~2 weeks. Slower market traffic."),
    (date(2026,  5, 30), "School Term 2 Break",     "Cuti Pertengahan Tahun",     -1, "~2 weeks."),
    (date(2026,  8, 22), "School Mid-term Break",   "Cuti Pertengahan Penggal 2", -1, "~1 week."),
    (date(2026, 11, 21), "School Year-End Break",   "Cuti Akhir Tahun",           -1, "~6 weeks. Long slow season."),
]


def get_upcoming_events(
    within_days: int = 21,
    reference_date: Optional[date] = None,
) -> list[dict]:
    """
    Return Malaysian festivals and holidays within the next N days.

    Args:
        within_days: Look-ahead window (default 21 days)
        reference_date: Override today's date (for testing)

    Returns:
        List of dicts sorted by date:
        [{ date, days_away, name, name_malay, demand_impact, notes, alert_type }]
    """
    today = reference_date or date.today()
    cutoff = today + timedelta(days=within_days)

    upcoming = []
    for fest_date, name_en, name_my, impact, notes in FESTIVALS:
        if today <= fest_date <= cutoff:
            days_away = (fest_date - today).days
            upcoming.append({
                "date":          fest_date.isoformat(),
                "days_away":     days_away,
                "name":          name_en,
                "name_malay":    name_my,
                "demand_impact": impact,
                "notes":         notes,
                "alert_type":    _classify_alert(impact, days_away),
            })

    upcoming.sort(key=lambda x: x["days_away"])
    return upcoming


def _classify_alert(impact: int, days_away: int) -> str:
    """Return an alert severity string for the brief."""
    if impact >= 2 and days_away <= 7:
        return "URGENT_STOCK_UP"
    elif impact >= 2:
        return "PLAN_AHEAD"
    elif impact == 1:
        return "MODERATE_DEMAND"
    elif impact <= -1:
        return "LOW_DEMAND"
    return "INFO"


def format_events_for_brief(events: list[dict], language: str = "English") -> str:
    """
    Format upcoming events as a short context block for the morning brief.
    Injected into the system prompt or user message.
    """
    if not events:
        return ""

    lines = []
    for e in events:
        days = e["days_away"]
        day_label = "today" if days == 0 else f"in {days} day{'s' if days != 1 else ''}"
        impact_emoji = {
            "URGENT_STOCK_UP": "🚨",
            "PLAN_AHEAD":      "📅",
            "MODERATE_DEMAND": "📈",
            "LOW_DEMAND":      "📉",
            "INFO":            "ℹ️",
        }.get(e["alert_type"], "📅")

        if language == "Malay":
            lines.append(
                f"{impact_emoji} {e['name_malay']} ({day_label}) — {e['notes']}"
            )
        else:
            lines.append(
                f"{impact_emoji} {e['name']} ({day_label}) — {e['notes']}"
            )

    return "UPCOMING EVENTS (next 21 days):\n" + "\n".join(lines)
