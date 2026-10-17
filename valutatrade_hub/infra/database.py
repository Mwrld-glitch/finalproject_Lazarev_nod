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

    def _read(self, key: str, default):
        """Читает JSON по ключу из SettingsLoader.

        default — что вернуть, если файла нет или он пуст.
        """
        path = self._settings.get(key)
        if not path.exists():
            return default
        content = path.read_text(encoding="utf-8").strip()
        if not content:
            return default
        return json.loads(content)

    def _write(self, key: str, data) -> None:
        """Пишет JSON по ключу из SettingsLoader."""
        path = self._settings.get(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    # ----- users -----

    def load_users(self):
        """Возвращает список объектов User."""
        from valutatrade_hub.core.models import User

        return [User.from_dict(u) for u in self._read("USERS_FILE", [])]

    def save_users(self, users) -> None:
        """Сохраняет список объектов User."""
        self._write("USERS_FILE", [u.to_dict() for u in users])

    # ----- portfolios -----

    def load_portfolios(self):
        """Возвращает список объектов Portfolio."""
        from valutatrade_hub.core.models import Portfolio

        return [
            Portfolio.from_dict(p)
            for p in self._read("PORTFOLIOS_FILE", [])
        ]

    def save_portfolios(self, portfolios) -> None:
        """Сохраняет список объектов Portfolio."""
        self._write(
            "PORTFOLIOS_FILE",
            [p.to_dict() for p in portfolios],
        )

    # ----- rates -----

    def load_rates(self) -> dict:
        """Читает rates.json в формате ТЗ.

        Возвращает {"pairs": {...}, "last_refresh": ...}.
        """
        return self._read(
            "RATES_FILE",
            {"pairs": {}, "last_refresh": None},
        )

    def save_rates(self, data: dict) -> None:
        """Сохраняет rates.json (формат ТЗ)."""
        self._write("RATES_FILE", data)

    def load_rates_map(self) -> dict:
        """Плоский словарь {код: курс_к_USD} для usecases."""
        raw = self.load_rates()
        result = {"USD": 1.0}
        for pair, value in raw.get("pairs", {}).items():
            if isinstance(value, dict) and pair.endswith("_USD"):
                result[pair[:-4]] = value["rate"]
        return result

    # ----- history (Parser Service) -----

    def load_history(self) -> list:
        """Читает exchange_rates.json (список записей)."""
        return self._read("HISTORY_FILE", [])

    def save_history(self, records: list) -> None:
        """Сохраняет exchange_rates.json."""
        self._write("HISTORY_FILE", records)