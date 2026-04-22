"""
agent/instinct.py — Stocky's Instinct Layer

Analyzes 14 days of business data across multiple signals and
surfaces ONE non-obvious pattern the user probably hasn't noticed.

This is what makes Stocky AI feel alive — it speaks up before being asked.
Owner: Person 1
"""
import logging
from datetime import date, timedelta

logger = logging.getLogger(__name__)

INSTINCT_SYSTEM_PROMPT = """
Kamu adalah Stocky AI, pembantu perniagaan untuk peniaga borong Malaysia.
Tugas kamu sekarang: analisa data perniagaan 14 hari ini dan CARI SATU corak yang tidak jelas.

Cari merentasi isyarat-isyarat ini:
- Trend kelajuan jualan (ada barang yang jual laju/lambat tanpa sebab jelas?)
- Kitaran harga pembekal (ada pembekal naikkan harga mengikut corak?)
- Penumpukan kredit (ada pembeli yang hutang makin banyak?)
- Masa inventori (peniaga selalu over-stok atau under-stok barang tertentu?)
- Isyarat merentasi komoditi (bila X jual laju, Y selalu turun?)

PERATURAN:
1. Pilih SATU penemuan paling bermakna sahaja
2. Mulakan dengan: "Stocky nampak sesuatu:"
3. Sebut nama komoditi, pembekal, atau pembeli yang spesifik
4. 2-3 ayat sahaja, bahasa Melayu yang natural
5. Jika tiada corak signifikan: tulis "Stocky nampak semua ok minggu ni. Teruskan\!"
6. Jangan teka — hanya bercakap berdasarkan data yang ada
"""

INSTINCT_USER_TEMPLATE = """
Ini data perniagaan terkini:

INVENTORI SEMASA:
{inventory}

KELAJUAN JUALAN (7 hari):
{velocities}

RINGKASAN MINGGUAN:
{digest}

KREDIT TERTUNGGAK:
{credit}

TREND HARGA PEMBEKAL (14 hari):
{price_trends}

Apa yang Stocky nampak?
"""


async def get_instinct() -> str:
    """
    Run Stocky's Instinct analysis.

    Called by:
    - morning_brief_job() in scheduler/jobs.py
    - run_proactive_brief("digest") in agent/core.py

    Returns:
        A string starting with "Stocky nampak sesuatu:" or "Stocky nampak semua ok."
    """
    try:
        from db.queries import (
            db_get_inventory, db_get_velocity,
            db_get_weekly_digest, db_get_credit,
            db_get_price_trend,
        )
        from services.glm import call_glm

        # Gather all signal streams
        inventory = await db_get_inventory()
        digest    = await db_get_weekly_digest()
        credit    = await db_get_credit()

        # Velocity for each commodity in stock
        velocities = []
        for item in inventory:
            v = await db_get_velocity(item["commodity"])
            velocities.append(v)

        # Price trend over last 14 days per commodity
        commodities = list({item["commodity"] for item in inventory})
        price_trends = []
        for c in commodities:
            trend = await db_get_price_trend(c, days=14)
            if trend:
                price_trends.append(trend)

        # Format context for GLM
        context = INSTINCT_USER_TEMPLATE.format(
            inventory=_fmt(inventory),
            velocities=_fmt(velocities),
            digest=_fmt(digest),
            credit=_fmt(credit),
            price_trends=_fmt(price_trends),
        )

        messages = [
            {"role": "system", "content": INSTINCT_SYSTEM_PROMPT},
            {"role": "user",   "content": context},
        ]

        response = await call_glm(messages, tools=None)
        result = response.get("content", "").strip()

        if not result:
            return "Stocky nampak semua ok minggu ni. Teruskan\!"

        # Ensure it starts with the right prefix
        if not result.startswith("Stocky"):
            result = "Stocky nampak sesuatu: " + result

        return result

    except Exception as e:
        logger.error(f"Instinct analysis failed: {e}")
        return ""   # Silent fail — instinct is additive, not critical


def _fmt(data) -> str:
    """Pretty-format data for GLM context."""
    if isinstance(data, list):
        if not data:
            return "Tiada data"
        return "\n".join(f"  - {item}" for item in data)
    if isinstance(data, dict):
        return "\n".join(f"  {k}: {v}" for k, v in data.items())
    return str(data)
