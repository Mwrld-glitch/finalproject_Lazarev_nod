"""Утилиты: валидации валютных кодов, конвертации."""

from valutatrade_hub.core.currencies import get_currency

EXCHANGE_RATES: dict[str, float] = {
    "USD": 1.0,
    "EUR": 1.0786,
    "RUB": 0.01016,
    "BTC": 59337.21,
    "ETH": 3720.00,
}


def normalize_code(code: str) -> str:
    """Приводит код к верхнему регистру и валидирует через реестр."""
    return get_currency(code).code


def convert(amount: float, rate: float) -> float:
    """Конвертирует сумму по курсу."""
    if not isinstance(amount, (int, float)) or amount < 0:
        raise ValueError("Сумма должна быть неотрицательным числом")
    if not isinstance(rate, (int, float)) or rate < 0:
        raise ValueError("Курс должен быть неотрицательным числом")
    return float(amount) * float(rate)