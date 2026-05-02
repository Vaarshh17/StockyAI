"""
db/seed.py — Seeds 60 days of realistic demo data.
Run once: python db/seed.py
Safe to run multiple times (checks if already seeded).
Owner: Person 2
"""
import asyncio
from datetime import date, datetime, timedelta
from db.models import init_db, AsyncSessionLocal, Supplier, SupplierPrice, Trade, Receivable, FamaBenchmark, Inventory
from sqlalchemy import select


SUPPLIERS = [
    {"name": "Pak Ali",    "phone": "012-3456789", "language": "malay",    "reliability": 8.5},
    {"name": "Ah Seng",    "phone": "016-8765432", "language": "mandarin", "reliability": 7.0},
    {"name": "Pak Rahman", "phone": "011-2345678", "language": "malay",    "reliability": 9.0},
    {"name": "Uncle Lim",  "phone": "017-5554321", "language": "mandarin", "reliability": 6.5},
]

# 8 weeks of FAMA benchmarks to cover 60-day history
FAMA_PRICES = [
    ("tomato",   2.75, 0), ("tomato",   2.80, 1), ("tomato",   2.65, 2), ("tomato",   2.70, 3),
    ("tomato",   2.72, 4), ("tomato",   2.68, 5), ("tomato",   2.75, 6), ("tomato",   2.60, 7),
    ("cili",     4.10, 0), ("cili",     3.90, 1), ("cili",     4.20, 2), ("cili",     4.00, 3),
    ("cili",     4.15, 4), ("cili",     3.85, 5), ("cili",     4.05, 6), ("cili",     3.95, 7),
    ("bayam",    1.80, 0), ("bayam",    1.75, 1), ("bayam",    1.90, 2), ("bayam",    1.85, 3),
    ("bayam",    1.78, 4), ("bayam",    1.82, 5), ("bayam",    1.76, 6), ("bayam",    1.80, 7),
    ("kangkung", 1.50, 0), ("kangkung", 1.45, 1), ("kangkung", 1.55, 2), ("kangkung", 1.50, 3),
    ("kangkung", 1.48, 4), ("kangkung", 1.52, 5), ("kangkung", 1.44, 6), ("kangkung", 1.50, 7),
    ("timun",    1.20, 0), ("timun",    1.15, 1), ("timun",    1.25, 2), ("timun",    1.20, 3),
    ("timun",    1.18, 4), ("timun",    1.22, 5), ("timun",    1.16, 6), ("timun",    1.20, 7),
]

SUPPLIER_PRICES_60D = [
    # recent 30 days
    ("Pak Ali",    "tomato",   2.60, 1),  ("Pak Ali",    "tomato",   2.55, 8),
    ("Ah Seng",    "tomato",   2.85, 2),  ("Ah Seng",    "tomato",   2.90, 9),
    ("Pak Rahman", "tomato",   2.90, 3),  ("Pak Rahman", "tomato",   2.80, 10),
    ("Pak Ali",    "cili",     4.00, 1),  ("Pak Ali",    "cili",     3.80, 8),
    ("Ah Seng",    "cili",     4.20, 2),  ("Uncle Lim",  "cili",     3.95, 5),
    ("Pak Ali",    "bayam",    1.70, 1),  ("Pak Rahman", "bayam",    1.65, 4),
    ("Ah Seng",    "kangkung", 1.40, 2),  ("Pak Ali",    "kangkung", 1.35, 6),
    ("Uncle Lim",  "timun",    1.10, 3),  ("Pak Rahman", "timun",    1.15, 7),
    # older 30-60 days
    ("Pak Ali",    "tomato",   2.58, 35), ("Pak Rahman", "tomato",   2.72, 42),
    ("Uncle Lim",  "cili",     3.90, 38), ("Pak Ali",    "cili",     3.85, 50),
    ("Pak Rahman", "bayam",    1.68, 40), ("Ah Seng",    "bayam",    1.72, 55),
    ("Pak Ali",    "kangkung", 1.38, 45), ("Uncle Lim",  "timun",    1.12, 48),
]


def generate_trades():
    trades = []
    today = date.today()

    # Buy trades — covering full 60-day window
    for days_ago, commodity, qty, price, supplier in [
        # recent buys (days 1–12)
        (1,  "tomato",   3000, 2.60, "Pak Ali"),
        (6,  "tomato",   2500, 2.55, "Pak Ali"),
        (12, "tomato",   3500, 2.80, "Pak Rahman"),
        (2,  "cili",      500, 4.00, "Pak Ali"),
        (9,  "cili",      400, 3.80, "Uncle Lim"),
        (3,  "bayam",     800, 1.70, "Pak Ali"),
        (8,  "bayam",    1000, 1.65, "Pak Rahman"),
        (4,  "kangkung",  600, 1.40, "Ah Seng"),
        (11, "kangkung",  700, 1.35, "Pak Ali"),
        (5,  "timun",     900, 1.10, "Uncle Lim"),
        # older buys (days 30–60) — give the finance engine historical depth
        (32, "tomato",   3200, 2.58, "Pak Ali"),
        (40, "tomato",   2800, 2.72, "Pak Rahman"),
        (35, "cili",      450, 3.90, "Uncle Lim"),
        (50, "cili",      500, 3.85, "Pak Ali"),
        (38, "bayam",     900, 1.68, "Pak Rahman"),
        (55, "bayam",    1100, 1.72, "Ah Seng"),
        (42, "kangkung",  650, 1.38, "Pak Ali"),
        (48, "timun",     850, 1.12, "Uncle Lim"),
        (58, "tomato",   3000, 2.60, "Pak Ali"),
        (60, "kangkung",  600, 1.40, "Ah Seng"),
    ]:
        trades.append(("buy", commodity, qty, price, supplier, today - timedelta(days=days_ago)))

    # Sell trades — 60 days of daily sells
    sell_data = [
        # commodity, avg_daily_kg, start_days_ago
        ("tomato",   400, 60),
        ("cili",      60, 60),
        ("bayam",     90, 60),   # slow mover — good for spoilage demo
        ("kangkung",  80, 60),
        ("timun",    100, 60),
    ]
    import random; random.seed(42)
    for commodity, avg, start in sell_data:
        for d in range(start, 0, -1):
            qty = random.uniform(avg * 0.7, avg * 1.3)
            price_map = {"tomato": 3.20, "cili": 5.50, "bayam": 2.80, "kangkung": 2.20, "timun": 1.80}
            trades.append(("sell", commodity, round(qty, 1), price_map[commodity], "various", today - timedelta(days=d)))
    return trades


# Historical receivables — PAID on time (builds a healthy collection rate)
# Format: (buyer_name, commodity, amount_rm, days_ago_created, days_until_due_from_creation, days_ago_paid)
PAID_RECEIVABLES = [
    ("Kedai Pak Hamid",   "tomato",   1800, 55, 7,  48),
    ("Restoran Maju",     "cili",      900, 48, 7,  42),
    ("Kedai Uncle Wong",  "bayam",     600, 40, 7,  34),
    ("Kedai Pak Hamid",   "kangkung",  480, 32, 7,  26),
    ("Restoran Maju",     "timun",    1200, 25, 7,  19),
    ("Syarikat Borong KL","tomato",   2400, 18, 7,  13),
]

# Current open receivables (not yet paid)
OPEN_RECEIVABLES = [
    # (buyer_name, commodity, amount_rm, days_ago_created, days_until_due)
    ("Kedai Pak Hamid",   "bayam",    1400, 5, -1),   # overdue by 1 day
    ("Restoran Maju",     "tomato",   2200, 3,  4),   # due in 4 days
    ("Kedai Uncle Wong",  "cili",      600, 1,  6),   # due in 6 days
]


async def seed_demo_data(force: bool = False):
    await init_db()

    async with AsyncSessionLocal() as session:
        # Skip if already seeded (unless force=True)
        result = await session.execute(select(Supplier).limit(1))
        if result.scalar_one_or_none():
            if not force:
                print("⏭  Seed skipped — data already present. Run with --force to reset.")
                return
            # Truncate all demo tables
            from sqlalchemy import text
            for table in ("inventory", "trades", "receivables", "supplier_prices",
                          "fama_benchmarks", "suppliers", "loan_offers"):
                await session.execute(text(f"DELETE FROM {table}"))
            await session.commit()
            print("🗑  Existing data cleared.")

        today = date.today()

        # Suppliers
        supplier_map = {}
        for s in SUPPLIERS:
            obj = Supplier(**s)
            session.add(obj)
            await session.flush()
            supplier_map[s["name"]] = obj.id

        # FAMA benchmarks (8 weeks)
        for commodity, price, weeks_ago in FAMA_PRICES:
            monday = today - timedelta(days=today.weekday()) - timedelta(weeks=weeks_ago)
            session.add(FamaBenchmark(commodity=commodity, price_per_kg=price, week_date=monday))

        # Supplier prices
        for name, commodity, price, days_ago in SUPPLIER_PRICES_60D:
            session.add(SupplierPrice(
                supplier_id=supplier_map[name],
                commodity=commodity,
                price_per_kg=price,
                quoted_date=today - timedelta(days=days_ago),
            ))

        # Trades (60 days)
        for trade_type, commodity, qty, price, counterparty, trade_date in generate_trades():
            session.add(Trade(
                trade_type=trade_type,
                commodity=commodity,
                quantity_kg=qty,
                price_per_kg=price,
                counterparty=counterparty,
                trade_date=trade_date,
            ))

        # Current inventory (what's left today)
        # entry_date formula: simulate a batch that has `shelf_life - days_elapsed` days left
        # max(0, ...) prevents future entry dates for long-shelf items (e.g. cili)
        for commodity, qty, cost, shelf_life, days_elapsed in [
            ("tomato",   800,  2.60, 5, 2),   # 3 days left — stockout in 2 days via velocity
            ("cili",     180,  4.00, 7, 0),   # 7 days left — stockout in 3 days via velocity
            ("bayam",    920,  1.70, 4, 3),   # 1 day left  — ⚠️ expires tomorrow, high spoilage risk
            ("kangkung", 240,  1.40, 4, 3),   # 1 day left  — ⚠️ expires tomorrow
            ("timun",    350,  1.10, 6, 1),   # 5 days left — OK
        ]:
            session.add(Inventory(
                commodity=commodity,
                quantity_kg=qty,
                entry_date=today - timedelta(days=days_elapsed),
                shelf_life_days=shelf_life,
                cost_per_kg=cost,
            ))

        # Paid historical receivables — establishes healthy collection rate
        for buyer, commodity, amount, days_ago_created, days_until_due, days_ago_paid in PAID_RECEIVABLES:
            created = today - timedelta(days=days_ago_created)
            due = created + timedelta(days=days_until_due)
            paid_date = today - timedelta(days=days_ago_paid)
            session.add(Receivable(
                buyer_name=buyer,
                commodity=commodity,
                amount_rm=amount,
                due_date=due,
                paid=True,
                paid_date=paid_date,
                created_at=datetime.combine(created, datetime.min.time()),
            ))

        # Open receivables (current outstanding)
        for buyer, commodity, amount, days_ago, days_until_due in OPEN_RECEIVABLES:
            due = today + timedelta(days=days_until_due)
            created = today - timedelta(days=days_ago)
            session.add(Receivable(
                buyer_name=buyer,
                commodity=commodity,
                amount_rm=amount,
                due_date=due,
                created_at=datetime.combine(created, datetime.min.time()),
            ))

        await session.commit()
        print("✅ Demo data seeded successfully (60 days).")


if __name__ == "__main__":
    import sys
    force = "--force" in sys.argv
    asyncio.run(seed_demo_data(force=force))
