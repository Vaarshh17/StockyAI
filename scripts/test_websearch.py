import asyncio
from services.websearch import search_market_news

async def main():
    tests = [
        # The exact scenario the user reported
        ("war vegetable prices increase Malaysia", "news"),
        # Flood disruption
        ("banjir Kelantan tomato supply", "news"),
        # Malay price query
        ("harga sayur naik Malaysia", "news"),
        # Festival - generic raya (should resolve to next upcoming raya)
        ("hari raya", "festival"),
        # Festival - specific
        ("raya haji", "festival"),
        # Festival - wesak (coming in 9 days)
        ("wesak", "festival"),
    ]
    for query, qtype in tests:
        print(f"\n{'='*60}")
        print(f"QUERY: {query!r}  type={qtype}")
        result = await search_market_news(query, qtype)
        print(f"Summary: {result['summary'][:120]}")
        for i, r in enumerate(result.get("results", [])[:3], 1):
            title = r['title'][:70]
            date_str = f"  [{r['date'][:10]}]" if r.get("date") else ""
            print(f"  [{i}]{date_str} {title}")

asyncio.run(main())
