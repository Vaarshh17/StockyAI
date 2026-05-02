"""
scripts/test_fama_live.py — FAMA benchmark price inspector.

Shows current FAMA benchmark prices stored in the DB.
Live scraping was removed (FAMA API is unstable); prices are seeded weekly.

Run from project root:
    python scripts/test_fama_live.py
    python scripts/test_fama_live.py --commodity tomato
"""
import asyncio
import argparse
import sys
import os
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def show_benchmarks(commodity: str = None):
    from db.models import init_db
    from db.queries import get_fama_price, db_get_all_user_ids
    from db.models import AsyncSessionLocal, FamaBenchmark
    from sqlalchemy import select

    await init_db()

    async with AsyncSessionLocal() as session:
        q = select(FamaBenchmark).order_by(FamaBenchmark.commodity, FamaBenchmark.week_date.desc())
        if commodity:
            q = q.where(FamaBenchmark.commodity == commodity.lower())
        result = await session.execute(q)
        rows = result.scalars().all()

    if not rows:
        print("No FAMA benchmark data found. Run seed_demo_data() first.")
        return

    print(f"\n{'='*55}")
    print(f"  FAMA Benchmark Prices (seeded)")
    print(f"  As of: {date.today()}")
    print(f"{'='*55}")
    print(f"  {'Commodity':<15} {'Week':<14} {'Price/kg':>10}")
    print(f"  {'-'*15} {'-'*14} {'-'*10}")

    seen = set()
    for r in rows:
        key = (r.commodity, r.week_date)
        if key in seen:
            continue
        seen.add(key)
        print(f"  {r.commodity:<15} {str(r.week_date):<14} RM{r.price_per_kg:>7.2f}")

    print(f"\nTotal records: {len(rows)}")


def main():
    parser = argparse.ArgumentParser(description="Inspect FAMA benchmark prices in DB")
    parser.add_argument("--commodity", "-c", help="Filter by commodity (e.g. tomato)", default=None)
    args = parser.parse_args()
    asyncio.run(show_benchmarks(args.commodity))


if __name__ == "__main__":
    main()
