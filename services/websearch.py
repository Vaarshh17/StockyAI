"""
services/websearch.py — Market news + Malaysian festival date lookup.

Two modes:
  query_type="festival" → hardcoded 2026 Malaysian public holidays (instant, no network)
  query_type="news"     → ddgs library (real web + news results, no API key needed)

News strategy:
  1. News search (date-stamped recent articles) with Malaysia-scoped query
  2. Fall back to text search if news is sparse
  3. Fall back to unscoped raw query if still empty
  Always returns a useful response — never a dead end.
"""
import logging
from datetime import date

logger = logging.getLogger(__name__)

DASHBOARD_URL = "https://stocky-ai-dashboard.lovable.app/"

# Malaysian public holidays 2026 — hardcoded so festival queries never need a network call
_FESTIVALS_2026: list[dict] = [
    {"name": "Thaipusam",                 "date": date(2026, 1, 28),  "keywords": ["thaipusam"]},
    {"name": "Tahun Baru Cina / CNY",     "date": date(2026, 2, 17),  "keywords": ["cny", "chinese new year", "tahun baru cina", "gong xi", "imlek"]},
    {"name": "Hari Raya Aidilfitri",      "date": date(2026, 3, 31),  "keywords": ["aidilfitri", "raya puasa", "lebaran", "hari raya aidilfitri"]},
    {"name": "Wesak Day",                 "date": date(2026, 5, 11),  "keywords": ["wesak", "waisak"]},
    {"name": "Hari Raya Aidiladha",       "date": date(2026, 6, 7),   "keywords": ["aidiladha", "raya haji", "korban", "qurban"]},
    {"name": "Hari Kebangsaan",           "date": date(2026, 8, 31),  "keywords": ["merdeka", "hari kebangsaan", "national day"]},
    {"name": "Hari Malaysia",             "date": date(2026, 9, 16),  "keywords": ["hari malaysia", "malaysia day"]},
    {"name": "Deepavali",                 "date": date(2026, 10, 26), "keywords": ["deepavali", "diwali", "divali"]},
    {"name": "Hari Raya Aidilfitri 2027", "date": date(2027, 3, 20),  "keywords": []},
]

# Generic "raya" fallback — matched only if nothing else matches
_RAYA_GENERIC_KEYWORDS = ["hari raya", "raya"]

_DEMAND_PROFILE: dict[str, dict] = {
    "Hari Raya Aidilfitri": {
        "high_demand": ["tomato", "cili", "bayam", "kangkung", "timun"],
        "note": "Semua sayur dan buah meningkat permintaan — stok 2 minggu sebelum raya",
        "lead_days": 14,
    },
    "Tahun Baru Cina / CNY": {
        "high_demand": ["tomato", "cili", "timun"],
        "note": "Permintaan tinggi untuk sayur segar — peniaga Cina beli lebih awal",
        "lead_days": 10,
    },
    "Hari Raya Aidiladha": {
        "high_demand": ["tomato", "cili", "timun"],
        "note": "Permintaan sederhana — lebih rendah dari Aidilfitri",
        "lead_days": 7,
    },
    "Deepavali": {
        "high_demand": ["tomato", "cili"],
        "note": "Permintaan tinggi dari restoran India — cili merah dan tomato terutama",
        "lead_days": 7,
    },
    "Wesak Day": {
        "high_demand": ["bayam", "timun", "kangkung"],
        "note": "Permintaan sayur meningkat dari komuniti Buddhist — sayur hijau terutama",
        "lead_days": 5,
    },
}


async def search_market_news(query: str, query_type: str = "news") -> dict:
    if query_type == "festival":
        return _get_festival_info(query)
    return await _search_commodity_news(query)


def _get_festival_info(query: str) -> dict:
    """Return festival date, days away, and demand impact. Zero network calls."""
    q = query.lower()
    today = date.today()

    # Match specific keywords first (longer/more specific wins)
    matched = None
    best_kw_len = 0
    for festival in _FESTIVALS_2026:
        for kw in festival["keywords"]:
            if kw in q and len(kw) > best_kw_len:
                matched = festival
                best_kw_len = len(kw)

    # Generic "raya" fallback — pick next upcoming raya-type festival
    if not matched:
        for kw in _RAYA_GENERIC_KEYWORDS:
            if kw in q:
                raya_festivals = [
                    f for f in _FESTIVALS_2026
                    if "raya" in f["name"].lower() or "hari raya" in f["name"].lower()
                ]
                upcoming_raya = [f for f in raya_festivals if f["date"] >= today]
                if upcoming_raya:
                    matched = min(upcoming_raya, key=lambda f: f["date"])
                elif raya_festivals:
                    matched = max(raya_festivals, key=lambda f: f["date"])
                break

    # Last resort: next upcoming festival
    if not matched:
        upcoming = [f for f in _FESTIVALS_2026 if f["date"] >= today]
        matched = min(upcoming, key=lambda f: f["date"]) if upcoming else None

    if not matched:
        return {
            "results": [],
            "festival_info": None,
            "summary": "Tiada maklumat festival dijumpai.",
        }

    days_away = (matched["date"] - today).days
    profile = _DEMAND_PROFILE.get(matched["name"], {})
    high_demand = profile.get("high_demand", [])
    note = profile.get("note", "Permintaan mungkin meningkat menjelang tarikh ini.")
    lead = profile.get("lead_days", 7)

    if days_away < 0:
        timing = f"sudah berlalu {abs(days_away)} hari lepas"
        action = ""
    elif days_away == 0:
        timing = "HARI INI"
        action = "Pasar pasti sesak — jual pada harga penuh hari ini."
    elif days_away <= lead:
        timing = f"dalam {days_away} hari"
        action = "Masa untuk restock sekarang — permintaan akan naik."
    else:
        timing = f"dalam {days_away} hari"
        action = f"Masih ada masa. Mulai restock {lead} hari sebelum tarikh."

    summary = (
        f"{matched['name']} {timing} ({matched['date'].strftime('%d %b %Y')}). "
        f"{note} {action}"
    )
    return {
        "results": [{"title": matched["name"], "snippet": summary, "url": "", "date": ""}],
        "festival_info": {
            "name": matched["name"],
            "date": matched["date"].isoformat(),
            "days_away": days_away,
            "high_demand_commodities": high_demand,
            "demand_note": note,
            "action": action,
        },
        "summary": summary,
    }


def _build_queries(query: str) -> list[str]:
    """
    Build a prioritised list of query variants to try.
    More specific → broader, Malay → English fallback.
    """
    q = query.strip()
    malaysia_present = "malaysia" in q.lower() or "malaysia" in q.lower()

    queries = []

    # 1. Scoped with Malaysia produce context
    if not malaysia_present:
        queries.append(f"{q} Malaysia harga sayur buah")
    else:
        queries.append(q)

    # 2. Core query + Malaysia only
    if not malaysia_present:
        queries.append(f"{q} Malaysia")

    # 3. Raw query (broadest fallback)
    queries.append(q)

    # Remove duplicates while preserving order
    seen = set()
    unique = []
    for item in queries:
        if item not in seen:
            seen.add(item)
            unique.append(item)
    return unique


def _ddg_news(query: str, max_results: int = 5) -> list[dict]:
    """News search — returns date-stamped recent articles."""
    from ddgs import DDGS
    results = []
    with DDGS() as d:
        for r in d.news(query, max_results=max_results):
            results.append({
                "title":   r.get("title", ""),
                "snippet": r.get("body", r.get("excerpt", ""))[:400],
                "url":     r.get("url", ""),
                "date":    r.get("date", ""),
            })
    return results


def _ddg_text(query: str, max_results: int = 5) -> list[dict]:
    """Text/web search — broader, includes older pages."""
    from ddgs import DDGS
    results = []
    with DDGS() as d:
        for r in d.text(query, max_results=max_results):
            results.append({
                "title":   r.get("title", ""),
                "snippet": r.get("body", "")[:400],
                "url":     r.get("href", ""),
                "date":    "",
            })
    return results


def _run_search_sync(queries: list[str], max_results: int = 5) -> list[dict]:
    """
    Try news search across query variants, then supplement with text search.
    Runs synchronously — called via run_in_executor.
    """
    results = []
    seen_urls = set()

    def add(items: list[dict]):
        for r in items:
            key = r.get("url") or r.get("title", "")
            if key and key not in seen_urls:
                seen_urls.add(key)
                results.append(r)

    # News search — try each query variant until we get at least 2 results
    for q in queries:
        if len(results) >= 2:
            break
        try:
            add(_ddg_news(q, max_results))
        except Exception as e:
            logger.debug(f"News search failed for {q!r}: {e}")

    # Text search — supplement if still sparse
    if len(results) < 3:
        for q in queries[:2]:  # only try top 2 variants
            if len(results) >= max_results:
                break
            try:
                add(_ddg_text(q, max_results))
            except Exception as e:
                logger.debug(f"Text search failed for {q!r}: {e}")

    return results[:max_results]


async def _search_commodity_news(query: str) -> dict:
    """
    Real web search via ddgs. Tries multiple query variants.
    Runs search in a thread executor to not block the async event loop.
    """
    import asyncio

    queries = _build_queries(query)
    loop = asyncio.get_event_loop()

    try:
        results = await asyncio.wait_for(
            loop.run_in_executor(None, _run_search_sync, queries, 5),
            timeout=15.0,
        )
    except asyncio.TimeoutError:
        logger.warning(f"DDG search timed out for: {query}")
        results = []
    except Exception as e:
        logger.error(f"DDG search error: {e}")
        results = []

    if results:
        titles = " | ".join(r["title"][:60] for r in results[:2] if r["title"])
        summary = f"Dijumpai {len(results)} artikel berkaitan '{query}'. Tajuk: {titles}."
    else:
        summary = (
            f"Tiada berita terkini dijumpai untuk '{query}'. "
            "Ini mungkin bermakna tiada gangguan bekalan besar dilaporkan buat masa ini. "
            "Cadangan: pantau harga FAMA minggu depan dan semak terus dengan pembekal anda."
        )

    return {
        "results":       results,
        "festival_info": None,
        "summary":       summary,
    }
