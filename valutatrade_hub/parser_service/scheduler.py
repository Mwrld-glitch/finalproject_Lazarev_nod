"""Планировщик периодического обновления курсов."""

import logging
import time

from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.parser_service.config import ParserConfig
from valutatrade_hub.parser_service.updater import RatesUpdater

log = logging.getLogger(__name__)


def run_periodic(interval_seconds: int = 300, max_runs: int | None = None) -> None:
    """Запускает run_update() каждые interval_seconds секунд.

    max_runs — ограничение на количество прогонов (для тестов);
    если None — работает бесконечно.
    """
    updater = RatesUpdater(ParserConfig())
    runs = 0
    while True:
        try:
            result = updater.run_update()
            log.info(
                "Обновление выполнено: %d курсов, ошибок %d",
                result["updated"], len(result["errors"]),
            )
        except ApiRequestError as e:
            log.error("Обновление не удалось: %s", e)
        except Exception:
            log.exception("Неожиданная ошибка обновления")

        runs += 1
        if max_runs is not None and runs >= max_runs:
            break
        time.sleep(interval_seconds)