"""Иерархия валют: Currency, FiatCurrency, CryptoCurrency."""

from abc import ABC, abstractmethod

from valutatrade_hub.core.exceptions import CurrencyNotFoundError


class Currency(ABC):
    """Абстрактный базовый класс валюты."""

    def __init__(self, code: str, name: str):
        if not code or not code.strip():
            raise ValueError("Код валюты не может быть пустым")
        code = code.strip().upper()
        if not (2 <= len(code) <= 5):
            raise ValueError("Код валюты должен быть 2–5 символов")
        if " " in code:
            raise ValueError("Код валюты не должен содержать пробелов")
        if not name or not name.strip():
            raise ValueError("Имя валюты не может быть пустым")
        self.code = code
        self.name = name.strip()

    @abstractmethod
    def get_display_info(self) -> str:
        """Строковое представление для UI/логов."""


class FiatCurrency(Currency):
    """Фиатная валюта."""

    def __init__(self, code: str, name: str, issuing_country: str):
        super().__init__(code, name)
        if not issuing_country or not issuing_country.strip():
            raise ValueError("Страна эмиссии не может быть пустой")
        self.issuing_country = issuing_country.strip()

    def get_display_info(self) -> str:
        return (
            f"[FIAT] {self.code} — {self.name} "
            f"(Issuing: {self.issuing_country})"
        )


class CryptoCurrency(Currency):
    """Криптовалюта."""

    def __init__(self, code: str, name: str, algorithm: str, market_cap: float):
        super().__init__(code, name)
        if not algorithm or not algorithm.strip():
            raise ValueError("Алгоритм не может быть пустым")
        if not isinstance(market_cap, (int, float)) or market_cap < 0:
            raise ValueError("Капитализация должна быть неотрицательным числом")
        self.algorithm = algorithm.strip()
        self.market_cap = float(market_cap)

    def get_display_info(self) -> str:
        return (
            f"[CRYPTO] {self.code} — {self.name} "
            f"(Algo: {self.algorithm}, MCAP: {self.market_cap:.2e})"
        )


CURRENCIES: dict[str, Currency] = {
    "USD": FiatCurrency("USD", "US Dollar", "United States"),
    "EUR": FiatCurrency("EUR", "Euro", "Eurozone"),
    "RUB": FiatCurrency("RUB", "Russian Ruble", "Russia"),
    "BTC": CryptoCurrency("BTC", "Bitcoin", "SHA-256", 1.12e12),
    "ETH": CryptoCurrency("ETH", "Ethereum", "Ethash", 4.0e11),
}


def get_currency(code: str) -> Currency:
    """Возвращает объект валюты по коду или бросает CurrencyNotFoundError."""
    if not code or not isinstance(code, str):
        raise CurrencyNotFoundError(f"Неизвестная валюта '{code}'")
    code = code.strip().upper()
    if code not in CURRENCIES:
        raise CurrencyNotFoundError(f"Неизвестная валюта '{code}'")
    return CURRENCIES[code]