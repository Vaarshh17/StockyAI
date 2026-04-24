"""
tests/unit/test_weather.py — Unit tests for services/weather.py
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from services.weather import get_forecast, _weather_code_to_label, CITY_COORDS


class TestWeatherCodeToLabel:
    def test_clear(self):
        assert _weather_code_to_label(0) == "Cerah"

    def test_cloudy(self):
        assert _weather_code_to_label(1) == "Berawan"
        assert _weather_code_to_label(3) == "Berawan"

    def test_rain(self):
        assert _weather_code_to_label(51) == "Hujan"
        assert _weather_code_to_label(67) == "Hujan"

    def test_heavy_rain(self):
        assert _weather_code_to_label(73) == "Hujan lebat"

    def test_storm(self):
        assert _weather_code_to_label(95) == "Ribut"


class TestCityCoords:
    def test_kuala_lumpur_exists(self):
        assert "Kuala Lumpur" in CITY_COORDS

    def test_all_cities_have_coords(self):
        for city, (lat, lon) in CITY_COORDS.items():
            assert isinstance(lat, float)
            assert isinstance(lon, float)
            assert 1 < lat < 7
            assert 100 < lon < 120


class TestGetForecast:
    @pytest.mark.asyncio
    async def test_returns_forecast_list(self):
        mock_response = {
            "daily": {
                "time": ["2024-04-20", "2024-04-21"],
                "weathercode": [0, 3],
                "precipitation_sum": [0.0, 5.0],
                "precipitation_probability_max": [10, 80],
                "temperature_2m_max": [33.0, 30.0],
            }
        }

        mock_resp = AsyncMock()
        mock_resp.json = MagicMock(return_value=mock_response)
        mock_resp.raise_for_status = AsyncMock()

        client_instance = AsyncMock()
        client_instance.get = AsyncMock(return_value=mock_resp)
        client_instance.__aenter__ = AsyncMock(return_value=client_instance)
        client_instance.__aexit__ = AsyncMock(return_value=False)

        with patch("services.weather.httpx.AsyncClient", return_value=client_instance):
            result = await get_forecast("Kuala Lumpur")

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["condition"] == "Cerah"
        assert result[1]["is_rainy"] is True

    @pytest.mark.asyncio
    async def test_default_city_is_kuala_lumpur(self):
        mock_response = {
            "daily": {
                "time": [],
                "weathercode": [],
                "precipitation_sum": [],
                "precipitation_probability_max": [],
                "temperature_2m_max": [],
            }
        }

        mock_resp = AsyncMock()
        mock_resp.json = MagicMock(return_value=mock_response)
        mock_resp.raise_for_status = AsyncMock()

        client_instance = AsyncMock()
        client_instance.get = AsyncMock(return_value=mock_resp)
        client_instance.__aenter__ = AsyncMock(return_value=client_instance)
        client_instance.__aexit__ = AsyncMock(return_value=False)

        with patch("services.weather.httpx.AsyncClient", return_value=client_instance):
            result = await get_forecast("Nonexistent City")

        assert isinstance(result, list)
