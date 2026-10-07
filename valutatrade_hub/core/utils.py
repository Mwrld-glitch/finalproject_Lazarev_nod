"""Утилиты для работы с JSON-файлами."""

import json

from valutatrade_hub.infra.settings import SettingsLoader


class DataStorage:
    """Работа с JSON-хранилищем."""

    @staticmethod
    def save_users(users):
        """Сохраняет список пользователей."""
        settings = SettingsLoader()
        path = settings.get("USERS_FILE")
        path.parent.mkdir(parents=True, exist_ok=True)
        data = [user.to_dict() for user in users]
        path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    @staticmethod
    def load_users():
        """Загружает список пользователей."""
        from valutatrade_hub.core.models import User

        path = SettingsLoader().get("USERS_FILE")
        if not path.exists():
            return []
        data = json.loads(path.read_text(encoding="utf-8"))
        return [User.from_dict(item) for item in data]

    @staticmethod
    def save_portfolios(portfolios):
        """Сохраняет список портфелей."""
        settings = SettingsLoader()
        path = settings.get("PORTFOLIOS_FILE")
        path.parent.mkdir(parents=True, exist_ok=True)
        data = [portfolio.to_dict() for portfolio in portfolios]
        path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    @staticmethod
    def load_portfolios():
        """Загружает список портфелей."""
        from valutatrade_hub.core.models import Portfolio

        path = SettingsLoader().get("PORTFOLIOS_FILE")
        if not path.exists():
            return []
        data = json.loads(path.read_text(encoding="utf-8"))
        return [Portfolio.from_dict(item) for item in data]