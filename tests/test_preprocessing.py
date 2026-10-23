from processing.preprocessing import (
    is_expensive,
    needs_warm_clothes,
    normalize_description,
)


def test_warm_clothes_below_zero():
    assert needs_warm_clothes(-3.2) is True


def test_no_warm_clothes_at_zero():
    assert needs_warm_clothes(0) is False


def test_expensive_rate():
    assert is_expensive(100.5) is True
    assert is_expensive(100) is False


def test_empty_description_replaced():
    assert normalize_description("") == "no data"
    assert normalize_description(None) == "no data"
    assert normalize_description(" fog ") == "fog"
