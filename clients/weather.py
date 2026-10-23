from typing import Any

from clients.errors import ExternalServiceError, InvalidResponseError, NotFoundError
from clients.http import get_json

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

WEATHER_CODES = {
    0: "clear sky",
    1: "mainly clear",
    2: "partly cloudy",
    3: "overcast",
    45: "fog",
    48: "rime fog",
    51: "light drizzle",
    53: "drizzle",
    55: "dense drizzle",
    56: "freezing drizzle",
    57: "dense freezing drizzle",
    61: "light rain",
    63: "rain",
    65: "heavy rain",
    66: "freezing rain",
    67: "heavy freezing rain",
    71: "light snow",
    73: "snow",
    75: "heavy snow",
    77: "snow grains",
    80: "light showers",
    81: "showers",
    82: "violent showers",
    85: "snow showers",
    86: "heavy snow showers",
    95: "thunderstorm",
    96: "thunderstorm with hail",
    99: "thunderstorm with heavy hail",
}


def _check_status(status: int, url: str) -> None:
    if status != 200:
        raise ExternalServiceError(f"{url}: unexpected status {status}")


def _find_city(city: str) -> tuple[float, float, str]:
    status, data = get_json(GEOCODING_URL, {"name": city, "count": 1})
    _check_status(status, GEOCODING_URL)
    if not isinstance(data, dict):
        raise InvalidResponseError("geocoding: unexpected response format")
    results = data.get("results") or []
    if not results:
        raise NotFoundError(f"city not found: {city}")
    place = results[0]
    try:
        return float(place["latitude"]), float(place["longitude"]), str(place["name"])
    except (KeyError, TypeError, ValueError) as exc:
        raise InvalidResponseError("geocoding: missing coordinates") from exc


def _parse_current(data: Any) -> tuple[float, int]:
    try:
        current = data["current"]
        return float(current["temperature_2m"]), int(current["weather_code"])
    except (KeyError, TypeError, ValueError) as exc:
        raise InvalidResponseError("forecast: missing current weather") from exc


def get_weather(city: str) -> dict[str, Any]:
    latitude, longitude, name = _find_city(city)
    status, data = get_json(
        FORECAST_URL,
        {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,weather_code",
        },
    )
    _check_status(status, FORECAST_URL)
    temp_c, code = _parse_current(data)
    return {
        "city": name,
        "temp_c": temp_c,
        "description": WEATHER_CODES.get(code, ""),
    }
