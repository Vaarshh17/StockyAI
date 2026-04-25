"""
tests/unit/test_instinct.py — Unit tests for agent/instinct.py
"""
import pytest
from unittest.mock import AsyncMock, patch


class TestGetInstinct:
    @pytest.mark.asyncio
    async def test_returns_instinct_with_data(self):
        with patch("db.queries.db_get_inventory", new=AsyncMock(return_value=[{"commodity": "tomato"}])):
            with patch("db.queries.db_get_weekly_digest", new=AsyncMock(return_value={"total_revenue_rm": 10000})):
                with patch("db.queries.db_get_credit", new=AsyncMock(return_value=[])):
                    with patch("db.queries.db_get_velocity", new=AsyncMock(return_value={"avg_daily_kg": 400})):
                        with patch("db.queries.db_get_price_trend", new=AsyncMock(return_value={"trend": "naik"})):
                            with patch("services.glm.call_llm", new=AsyncMock(return_value={"content": "Stocky nampak sesuatu: tomato harga naik"})):
                                from agent.instinct import get_instinct
                                result = await get_instinct()
        assert "Stocky nampak" in result

    @pytest.mark.asyncio
    async def test_adds_prefix_if_missing(self):
        with patch("db.queries.db_get_inventory", new=AsyncMock(return_value=[{"commodity": "tomato"}])):
            with patch("db.queries.db_get_weekly_digest", new=AsyncMock(return_value={})):
                with patch("db.queries.db_get_credit", new=AsyncMock(return_value=[])):
                    with patch("db.queries.db_get_velocity", new=AsyncMock(return_value={})):
                        with patch("db.queries.db_get_price_trend", new=AsyncMock(return_value=None)):
                            with patch("services.glm.call_llm", new=AsyncMock(return_value={"content": "Harga tomato naik"})):
                                from agent.instinct import get_instinct
                                result = await get_instinct()
        assert result.startswith("Stocky nampak sesuatu:")

    @pytest.mark.asyncio
    async def test_returns_ok_on_empty_response(self):
        with patch("db.queries.db_get_inventory", new=AsyncMock(return_value=[{"commodity": "tomato"}])):
            with patch("db.queries.db_get_weekly_digest", new=AsyncMock(return_value={})):
                with patch("db.queries.db_get_credit", new=AsyncMock(return_value=[])):
                    with patch("db.queries.db_get_velocity", new=AsyncMock(return_value={})):
                        with patch("db.queries.db_get_price_trend", new=AsyncMock(return_value=None)):
                            with patch("services.glm.call_llm", new=AsyncMock(return_value={"content": ""})):
                                from agent.instinct import get_instinct
                                result = await get_instinct()
        assert "semua ok" in result

    @pytest.mark.asyncio
    async def test_returns_empty_on_exception(self):
        with patch("db.queries.db_get_inventory", new=AsyncMock(side_effect=Exception("DB error"))):
            from agent.instinct import get_instinct
            result = await get_instinct()
        assert result == ""


class TestFmtHelper:
    def test_formats_list(self):
        from agent.instinct import _fmt
        result = _fmt([{"a": 1}, {"b": 2}])
        assert "  - " in result

    def test_formats_empty_list(self):
        from agent.instinct import _fmt
        result = _fmt([])
        assert "Tiada data" in result

    def test_formats_dict(self):
        from agent.instinct import _fmt
        result = _fmt({"key": "value"})
        assert "key" in result
        assert "value" in result

    def test_formats_string(self):
        from agent.instinct import _fmt
        result = _fmt("hello")
        assert result == "hello"
