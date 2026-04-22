"""
services/weather.py — Open-Meteo weather forecast (free, no API key).

Owner: Person 4
Docs: https://open-meteo.com/en/docs
"""
import httpx
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Coordinates for Malaysian cities
CITY_COORDS = {
    "Kuala Lumpur": (3.1390, 101.6869),
    "Shah Alam":    (3.0733, 101.5185),
    "Klang":        (3.0449, 101.4450),
    "Petaling Jaya":(3.1073, 101.6067),
    "Seremban":     (2.7297, 101.9381),
}

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


async def get_forecast(city: str = "Kuala Lumpur", days: int = 5) -> list[dict]:
    """
    Fetch weather forecast for a Malaysian city.

    Returns:
        List of daily forecasts: [{date, condition, rain_mm, rain_probability, temp_max}]
    """
    lat, lon = CITY_COORDS.get(city, CITY_COORDS["Kuala Lumpur"])

    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": ["precipitation_sum", "precipitation_probability_max", "temperature_2m_max", "weathercode"],
        "timezone": "Asia/Kuala_Lumpur",
        "forecast_days": days,
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(OPEN_METEO_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

    daily = data["daily"]
    forecasts = []
    for i in range(len(daily["time"])):
        code = daily["weathercode"][i]
        forecasts.append({
            "date": daily["time"][i],
            "condition": _weather_code_to_label(code),
            "rain_mm": daily["precipitation_sum"][i],
            "rain_probability": daily["precipitation_probability_max"][i],
            "temp_max": daily["temperature_2m_max"][i],
            "is_rainy": daily["precipitation_probability_max"][i] > 50,
        })
    return forecasts


def _weather_code_to_label(code: int) -> str:
    if code == 0:
        return "Cerah"
    elif code <= 3:
        return "Berawan"
    elif code <= 67:
        return "Hujan"
    elif code <= 77:
        return "Hujan lebat"
    else:
        return "Ribut"
