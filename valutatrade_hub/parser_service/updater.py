"""Обновление курсов из внешних API."""

import logging
from datetime import datetime, timezone

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
        """Обновляет курсы.

        Возвращает {"updated": int, "last_refresh": str, "errors": [str]}.
        Бросает ApiRequestError только если упали все клиенты.
        """
        log.info("Старт обновления курсов (source=%s)", source or "all")

        all_rates: dict = {}
        sources: dict = {}
        timestamps: dict = {}
        errors: list[str] = []
        succeeded = 0

        for client in self.clients:
            name = type(client).__name__
            if source and source.lower() not in name.lower():
                continue
            try:
                response = client.fetch_rates()
                rates = response["rates"]
                updated_at = response.get("updated_at")
                all_rates.update(rates)
                for pair in rates:
                    sources[pair] = name
                    if updated_at:
                        timestamps[pair] = updated_at
                succeeded += 1
                log.info("%s: получено %d курсов", name, len(rates))
            except ApiRequestError as e:
                errors.append(f"{name}: {e}")
                log.error("%s: ошибка — %s", name, e)
            except Exception as e:
                errors.append(f"{name}: {e}")
                log.exception("%s: неожиданная ошибка", name)

        if not all_rates:
            log.error("Не удалось получить ни одного курса")
            raise ApiRequestError(
                "Ошибка при обращении к внешнему API: "
                + ("; ".join(errors) if errors else "все источники недоступны")
            )

        self.storage.save_rates(all_rates, sources, timestamps)
        self.storage.append_history(all_rates, sources)

        last_refresh = datetime.now(timezone.utc).isoformat()
        log.info(
            "Сохранено %d курсов, источников успешно: %d",
            len(all_rates), succeeded,
        )

        return {
            "updated": len(all_rates),
            "last_refresh": last_refresh,
            "errors": errors,
        }