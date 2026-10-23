COLD_THRESHOLD_C = 0
EXPENSIVE_THRESHOLD = 100
DEFAULT_DESCRIPTION = "no data"


def needs_warm_clothes(temp_c: float) -> bool:
    return temp_c < COLD_THRESHOLD_C


def is_expensive(rate_to_rub: float) -> bool:
    return rate_to_rub > EXPENSIVE_THRESHOLD


def normalize_description(description: str | None) -> str:
    cleaned = (description or "").strip()
    return cleaned or DEFAULT_DESCRIPTION
