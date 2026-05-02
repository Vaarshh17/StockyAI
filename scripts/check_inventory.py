import asyncio
from db.queries import db_get_inventory, db_get_velocity

async def main():
    items = await db_get_inventory()
    print("=== INVENTORY ===")
    for i in items:
        print(f"  {i['commodity']:12} {i['quantity_kg']:6}kg  shelf={i['shelf_life_days']}d  days_remaining={i['days_remaining']}")

    print("\n=== VELOCITY (7d) ===")
    for commodity in ["tomato", "cili", "bayam", "kangkung", "timun"]:
        v = await db_get_velocity(commodity, days=7)
        v14 = await db_get_velocity(commodity, days=14)
        print(f"  {commodity:12}  7d={v['avg_daily_kg']}kg/day  14d={v14['avg_daily_kg']}kg/day")

asyncio.run(main())
