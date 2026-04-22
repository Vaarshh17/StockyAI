"""
services/fama.py — FAMA benchmark price service.

FAMA (Federal Agricultural Marketing Authority) publishes weekly
commodity prices. We seed these into the DB and serve from there.

Owner: Person 4
"""
import logging
from datetime import date, timedelta
from db.queries import get_fama_price

logger = logging.getLogger(__name__)


async def get_benchmark(commodity: str, week_date: date = None) -> dict | None:
    """
    Get FAMA benchmark price for a commodity.

    Args:
        commodity: e.g. "tomato", "cili", "bayam"
        week_date: date of the week (defaults to current week Monday)

    Returns:
        {'commodity': str, 'price_per_kg': float, 'week_date': str} or None
    """
    if week_date is None:
        today = date.today()
        week_date = today - timedelta(days=today.weekday())  # Monday

    return await get_fama_price(commodity, week_date)


# Commodity name normalisation — handle Malay/English variants
COMMODITY_ALIASES = {
    "tomato": ["tomato", "tomat", "tomatoes"],
    "cili":   ["cili", "chili", "chilli", "cabai"],
    "bayam":  ["bayam", "spinach", "amaranth"],
    "kangkung": ["kangkung", "water spinach"],
    "kailan": ["kailan", "kai lan", "chinese broccoli"],
    "timun":  ["timun", "cucumber"],
    "kubis":  ["kubis", "cabbage"],
}

def normalise_commodity(name: str) -> str:
    """Normalise commodity name to canonical form."""
    name_lower = name.lower().strip()
    for canonical, aliases in COMMODITY_ALIASES.items():
        if name_lower in aliases or name_lower == canonical:
            return canonical
    return name_lower
