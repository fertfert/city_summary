from unittest.mock import MagicMock, patch

import pytest
import requests

from clients import http, rates
from clients.errors import ExternalServiceError, NotFoundError


def make_response(status, payload=None, headers=None):
    response = MagicMock()
    response.status_code = status
    response.headers = headers or {}
    response.json.return_value = payload
    return response


@pytest.fixture(autouse=True)
def no_sleep():
    with patch("clients.http.time.sleep") as sleep:
        yield sleep


@pytest.fixture(autouse=True)
def clear_cache():
    rates._cache.clear()


def test_retries_on_timeout_then_succeeds():
    responses = [requests.exceptions.Timeout(), make_response(200, {"ok": True})]
    with patch("clients.http.requests.get", side_effect=responses) as get:
        assert http.get_json("https://example.com") == (200, {"ok": True})
    assert get.call_count == 2
    assert get.call_args.kwargs["timeout"] <= 10


def test_gives_up_after_retries():
    with (
        patch("clients.http.requests.get", return_value=make_response(503)) as get,
        pytest.raises(ExternalServiceError),
    ):
        http.get_json("https://example.com")
    assert get.call_count == http.RETRIES + 1


def test_respects_retry_after(no_sleep):
    responses = [
        make_response(429, headers={"Retry-After": "3"}),
        make_response(200, {}),
    ]
    with patch("clients.http.requests.get", side_effect=responses):
        http.get_json("https://example.com")
    no_sleep.assert_called_once_with(3.0)


def test_unknown_currency():
    response = make_response(422, {"message": "invalid currency"})
    with (
        patch("clients.http.requests.get", return_value=response),
        pytest.raises(NotFoundError),
    ):
        rates.get_rate("XXX")


def test_rate_is_cached():
    response = make_response(200, {"rate": 81.46})
    with patch("clients.http.requests.get", return_value=response) as get:
        assert rates.get_rate("USD") == 81.46
        assert rates.get_rate("usd") == 81.46
    assert get.call_count == 1
