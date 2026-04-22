"""
db/seed.py — Seeds 30 days of realistic demo data.
Run once: python db/seed.py
Safe to run multiple times (checks if already seeded).
Owner: Person 2
"""
import asyncio
from datetime import date, timedelta
from db.models import init_db, AsyncSessionLocal, Supplier, SupplierPrice, Trade, Receivable, FamaBenchmark, Inventory
from sqlalchemy import select


SUPPLIERS = [
    {"name": "Pak Ali",    "phone": "012-3456789", "language": "malay",    "reliability": 8.5},
    {"name": "Ah Seng",    "phone": "016-8765432", "language": "mandarin", "reliability": 7.0},
    {"name": "Pak Rahman", "phone": "011-2345678", "language": "malay",    "reliability": 9.0},
    {"name": "Uncle Lim",  "phone": "017-5554321", "language": "mandarin", "reliability": 6.5},
]

FAMA_PRICES = [
    # (commodity, price_per_kg, weeks_ago)
    ("tomato",   2.75, 0), ("tomato",   2.80, 1), ("tomato",   2.65, 2), ("tomato",   2.70, 3),
    ("cili",     4.10, 0), ("cili",     3.90, 1), ("cili",     4.20, 2), ("cili",     4.00, 3),
    ("bayam",    1.80, 0), ("bayam",    1.75, 1), ("bayam",    1.90, 2), ("bayam",    1.85, 3),
    ("kangkung", 1.50, 0), ("kangkung", 1.45, 1), ("kangkung", 1.55, 2), ("kangkung", 1.50, 3),
    ("timun",    1.20, 0), ("timun",    1.15, 1), ("timun",    1.25, 2), ("timun",    1.20, 3),
]

SUPPLIER_PRICES_30D = [
    # (supplier_name, commodity, price, days_ago)
    ("Pak Ali",    "tomato",   2.60, 1),  ("Pak Ali",    "tomato",   2.55, 8),
    ("Ah Seng",    "tomato",   2.85, 2),  ("Ah Seng",    "tomato",   2.90, 9),
    ("Pak Rahman", "tomato",   2.90, 3),  ("Pak Rahman", "tomato",   2.80, 10),
    ("Pak Ali",    "cili",     4.00, 1),  ("Pak Ali",    "cili",     3.80, 8),
    ("Ah Seng",    "cili",     4.20, 2),  ("Uncle Lim",  "cili",     3.95, 5),
    ("Pak Ali",    "bayam",    1.70, 1),  ("Pak Rahman", "bayam",    1.65, 4),
    ("Ah Seng",    "kangkung", 1.40, 2),  ("Pak Ali",    "kangkung", 1.35, 6),
    ("Uncle Lim",  "timun",    1.10, 3),  ("Pak Rahman", "timun",    1.15, 7),
]

# 30 days of buy/sell trades
def generate_trades():
    trades = []
    today = date.today()
    # Buys (every 3-5 days per commodity)
    for days_ago, commodity, qty, price, supplier in [
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
    ]:
        trades.append(("buy", commodity, qty, price, supplier, today - timedelta(days=days_ago)))

    # Sells (daily, varying velocity)
    sell_data = [
        # commodity, avg_daily_kg, start_days_ago
        ("tomato",   400, 30),
        ("cili",      60, 30),
        ("bayam",     90, 30),   # slow mover — good for spoilage demo
        ("kangkung",  80, 30),
        ("timun",    100, 30),
    ]
    import random; random.seed(42)
    for commodity, avg, start in sell_data:
        for d in range(start, 0, -1):
            qty = random.uniform(avg * 0.7, avg * 1.3)
            price_map = {"tomato": 3.20, "cili": 5.50, "bayam": 2.80, "kangkung": 2.20, "timun": 1.80}
            trades.append(("sell", commodity, round(qty, 1), price_map[commodity], "various", today - timedelta(days=d)))
    return trades


RECEIVABLES = [
    # (buyer_name, commodity, amount_rm, days_ago_created, days_until_due)
    ("Kedai Pak Hamid",   "bayam",    1400, 5, -1),   # overdue by 1 day
    ("Restoran Maju",     "tomato",   2200, 3,  4),   # due in 4 days
    ("Kedai Uncle Wong",  "cili",      600, 1,  6),   # due in 6 days
]


async def seed_demo_data():
    await init_db()

    async with AsyncSessionLocal() as session:
        # Skip if already seeded
        result = await session.execute(select(Supplier).limit(1))
        if result.scalar_one_or_none():
            return

        today = date.today()

        # Suppliers
        supplier_map = {}
        for s in SUPPLIERS:
            obj = Supplier(**s)
            session.add(obj)
            await session.flush()
            supplier_map[s["name"]] = obj.id

        # FAMA benchmarks
        for commodity, price, weeks_ago in FAMA_PRICES:
            monday = today - timedelta(days=today.weekday()) - timedelta(weeks=weeks_ago)
            session.add(FamaBenchmark(commodity=commodity, price_per_kg=price, week_date=monday))

        # Supplier prices
        for name, commodity, price, days_ago in SUPPLIER_PRICES_30D:
            session.add(SupplierPrice(
                supplier_id=supplier_map[name],
                commodity=commodity,
                price_per_kg=price,
                quoted_date=today - timedelta(days=days_ago),
            ))

        # Trades
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
        for commodity, qty, cost, shelf_life in [
            ("tomato",   800,  2.60, 5),
            ("cili",     180,  4.00, 10),
            ("bayam",    920,  1.70, 3),   # ← high spoilage risk for demo
            ("kangkung", 240,  1.40, 4),
            ("timun",    350,  1.10, 6),
        ]:
            session.add(Inventory(
                commodity=commodity,
                quantity_kg=qty,
                entry_date=today - timedelta(days=7 - shelf_life),
                shelf_life_days=shelf_life,
                cost_per_kg=cost,
            ))

        # Receivables
        for buyer, commodity, amount, days_ago, days_until_due in RECEIVABLES:
            due = today + timedelta(days=days_until_due)
            session.add(Receivable(
                buyer_name=buyer,
                commodity=commodity,
                amount_rm=amount,
                due_date=due,
            ))

        await session.commit()
        print("✅ Demo data seeded successfully.")


if __name__ == "__main__":
    asyncio.run(seed_demo_data())
