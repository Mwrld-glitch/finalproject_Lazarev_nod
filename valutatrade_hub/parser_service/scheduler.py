"""Планировщик периодического обновления курсов."""

import logging
import time

from valutatrade_hub.parser_service.updater import RatesUpdater

log = logging.getLogger(__name__)


def run_periodic(interval_seconds: int = 300, max_runs: int | None = None) -> None:
    """Запускает обновление курсов каждые interval_seconds секунд."""
    updater = RatesUpdater()
    runs = 0
    while True:
        try:
            updater.run_update()
        except Exception as e:
            log.error("Ошибка обновления: %s", e)
        runs += 1
        if max_runs is not None and runs >= max_runs:
            break
        time.sleep(interval_seconds)