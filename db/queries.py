"""
db/queries.py — All database query functions.
One function per tool. Returns plain dicts (not ORM objects) for easy JSON serialisation.
Owner: Person 2
"""
from datetime import date, datetime, timedelta
from sqlalchemy import select, func, and_
from db.models import AsyncSessionLocal, Inventory, Supplier, SupplierPrice, Trade, Receivable, FamaBenchmark


# ─── INVENTORY ────────────────────────────────────────────────────────────────

async def db_get_inventory(commodity: str = None) -> list[dict]:
    async with AsyncSessionLocal() as session:
        q = select(Inventory)
        if commodity:
            q = q.where(Inventory.commodity == commodity.lower())
        result = await session.execute(q)
        rows = result.scalars().all()
        today = date.today()
        return [
            {
                "commodity": r.commodity,
                "quantity_kg": r.quantity_kg,
                "entry_date": str(r.entry_date),
                "shelf_life_days": r.shelf_life_days,
                "days_remaining": r.shelf_life_days - (today - r.entry_date).days,
                "cost_per_kg": r.cost_per_kg,
            }
            for r in rows if r.quantity_kg > 0
        ]


async def db_update_inventory(
    commodity: str,
    quantity_kg: float,
    price_per_kg: float = None,
    supplier_name: str = None,
    shelf_life_days: int = 7,
) -> dict:
    async with AsyncSessionLocal() as session:
        # Find or create supplier
        supplier_id = None
        if supplier_name:
            result = await session.execute(
                select(Supplier).where(Supplier.name == supplier_name)
            )
            supplier = result.scalar_one_or_none()
            if not supplier:
                supplier = Supplier(name=supplier_name)
                session.add(supplier)
                await session.flush()
            supplier_id = supplier.id

            # Log the price quote
            if price_per_kg:
                session.add(SupplierPrice(
                    supplier_id=supplier_id,
                    commodity=commodity.lower(),
                    price_per_kg=price_per_kg,
                    quantity_kg=quantity_kg,
                    quoted_date=date.today(),
                ))

        # Add inventory entry
        item = Inventory(
            commodity=commodity.lower(),
            quantity_kg=quantity_kg,
            entry_date=date.today(),
            shelf_life_days=shelf_life_days,
            cost_per_kg=price_per_kg,
            supplier_id=supplier_id,
        )
        session.add(item)

        # Log as a buy trade
        session.add(Trade(
            trade_type="buy",
            commodity=commodity.lower(),
            quantity_kg=quantity_kg,
            price_per_kg=price_per_kg or 0,
            counterparty=supplier_name,
            trade_date=date.today(),
        ))

        await session.commit()

    # Return updated totals
    updated = await db_get_inventory(commodity)
    total = sum(r["quantity_kg"] for r in updated)
    return {"status": "updated", "commodity": commodity, "added_kg": quantity_kg, "total_stock_kg": total}


async def db_log_sell(
    commodity: str,
    quantity_kg: float,
    price_per_kg: float = None,
    buyer_name: str = None,
) -> dict:
    """
    Record a sell transaction and deduct stock using FIFO (oldest batch first).
    """
    async with AsyncSessionLocal() as session:
        # Log the sell trade
        session.add(Trade(
            trade_type="sell",
            commodity=commodity.lower(),
            quantity_kg=quantity_kg,
            price_per_kg=price_per_kg or 0,
            counterparty=buyer_name,
            trade_date=date.today(),
        ))

        # FIFO inventory deduction — oldest entries first
        result = await session.execute(
            select(Inventory)
            .where(and_(
                Inventory.commodity == commodity.lower(),
                Inventory.quantity_kg > 0,
            ))
            .order_by(Inventory.entry_date)
        )
        batches = result.scalars().all()

        remaining = quantity_kg
        for batch in batches:
            if remaining <= 0:
                break
            deduct = min(batch.quantity_kg, remaining)
            batch.quantity_kg -= deduct
            remaining -= deduct

        await session.commit()

    updated = await db_get_inventory(commodity)
    total_left = sum(r["quantity_kg"] for r in updated)
    revenue = round(quantity_kg * (price_per_kg or 0), 2)
    return {
        "status": "logged",
        "commodity": commodity,
        "sold_kg": quantity_kg,
        "price_per_kg": price_per_kg,
        "revenue_rm": revenue,
        "remaining_stock_kg": total_left,
    }


async def db_get_velocity(commodity: str, days: int = 7) -> dict:
    """Calculate average daily sell rate for a commodity over N days."""
    since = date.today() - timedelta(days=days)
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(func.sum(Trade.quantity_kg))
            .where(and_(
                Trade.commodity == commodity.lower(),
                Trade.trade_type == "sell",
                Trade.trade_date >= since,
            ))
        )
        total_sold = result.scalar() or 0
    return {
        "commodity": commodity,
        "total_sold_kg": total_sold,
        "avg_daily_kg": round(total_sold / days, 1),
        "period_days": days,
    }


# ─── SUPPLIER PRICES ──────────────────────────────────────────────────────────

async def db_compare_prices(commodity: str, quantity_needed_kg: float = None) -> dict:
    since = date.today() - timedelta(days=14)  # last 2 weeks
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Supplier.name, Supplier.language, SupplierPrice.price_per_kg, SupplierPrice.quoted_date)
            .join(Supplier, SupplierPrice.supplier_id == Supplier.id)
            .where(and_(
                SupplierPrice.commodity == commodity.lower(),
                SupplierPrice.quoted_date >= since,
            ))
            .order_by(SupplierPrice.price_per_kg)
        )
        rows = result.all()

    fama = await get_fama_price(commodity)
    fama_price = fama["price_per_kg"] if fama else None

    suppliers = [
        {
            "name": r[0],
            "language": r[1],
            "price_per_kg": r[2],
            "quoted_date": str(r[3]),
            "vs_fama_pct": round((r[2] - fama_price) / fama_price * 100, 1) if fama_price else None,
        }
        for r in rows
    ]
    return {
        "commodity": commodity,
        "suppliers": suppliers,
        "fama_benchmark": fama_price,
        "cheapest": suppliers[0] if suppliers else None,
    }


# ─── CREDIT / RECEIVABLES ─────────────────────────────────────────────────────

async def db_get_credit(buyer_name: str = None) -> list[dict]:
    async with AsyncSessionLocal() as session:
        q = select(Receivable).where(Receivable.paid == False)
        if buyer_name:
            q = q.where(Receivable.buyer_name == buyer_name)
        result = await session.execute(q)
        rows = result.scalars().all()
        today = date.today()
        return [
            {
                "buyer_name": r.buyer_name,
                "commodity": r.commodity,
                "amount_rm": r.amount_rm,
                "due_date": str(r.due_date) if r.due_date else None,
                "days_overdue": (today - r.due_date).days if r.due_date and r.due_date < today else 0,
                "due_today": r.due_date == today if r.due_date else False,
            }
            for r in rows
        ]


async def db_log_credit(buyer_name: str, amount_rm: float, commodity: str = None, due_date: str = None) -> dict:
    due = date.fromisoformat(due_date) if due_date else date.today() + timedelta(days=7)
    async with AsyncSessionLocal() as session:
        rec = Receivable(
            buyer_name=buyer_name,
            commodity=commodity,
            amount_rm=amount_rm,
            due_date=due,
        )
        session.add(rec)
        await session.commit()

    all_credit = await db_get_credit(buyer_name)
    total = sum(r["amount_rm"] for r in all_credit)
    return {"status": "logged", "buyer_name": buyer_name, "amount_rm": amount_rm, "due_date": str(due), "total_outstanding": total}


# ─── FAMA BENCHMARKS ─────────────────────────────────────────────────────────

async def get_fama_price(commodity: str, week_date: date = None) -> dict | None:
    if week_date is None:
        today = date.today()
        week_date = today - timedelta(days=today.weekday())
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(FamaBenchmark)
            .where(and_(
                FamaBenchmark.commodity == commodity.lower(),
                FamaBenchmark.week_date <= week_date,
            ))
            .order_by(FamaBenchmark.week_date.desc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
    if not row:
        return None
    return {"commodity": row.commodity, "price_per_kg": row.price_per_kg, "week_date": str(row.week_date)}


# ─── WEEKLY DIGEST ────────────────────────────────────────────────────────────

async def db_get_weekly_digest() -> dict:
    since = date.today() - timedelta(days=7)
    async with AsyncSessionLocal() as session:
        # Revenue
        result = await session.execute(
            select(Trade.commodity, func.sum(Trade.quantity_kg * Trade.price_per_kg).label("revenue"))
            .where(and_(Trade.trade_type == "sell", Trade.trade_date >= since))
            .group_by(Trade.commodity)
            .order_by(func.sum(Trade.quantity_kg * Trade.price_per_kg).desc())
        )
        revenue_rows = result.all()

        # Outstanding credit
        credit_result = await session.execute(
            select(func.sum(Receivable.amount_rm)).where(Receivable.paid == False)
        )
        total_credit = credit_result.scalar() or 0

    total_revenue = sum(r[1] for r in revenue_rows)
    return {
        "period": f"{since} to {date.today()}",
        "total_revenue_rm": round(total_revenue, 2),
        "by_commodity": [{"commodity": r[0], "revenue_rm": round(r[1], 2)} for r in revenue_rows],
        "best_commodity": revenue_rows[0][0] if revenue_rows else None,
        "worst_commodity": revenue_rows[-1][0] if len(revenue_rows) > 1 else None,
        "outstanding_credit_rm": round(total_credit, 2),
    }


# ─── PRICE TREND (for Stocky's Instinct) ──────────────────────────────────────

async def db_get_price_trend(commodity: str, days: int = 14) -> dict | None:
    """
    Get supplier price trend for a commodity over the last N days.
    Used by Stocky's Instinct to detect pricing patterns.
    """
    since = date.today() - timedelta(days=days)
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(
                SupplierPrice.quoted_date,
                Supplier.name,
                SupplierPrice.price_per_kg,
            )
            .join(Supplier, SupplierPrice.supplier_id == Supplier.id)
            .where(and_(
                SupplierPrice.commodity == commodity.lower(),
                SupplierPrice.quoted_date >= since,
            ))
            .order_by(SupplierPrice.quoted_date)
        )
        rows = result.all()

    if not rows:
        return None

    prices = [r[2] for r in rows]
    avg_early = sum(prices[:len(prices)//2]) / max(len(prices)//2, 1)
    avg_late  = sum(prices[len(prices)//2:]) / max(len(prices) - len(prices)//2, 1)
    trend = "naik" if avg_late > avg_early * 1.05 else "turun" if avg_late < avg_early * 0.95 else "stabil"

    return {
        "commodity":  commodity,
        "period_days": days,
        "data_points": len(rows),
        "earliest_price": prices[0] if prices else None,
        "latest_price":   prices[-1] if prices else None,
        "trend":      trend,
        "pct_change": round((avg_late - avg_early) / avg_early * 100, 1) if avg_early else 0,
    }
