import logging
import time
from typing import Any

import requests

from clients.errors import ExternalServiceError, InvalidResponseError

TIMEOUT = 5
RETRIES = 2
BACKOFF = 0.5
MAX_RETRY_AFTER = 10
RETRY_STATUSES = {500, 502, 503, 504}

logger = logging.getLogger(__name__)


def _retry_after(response: requests.Response) -> float | None:
    value = response.headers.get("Retry-After", "")
    if value.isdigit():
        return min(float(value), MAX_RETRY_AFTER)
    return None


def get_json(
    url: str,
    params: dict[str, Any] | None = None,
    session: requests.Session | None = None,
) -> tuple[int, Any]:
    http = session or requests
    for attempt in range(RETRIES + 1):
        delay = BACKOFF * 2**attempt
        try:
            response = http.get(url, params=params, timeout=TIMEOUT)
        except (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
        ) as exc:
            logger.warning("GET %s failed: %s (attempt %d)", url, exc, attempt + 1)
        else:
            if response.status_code == 429:
                delay = _retry_after(response) or delay
                logger.warning("GET %s rate limited (attempt %d)", url, attempt + 1)
            elif response.status_code in RETRY_STATUSES:
                logger.warning(
                    "GET %s returned %d (attempt %d)",
                    url,
                    response.status_code,
                    attempt + 1,
                )
            else:
                try:
                    return response.status_code, response.json()
                except ValueError as exc:
                    raise InvalidResponseError(f"{url}: response is not JSON") from exc
        if attempt < RETRIES:
            time.sleep(delay)
    raise ExternalServiceError(f"{url}: service unavailable after {RETRIES} retries")
