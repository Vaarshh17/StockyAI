"""
tests/integration/test_db.py — Integration tests for database layer (models + queries).
Uses real in-memory SQLite to test actual SQL operations.
"""
import pytest
from datetime import date, timedelta


@pytest.mark.asyncio
async def test_init_db_creates_tables(fresh_db):
    from db.models import engine
    from sqlalchemy import inspect
    async with engine.connect() as conn:
        tables = await conn.run_sync(lambda sync_conn: inspect(sync_conn).get_table_names())
    expected = {"inventory", "suppliers", "supplier_prices", "trades", "receivables", "fama_benchmarks", "user_profiles"}
    assert expected.issubset(set(tables))


class TestInventoryQueries:
    @pytest.mark.asyncio
    async def test_get_inventory_empty_db(self, fresh_db):
        from db.queries import db_get_inventory
        result = await db_get_inventory()
        assert result == []

    @pytest.mark.asyncio
    async def test_update_inventory_creates_entry(self, fresh_db):
        from db.queries import db_update_inventory, db_get_inventory
        await db_update_inventory("tomato", 500, price_per_kg=2.60, supplier_name="Pak Ali")
        result = await db_get_inventory("tomato")
        assert len(result) >= 1
        assert result[0]["quantity_kg"] == 500

    @pytest.mark.asyncio
    async def test_update_inventory_creates_supplier(self, fresh_db):
        from db.queries import db_update_inventory
        await db_update_inventory("cili", 100, price_per_kg=4.00, supplier_name="New Supplier")
        from db.models import AsyncSessionLocal, Supplier
        from sqlalchemy import select
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Supplier).where(Supplier.name == "New Supplier"))
            assert result.scalar_one_or_none() is not None

    @pytest.mark.asyncio
    async def test_update_inventory_logs_trade(self, fresh_db):
        from db.queries import db_update_inventory
        from db.models import AsyncSessionLocal, Trade
        from sqlalchemy import select
        await db_update_inventory("tomato", 300, price_per_kg=2.50, supplier_name="Pak Ali")
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Trade).where(Trade.trade_type == "buy"))
            trade = result.scalar_one_or_none()
            assert trade is not None
            assert trade.commodity == "tomato"
            assert trade.quantity_kg == 300

    @pytest.mark.asyncio
    async def test_update_inventory_without_supplier(self, fresh_db):
        from db.queries import db_update_inventory, db_get_inventory
        await db_update_inventory("bayam", 200, shelf_life_days=3)
        result = await db_get_inventory("bayam")
        assert len(result) >= 1
        assert result[0]["quantity_kg"] == 200

    @pytest.mark.asyncio
    async def test_log_sell_deducts_fifo(self, fresh_db):
        from db.queries import db_update_inventory, db_log_sell, db_get_inventory
        await db_update_inventory("tomato", 500, price_per_kg=2.50, supplier_name="Pak Ali")
        await db_update_inventory("tomato", 300, price_per_kg=2.80, supplier_name="Ah Seng")
        result = await db_log_sell("tomato", 200, price_per_kg=3.20, buyer_name="Restoran Maju")
        assert result["sold_kg"] == 200
        assert result["remaining_stock_kg"] == 600

    @pytest.mark.asyncio
    async def test_log_sell_records_trade(self, fresh_db):
        from db.queries import db_update_inventory, db_log_sell
        from db.models import AsyncSessionLocal, Trade
        from sqlalchemy import select
        await db_update_inventory("tomato", 500, price_per_kg=2.50, supplier_name="Pak Ali")
        await db_log_sell("tomato", 100, price_per_kg=3.20, buyer_name="Test Buyer")
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Trade).where(Trade.trade_type == "sell"))
            trade = result.scalar_one_or_none()
            assert trade is not None
            assert trade.counterparty == "Test Buyer"

    @pytest.mark.asyncio
    async def test_days_remaining_calculation(self, fresh_db):
        from db.queries import db_update_inventory, db_get_inventory
        await db_update_inventory("bayam", 100, shelf_life_days=3)
        result = await db_get_inventory("bayam")
        assert result[0]["days_remaining"] == 3

    @pytest.mark.asyncio
    async def test_zero_quantity_excluded(self, fresh_db):
        from db.queries import db_update_inventory, db_log_sell, db_get_inventory
        await db_update_inventory("tomato", 100, price_per_kg=2.50, supplier_name="Pak Ali")
        await db_log_sell("tomato", 100)
        result = await db_get_inventory("tomato")
        assert len(result) == 0


class TestCreditQueries:
    @pytest.mark.asyncio
    async def test_log_and_get_credit(self, fresh_db):
        from db.queries import db_log_credit, db_get_credit
        due = str(date.today() + timedelta(days=7))
        await db_log_credit("Kedai Pak Hamid", 500.0, "bayam", due)
        result = await db_get_credit("Kedai Pak Hamid")
        assert len(result) >= 1
        assert result[0]["amount_rm"] == 500.0

    @pytest.mark.asyncio
    async def test_get_all_unpaid_credit(self, fresh_db):
        from db.queries import db_log_credit, db_get_credit
        await db_log_credit("Buyer A", 100, "tomato")
        await db_log_credit("Buyer B", 200, "cili")
        result = await db_get_credit()
        assert len(result) >= 2

    @pytest.mark.asyncio
    async def test_overdue_detection(self, fresh_db):
        from db.queries import db_log_credit, db_get_credit
        overdue_date = str(date.today() - timedelta(days=2))
        await db_log_credit("Late Payer", 300, "tomato", overdue_date)
        result = await db_get_credit("Late Payer")
        assert result[0]["days_overdue"] > 0

    @pytest.mark.asyncio
    async def test_due_today_detection(self, fresh_db):
        from db.queries import db_log_credit, db_get_credit
        await db_log_credit("Today Payer", 100, "cili", str(date.today()))
        result = await db_get_credit("Today Payer")
        assert result[0]["due_today"] is True

    @pytest.mark.asyncio
    async def test_log_credit_default_due_date(self, fresh_db):
        from db.queries import db_log_credit
        result = await db_log_credit("No Date Buyer", 100, "tomato")
        assert result["due_date"] is not None


class TestSupplierPriceQueries:
    @pytest.mark.asyncio
    async def test_compare_prices(self, fresh_db):
        from db.queries import db_update_inventory, db_compare_prices
        from db.models import AsyncSessionLocal, FamaBenchmark
        from sqlalchemy import select

        # Seed FAMA benchmark for compare_prices to work
        async with AsyncSessionLocal() as session:
            session.add(FamaBenchmark(commodity="tomato", price_per_kg=2.75, week_date=date.today()))
            await session.commit()

        await db_update_inventory("tomato", 500, price_per_kg=2.60, supplier_name="Pak Ali")
        await db_update_inventory("tomato", 300, price_per_kg=2.85, supplier_name="Ah Seng")
        result = await db_compare_prices("tomato")
        assert "suppliers" in result
        assert "fama_benchmark" in result
        if len(result["suppliers"]) >= 2:
            prices = [s["price_per_kg"] for s in result["suppliers"]]
            assert prices == sorted(prices)

    @pytest.mark.asyncio
    async def test_compare_prices_empty(self, fresh_db):
        from db.queries import db_compare_prices
        result = await db_compare_prices("mangga")
        assert result["suppliers"] == []
        assert result["cheapest"] is None


class TestVelocityQueries:
    @pytest.mark.asyncio
    async def test_velocity_calculation(self, fresh_db):
        from db.queries import db_update_inventory, db_log_sell, db_get_velocity
        await db_update_inventory("tomato", 5000, price_per_kg=2.50, supplier_name="Pak Ali")
        await db_log_sell("tomato", 100, price_per_kg=3.20)
        result = await db_get_velocity("tomato")
        assert result["avg_daily_kg"] > 0
        assert result["commodity"] == "tomato"

    @pytest.mark.asyncio
    async def test_velocity_no_sales(self, fresh_db):
        from db.queries import db_get_velocity
        result = await db_get_velocity("mangga")
        assert result["avg_daily_kg"] == 0


class TestFamaBenchmarkQueries:
    @pytest.mark.asyncio
    async def test_get_fama_price(self, seeded_db):
        from db.queries import get_fama_price
        result = await get_fama_price("tomato")
        assert result is not None
        assert result["price_per_kg"] > 0

    @pytest.mark.asyncio
    async def test_get_fama_price_nonexistent(self, fresh_db):
        from db.queries import get_fama_price
        result = await get_fama_price("mangga")
        assert result is None


class TestWeeklyDigest:
    @pytest.mark.asyncio
    async def test_digest_with_data(self, seeded_db):
        from db.queries import db_get_weekly_digest
        result = await db_get_weekly_digest()
        assert "total_revenue_rm" in result
        assert "outstanding_credit_rm" in result
        assert "by_commodity" in result

    @pytest.mark.asyncio
    async def test_digest_empty_db(self, fresh_db):
        from db.queries import db_get_weekly_digest
        result = await db_get_weekly_digest()
        assert result["total_revenue_rm"] == 0
        assert result["best_commodity"] is None


class TestUserProfile:
    @pytest.mark.asyncio
    async def test_save_and_get_persona(self, fresh_db):
        from db.queries import db_save_persona, db_get_persona
        persona = {"name": "Ahmad", "language": "Bahasa Malaysia", "commodities": ["tomato", "cili"], "city": "KL"}
        await db_save_persona(12345, persona)
        result = await db_get_persona(12345)
        assert result["name"] == "Ahmad"
        assert "tomato" in result["commodities"]

    @pytest.mark.asyncio
    async def test_update_existing_persona(self, fresh_db):
        from db.queries import db_save_persona, db_get_persona
        await db_save_persona(999, {"name": "Old", "language": "English", "commodities": [], "city": "KL"})
        await db_save_persona(999, {"name": "New", "language": "Mandarin", "commodities": ["cili"], "city": "JB"})
        result = await db_get_persona(999)
        assert result["name"] == "New"
        assert result["language"] == "Mandarin"

    @pytest.mark.asyncio
    async def test_get_nonexistent_persona(self, fresh_db):
        from db.queries import db_get_persona
        result = await db_get_persona(99999)
        assert result is None


class TestPriceTrend:
    @pytest.mark.asyncio
    async def test_price_trend_with_data(self, seeded_db):
        from db.queries import db_get_price_trend
        result = await db_get_price_trend("tomato", days=14)
        if result:
            assert "trend" in result
            assert result["commodity"] == "tomato"

    @pytest.mark.asyncio
    async def test_price_trend_no_data(self, fresh_db):
        from db.queries import db_get_price_trend
        result = await db_get_price_trend("mangga", days=14)
        assert result is None


class TestSeedData:
    @pytest.mark.asyncio
    async def test_seed_creates_data(self, seeded_db):
        from db.queries import db_get_inventory, db_get_credit
        inventory = await db_get_inventory()
        credit = await db_get_credit()
        assert len(inventory) > 0
        assert len(credit) > 0

    @pytest.mark.asyncio
    async def test_seed_idempotent(self, seeded_db):
        from db.seed import seed_demo_data
        await seed_demo_data()
        from db.queries import db_get_inventory
        inventory = await db_get_inventory()
        assert len(inventory) > 0
