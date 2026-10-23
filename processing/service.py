from typing import Any

from clients.rates import get_rate
from clients.weather import get_weather
from processing.preprocessing import (
    is_expensive,
    needs_warm_clothes,
    normalize_description,
)


def build_city_summary(city: str, currency: str = "USD") -> dict[str, Any]:
    currency = currency.upper()
    weather = get_weather(city)
    rate = get_rate(currency)
    return {
        "city": weather["city"],
        "weather": {
            "temp_c": weather["temp_c"],
            "description": normalize_description(weather["description"]),
            "warm_clothes": needs_warm_clothes(weather["temp_c"]),
        },
        "rates": {
            "currency": currency,
            "rate_to_rub": round(rate, 2),
            "expensive": is_expensive(rate),
        },
    }
