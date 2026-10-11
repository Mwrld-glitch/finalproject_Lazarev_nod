"""Singleton DatabaseManager — работа с JSON-хранилищем."""

import json

from valutatrade_hub.infra.settings import SettingsLoader


class DatabaseManager:
    """Singleton для чтения/записи JSON.

    Реализован через __new__ — простой и читаемый способ.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._settings = SettingsLoader()
        return cls._instance

    def _read(self, key: str):
        """Читает JSON по ключу из SettingsLoader."""
        path = self._settings.get(key)
        if not path.exists():
            return []
        content = path.read_text(encoding="utf-8").strip()
        return json.loads(content) if content else []

    def _write(self, key: str, data) -> None:
        """Пишет JSON по ключу из SettingsLoader."""
        path = self._settings.get(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def load_users(self):
        """Возвращает список объектов User."""
        from valutatrade_hub.core.models import User

        return [User.from_dict(u) for u in self._read("USERS_FILE")]

    def save_users(self, users) -> None:
        """Сохраняет список объектов User."""
        self._write("USERS_FILE", [u.to_dict() for u in users])

    def load_portfolios(self):
        """Возвращает список объектов Portfolio."""
        from valutatrade_hub.core.models import Portfolio

        return [Portfolio.from_dict(p) for p in self._read("PORTFOLIOS_FILE")]

    def save_portfolios(self, portfolios) -> None:
        """Сохраняет список объектов Portfolio."""
        self._write("PORTFOLIOS_FILE", [p.to_dict() for p in portfolios])

    def load_rates(self) -> dict:
        """Читает rates.json → {код: курс_к_USD}."""
        raw = self._read("RATES_FILE")
        result = {"USD": 1.0}
        for key, value in raw.items():
            if isinstance(value, dict) and key.endswith("_USD"):
                result[key[:-4]] = value["rate"]
        return result