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

INSTINCT_SYSTEM_PROMPTS = {
    "Malay": """
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
5. Jika tiada corak signifikan: tulis "Stocky nampak semua ok minggu ni. Teruskan!"
6. Jangan teka — hanya bercakap berdasarkan data yang ada
""",
    "English": """
You are Stocky AI, a business intelligence partner for Malaysian produce wholesalers.
Your task: analyse the last 14 days of business data and surface ONE non-obvious pattern.

Look across these signals:
- Sales velocity trends (anything selling unusually fast or slow?)
- Supplier price cycles (any supplier raising prices in a pattern?)
- Credit accumulation (any buyer whose debt keeps growing?)
- Inventory timing (consistently over- or under-stocked on any commodity?)
- Cross-commodity signals (when X sells fast, does Y always slow down?)

RULES:
1. Pick ONE most meaningful finding only
2. Start with: "Stocky sees something:"
3. Name the specific commodity, supplier, or buyer
4. 2-3 sentences max, plain conversational English
5. If no significant pattern: write "Stocky sees everything looking normal this week. Keep it up!"
6. Do not guess — only speak from the data provided
""",
    "中文": """
你是Stocky AI，马来西亚批发商的商业智能助手。
你的任务：分析过去14天的业务数据，找出一个不明显的规律。

关注以下信号：
- 销售速度趋势（有没有哪种商品异常快或慢？）
- 供应商价格周期（有没有供应商按规律涨价？）
- 信用积累（有没有买家欠款越来越多？）
- 库存时机（某种商品是否总是过多或不足？）
- 跨商品信号（X卖得快时，Y是否总会下降？）

规则：
1. 只选一个最有意义的发现
2. 以"Stocky发现了什么："开头
3. 具体说明是哪种商品、供应商或买家
4. 最多2-3句话，自然口语化中文
5. 如果没有明显规律：写"Stocky看本周一切正常，继续保持！"
6. 不要猜测——只根据提供的数据发言
""",
}

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


async def get_instinct(language: str = "Malay") -> str:
    """
    Run Stocky's Instinct analysis via ILMU API (Z.ai / ilmu-glm-5.1).

    Called by:
    - run_proactive_brief("morning") in agent/core.py
    - run_proactive_brief("digest") in agent/core.py

    Args:
        language: User's preferred language ("Malay", "English", "中文")

    Returns:
        A string starting with "Stocky nampak sesuatu:" / "Stocky sees something:" etc.
    """
    try:
        from db.queries import (
            db_get_inventory, db_get_velocity,
            db_get_weekly_digest, db_get_credit,
            db_get_price_trend,
        )
        from services.glm import call_llm  # ← correct function name

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

        system_prompt = INSTINCT_SYSTEM_PROMPTS.get(language, INSTINCT_SYSTEM_PROMPTS["Malay"])
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": context},
        ]

        response = await call_llm(messages, tools=None)   # ← call_llm, not call_glm
        result = response.get("content", "").strip()

        if not result:
            fallbacks = {
                "English": "Stocky sees everything looking normal this week. Keep it up!",
                "中文":    "Stocky看本周一切正常，继续保持！",
            }
            return fallbacks.get(language, "Stocky nampak semua ok minggu ni. Teruskan!")

        # Ensure it starts with the right prefix
        if not result.startswith("Stocky"):
            prefix = {
                "English": "Stocky sees something: ",
                "中文":    "Stocky发现了什么：",
            }.get(language, "Stocky nampak sesuatu: ")
            result = prefix + result

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
