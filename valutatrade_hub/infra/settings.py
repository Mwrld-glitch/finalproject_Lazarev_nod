"""Singleton SettingsLoader — единая точка конфигурации."""

from pathlib import Path
from typing import Any


class SettingsLoader:
    """Singleton с настройками проекта. """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load()
        return cls._instance

    def _load(self) -> None:
        """Загружает конфигурацию."""
        self._settings = {
            "DATA_DIR": Path("data"),
            "USERS_FILE": Path("data/users.json"),
            "PORTFOLIOS_FILE": Path("data/portfolios.json"),
            "RATES_FILE": Path("data/rates.json"),
            "HISTORY_FILE": Path("data/exchange_rates.json"),
            "RATES_TTL_SECONDS": 300,
            "DEFAULT_BASE": "USD",
            "LOG_FILE": Path("logs/actions.log"),
            "LOG_FORMAT": "%(asctime)s %(levelname)s %(message)s",
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Возвращает значение по ключу."""
        return self._settings.get(key, default)

    def reload(self) -> None:
        """Перезагружает конфигурацию."""
        self._load()