"""
tests/unit/test_tools.py — Unit tests for agent/tools.py
"""
import pytest
from unittest.mock import AsyncMock, patch


class TestToolSchemas:
    def test_tools_list_has_10_entries(self):
        from agent.tools import TOOLS
        assert len(TOOLS) == 10

    def test_all_tools_have_required_fields(self):
        from agent.tools import TOOLS
        for tool in TOOLS:
            assert tool["type"] == "function"
            func = tool["function"]
            assert "name" in func
            assert "description" in func
            assert "parameters" in func

    def test_expected_tool_names(self):
        from agent.tools import TOOLS
        names = {t["function"]["name"] for t in TOOLS}
        expected = {
            "get_inventory", "update_inventory", "log_sell",
            "compare_supplier_prices", "get_outstanding_credit",
            "log_credit", "get_weather_forecast", "get_velocity",
            "get_weekly_digest", "get_instinct_analysis",
        }
        assert names == expected


class TestExecuteTool:
    @pytest.mark.asyncio
    async def test_get_inventory(self):
        with patch("db.queries.db_get_inventory", new=AsyncMock(return_value=[{"commodity": "tomato", "quantity_kg": 500}])):
            from agent.tools import execute_tool
            result = await execute_tool("get_inventory", {})
            assert result[0]["commodity"] == "tomato"

    @pytest.mark.asyncio
    async def test_update_inventory(self):
        with patch("db.queries.db_update_inventory", new=AsyncMock(return_value={"status": "updated", "commodity": "cili", "added_kg": 100, "total_stock_kg": 200})):
            from agent.tools import execute_tool
            result = await execute_tool("update_inventory", {"commodity": "cili", "quantity_kg": 100})
            assert result["status"] == "updated"

    @pytest.mark.asyncio
    async def test_log_sell(self):
        with patch("db.queries.db_log_sell", new=AsyncMock(return_value={"status": "logged", "commodity": "tomato", "sold_kg": 50})):
            from agent.tools import execute_tool
            result = await execute_tool("log_sell", {"commodity": "tomato", "quantity_kg": 50})
            assert result["status"] == "logged"

    @pytest.mark.asyncio
    async def test_compare_supplier_prices(self):
        with patch("db.queries.db_compare_prices", new=AsyncMock(return_value={"commodity": "tomato", "suppliers": [], "fama_benchmark": 2.75})):
            from agent.tools import execute_tool
            result = await execute_tool("compare_supplier_prices", {"commodity": "tomato"})
            assert result["fama_benchmark"] == 2.75

    @pytest.mark.asyncio
    async def test_get_outstanding_credit(self):
        with patch("db.queries.db_get_credit", new=AsyncMock(return_value=[{"buyer_name": "Hamid", "amount_rm": 500}])):
            from agent.tools import execute_tool
            result = await execute_tool("get_outstanding_credit", {})
            assert result[0]["buyer_name"] == "Hamid"

    @pytest.mark.asyncio
    async def test_log_credit(self):
        with patch("db.queries.db_log_credit", new=AsyncMock(return_value={"status": "logged", "buyer_name": "Hamid"})):
            from agent.tools import execute_tool
            result = await execute_tool("log_credit", {"buyer_name": "Hamid", "amount_rm": 500})
            assert result["status"] == "logged"

    @pytest.mark.asyncio
    async def test_get_weather_forecast(self):
        with patch("services.weather.get_forecast", new=AsyncMock(return_value=[{"date": "2024-04-20", "condition": "Cerah"}])):
            from agent.tools import execute_tool
            result = await execute_tool("get_weather_forecast", {"city": "Kuala Lumpur"})
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_weather_default_city(self):
        with patch("services.weather.get_forecast", new=AsyncMock(return_value=[])) as mock:
            from agent.tools import execute_tool
            await execute_tool("get_weather_forecast", {})
            mock.assert_called_once_with("Kuala Lumpur")

    @pytest.mark.asyncio
    async def test_get_velocity(self):
        with patch("db.queries.db_get_velocity", new=AsyncMock(return_value={"commodity": "tomato", "avg_daily_kg": 400})):
            from agent.tools import execute_tool
            result = await execute_tool("get_velocity", {"commodity": "tomato"})
            assert result["avg_daily_kg"] == 400

    @pytest.mark.asyncio
    async def test_get_weekly_digest(self):
        with patch("db.queries.db_get_weekly_digest", new=AsyncMock(return_value={"total_revenue_rm": 50000})):
            from agent.tools import execute_tool
            result = await execute_tool("get_weekly_digest", {})
            assert result["total_revenue_rm"] == 50000

    @pytest.mark.asyncio
    async def test_get_instinct_analysis(self):
        with patch("agent.instinct.get_instinct", new=AsyncMock(return_value="Stocky nampak sesuatu: test")):
            from agent.tools import execute_tool
            result = await execute_tool("get_instinct_analysis", {})
            assert "instinct" in result

    @pytest.mark.asyncio
    async def test_unknown_tool_returns_error(self):
        from agent.tools import execute_tool
        result = await execute_tool("nonexistent_tool", {})
        assert "error" in result
        assert "Unknown tool" in result["error"]

    @pytest.mark.asyncio
    async def test_tool_exception_returns_error(self):
        with patch("db.queries.db_get_inventory", new=AsyncMock(side_effect=Exception("DB down"))):
            from agent.tools import execute_tool
            result = await execute_tool("get_inventory", {})
            assert "error" in result
            assert "DB down" in result["error"]
