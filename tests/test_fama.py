"""
tests/unit/test_fama.py — Unit tests for services/fama.py
"""
import pytest
from datetime import date
from unittest.mock import AsyncMock, patch
from services.fama import normalise_commodity, COMMODITY_ALIASES, get_benchmark


class TestNormaliseCommodity:
    def test_canonical_names(self):
        assert normalise_commodity("tomato") == "tomato"
        assert normalise_commodity("cili") == "cili"
        assert normalise_commodity("bayam") == "bayam"
        assert normalise_commodity("kangkung") == "kangkung"

    def test_aliases(self):
        assert normalise_commodity("Tomatoes") == "tomato"
        assert normalise_commodity("chili") == "cili"
        assert normalise_commodity("Chilli") == "cili"
        assert normalise_commodity("spinach") == "bayam"
        assert normalise_commodity("cucumber") == "timun"
        assert normalise_commodity("cabbage") == "kubis"

    def test_case_insensitive(self):
        assert normalise_commodity("TOMATO") == "tomato"
        assert normalise_commodity("BAYAM") == "bayam"

    def test_whitespace_stripped(self):
        assert normalise_commodity("  tomato  ") == "tomato"

    def test_unknown_returns_lowered(self):
        assert normalise_commodity("Mangga") == "mangga"

    def test_kailan_variants(self):
        assert normalise_commodity("kai lan") == "kailan"
        assert normalise_commodity("chinese broccoli") == "kailan"


class TestGetBenchmark:
    @pytest.mark.asyncio
    async def test_delegates_to_db(self):
        with patch("db.queries.get_fama_price", new=AsyncMock(return_value={"commodity": "tomato", "price_per_kg": 2.75, "week_date": "2024-04-15"})):
            result = await get_benchmark("tomato")
            assert result["price_per_kg"] == 2.75

    @pytest.mark.asyncio
    async def test_default_week_is_current_monday(self):
        with patch("db.queries.get_fama_price", new=AsyncMock(return_value=None)) as mock:
            await get_benchmark("tomato")
            call_args = mock.call_args
            # Second arg should be a Monday
            week_date = call_args[0][1]
            assert week_date.weekday() == 0

    @pytest.mark.asyncio
    async def test_custom_week_date(self):
        with patch("db.queries.get_fama_price", new=AsyncMock(return_value=None)) as mock:
            custom_date = date(2024, 4, 15)
            await get_benchmark("tomato", week_date=custom_date)
            mock.assert_called_once_with("tomato", custom_date)

    @pytest.mark.asyncio
    async def test_returns_none_when_no_data(self):
        with patch("db.queries.get_fama_price", new=AsyncMock(return_value=None)):
            result = await get_benchmark("nonexistent")
            assert result is None
