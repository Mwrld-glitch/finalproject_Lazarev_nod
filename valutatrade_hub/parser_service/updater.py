"""Обновление курсов из внешних API."""

import logging

from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.parser_service.api_clients import (
    CoinGeckoClient,
    ExchangeRateApiClient,
)
from valutatrade_hub.parser_service.config import ParserConfig
from valutatrade_hub.parser_service.storage import RatesStorage

log = logging.getLogger(__name__)


class RatesUpdater:
    """Опрашивает клиентов и сохраняет курсы."""

    def __init__(
        self,
        config: ParserConfig | None = None,
        clients: list | None = None,
        storage: RatesStorage | None = None,
    ):
        self.config = config or ParserConfig()
        self.clients = clients or [
            CoinGeckoClient(self.config),
            ExchangeRateApiClient(self.config),
        ]
        self.storage = storage or RatesStorage(self.config)

    def run_update(self, source: str | None = None) -> dict:
        """Обновляет курсы. Если source задан — только этого клиента."""
        log.info("Старт обновления курсов (source=%s)", source or "all")
        all_rates: dict = {}
        sources: dict = {}

        for client in self.clients:
            name = type(client).__name__
            if source and source.lower() not in name.lower():
                continue
            try:
                rates = client.fetch_rates()
                all_rates.update(rates)
                for pair in rates:
                    sources[pair] = name
                log.info("%s: получено %d курсов", name, len(rates))
            except ApiRequestError as e:
                log.error("%s: ошибка — %s", name, e)

        if all_rates:
            self.storage.save_rates(all_rates, sources)
            self.storage.append_history(all_rates, sources)
            log.info("Сохранено %d курсов", len(all_rates))

        return all_rates