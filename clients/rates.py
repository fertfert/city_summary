import time

from clients.errors import ExternalServiceError, InvalidResponseError, NotFoundError
from clients.http import get_json

RATE_URL = "https://api.frankfurter.dev/v2/rate/{currency}/RUB"
CACHE_TTL = 300

_cache: dict[str, tuple[float, float]] = {}


def get_rate(currency: str = "USD") -> float:
    currency = currency.upper()
    if currency == "RUB":
        return 1.0
    cached = _cache.get(currency)
    if cached and time.monotonic() - cached[1] < CACHE_TTL:
        return cached[0]

    url = RATE_URL.format(currency=currency)
    status, data = get_json(url)
    if status in (404, 422):
        raise NotFoundError(f"currency not found: {currency}")
    if status != 200:
        raise ExternalServiceError(f"{url}: unexpected status {status}")
    try:
        rate = float(data["rate"])
    except (KeyError, TypeError, ValueError) as exc:
        raise InvalidResponseError("rates: missing rate field") from exc
    if rate <= 0:
        raise InvalidResponseError(f"rates: invalid rate {rate}")

    _cache[currency] = (rate, time.monotonic())
    return rate
