"""Клиенты внешних API для получения курсов."""

from abc import ABC, abstractmethod

import requests

from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.parser_service.config import ParserConfig


class BaseApiClient(ABC):
    """Базовый интерфейс клиента API."""

    @abstractmethod
    def fetch_rates(self) -> dict:
        """Возвращает {ПАРА: курс}."""


class CoinGeckoClient(BaseApiClient):
    """Клиент CoinGecko для криптовалют."""

    def __init__(self, config: ParserConfig | None = None):
        self.config = config or ParserConfig()

    def fetch_rates(self) -> dict:
        ids = ",".join(self.config.CRYPTO_ID_MAP.values())
        params = {"ids": ids, "vs_currencies": self.config.BASE_CURRENCY.lower()}
        try:
            resp = requests.get(
                self.config.COINGECKO_URL,
                params=params,
                timeout=self.config.REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise ApiRequestError(f"CoinGecko: {e}") from e

        data = resp.json()
        result = {}
        for code, coin_id in self.config.CRYPTO_ID_MAP.items():
            rate = data.get(coin_id, {}).get(self.config.BASE_CURRENCY.lower())
            if rate is None:
                raise ApiRequestError(f"CoinGecko: нет курса для {code}")
            result[f"{code}_{self.config.BASE_CURRENCY}"] = float(rate)
        return result


class ExchangeRateApiClient(BaseApiClient):
    """Клиент ExchangeRate-API для фиатных валют."""

    def __init__(self, config: ParserConfig | None = None):
        self.config = config or ParserConfig()

    def fetch_rates(self) -> dict:
        if not self.config.EXCHANGERATE_API_KEY:
            raise ApiRequestError("ExchangeRate-API: не задан API-ключ")

        url = (
            f"{self.config.EXCHANGERATE_API_URL}/"
            f"{self.config.EXCHANGERATE_API_KEY}/latest/"
            f"{self.config.BASE_CURRENCY}"
        )
        try:
            resp = requests.get(url, timeout=self.config.REQUEST_TIMEOUT)
            resp.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise ApiRequestError(f"ExchangeRate-API: {e}") from e

        data = resp.json()
        if data.get("result") != "success":
            raise ApiRequestError(
                f"ExchangeRate-API: {data.get('error-type', 'неизвестная ошибка')}"
            )

        rates = data.get("conversion_rates", {})
        result = {}
        for code in self.config.FIAT_CURRENCIES:
            rate = rates.get(code)
            if rate is None:
                raise ApiRequestError(f"ExchangeRate-API: нет курса для {code}")
            # API отдаёт «сколько X за 1 USD», переворачиваем в «USD за 1 X»
            result[f"{code}_{self.config.BASE_CURRENCY}"] = 1.0 / float(rate)
        return result