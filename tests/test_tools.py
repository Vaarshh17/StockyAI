"""
tests/test_tools.py — Unit tests for tool functions.
Owner: Person 5
"""
import pytest
import pytest_asyncio
from datetime import date
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_get_inventory_returns_list(mock_db):
    from db.queries import db_get_inventory
    result = await db_get_inventory()
    assert isinstance(result, list)


@pytest.mark.asyncio
async def test_update_inventory_increases_stock(seeded_db):
    from db.queries import db_get_inventory, db_update_inventory
    before = await db_get_inventory("tomato")
    before_qty = sum(r["quantity_kg"] for r in before)

    await db_update_inventory("tomato", 500, price_per_kg=2.80, supplier_name="Pak Ali")

    after = await db_get_inventory("tomato")
    after_qty = sum(r["quantity_kg"] for r in after)

    assert after_qty == before_qty + 500


@pytest.mark.asyncio
async def test_log_credit_creates_record(seeded_db):
    from db.queries import db_log_credit, db_get_credit
    await db_log_credit("Test Buyer", 500.0, "tomato", str(date.today()))
    credits = await db_get_credit("Test Buyer")
    assert len(credits) >= 1
    assert credits[0]["amount_rm"] == 500.0


@pytest.mark.asyncio
async def test_compare_prices_returns_ranked_list(seeded_db):
    from db.queries import db_compare_prices
    result = await db_compare_prices("tomato")
    assert "suppliers" in result
    assert "fama_benchmark" in result
    # Should be sorted by price
    prices = [s["price_per_kg"] for s in result["suppliers"]]
    assert prices == sorted(prices)


@pytest.mark.asyncio
async def test_velocity_calculation(seeded_db):
    from db.queries import db_get_velocity
    result = await db_get_velocity("tomato")
    assert "avg_daily_kg" in result
    assert result["avg_daily_kg"] > 0


@pytest.mark.asyncio
async def test_weekly_digest_structure(seeded_db):
    from db.queries import db_get_weekly_digest
    result = await db_get_weekly_digest()
    assert "total_revenue_rm" in result
    assert "outstanding_credit_rm" in result
    assert "by_commodity" in result
