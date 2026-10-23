import argparse
import json
import logging
import re
import sys
import uuid
from typing import Any

from clients.errors import ExternalServiceError, NotFoundError
from processing.service import build_city_summary

EXIT_OK = 0
EXIT_BAD_ARGS = 2
EXIT_NOT_FOUND = 3
EXIT_UNAVAILABLE = 4


def currency_code(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z]{3}", value):
        raise argparse.ArgumentTypeError(
            "ожидается трёхбуквенный ISO-код, например USD"
        )
    return value.upper()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Сводка по городу: погода и курс валюты"
    )
    parser.add_argument("--city", required=True, help="название города")
    parser.add_argument(
        "--currency",
        type=currency_code,
        default="USD",
        help="ISO-код валюты (по умолчанию USD)",
    )
    parser.add_argument("--json", action="store_true", help="вывести сводку в JSON")
    parser.add_argument("-v", "--verbose", action="store_true", help="подробные логи")
    return parser.parse_args(argv)


def setup_logging(verbose: bool) -> None:
    run_id = uuid.uuid4().hex[:8]
    old_factory = logging.getLogRecordFactory()

    def factory(*args: Any, **kwargs: Any) -> logging.LogRecord:
        record = old_factory(*args, **kwargs)
        record.run_id = run_id
        return record

    logging.setLogRecordFactory(factory)
    logging.basicConfig(
        level=logging.INFO if verbose else logging.WARNING,
        format="%(asctime)s [%(run_id)s] %(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
    )


def yes_no(value: bool) -> str:
    return "да" if value else "нет"


def format_summary(summary: dict[str, Any]) -> str:
    weather = summary["weather"]
    rates = summary["rates"]
    return "\n".join(
        [
            f"Город: {summary['city']}",
            f"Погода: {weather['temp_c']}°C, {weather['description']}",
            f"Тёплая одежда: {yes_no(weather['warm_clothes'])}",
            f"{rates['currency']}→RUB: {rates['rate_to_rub']:.2f}",
            f"Дорогой курс: {yes_no(rates['expensive'])}",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    city = args.city.strip()
    if not city:
        print("Ошибка: пустое название города", file=sys.stderr)
        return EXIT_BAD_ARGS
    setup_logging(args.verbose)
    logger = logging.getLogger("city_summary")
    logger.info("Building summary for %s, currency %s", city, args.currency)

    try:
        summary = build_city_summary(city, args.currency)
    except NotFoundError as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return EXIT_NOT_FOUND
    except ExternalServiceError as exc:
        print(f"Внешний сервис недоступен: {exc}", file=sys.stderr)
        return EXIT_UNAVAILABLE

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(format_summary(summary))
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
