"""Утилиты для работы с JSON-файлами."""

import json
from pathlib import Path

DATA_DIR = Path("data")
USERS_FILE = DATA_DIR / "users.json"
PORTFOLIOS_FILE = DATA_DIR / "portfolios.json"


class DataStorage:
    """Работа с JSON-хранилищем."""

    @staticmethod
    def save_users(users, filepath=USERS_FILE):
        """Сохраняет список пользователей."""
        filepath.parent.mkdir(parents=True, exist_ok=True)
        data = [user.to_dict() for user in users]
        filepath.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    @staticmethod
    def load_users(filepath=USERS_FILE):
        """Загружает список пользователей."""
        from valutatrade_hub.core.models import User

        if not filepath.exists():
            return []
        data = json.loads(filepath.read_text(encoding="utf-8"))
        return [User.from_dict(item) for item in data]

    @staticmethod
    def save_portfolios(portfolios, filepath=PORTFOLIOS_FILE):
        """Сохраняет список портфелей."""
        filepath.parent.mkdir(parents=True, exist_ok=True)
        data = [portfolio.to_dict() for portfolio in portfolios]
        filepath.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    @staticmethod
    def load_portfolios(filepath=PORTFOLIOS_FILE):
        """Загружает список портфелей."""
        from valutatrade_hub.core.models import Portfolio

        if not filepath.exists():
            return []
        data = json.loads(filepath.read_text(encoding="utf-8"))
        return [Portfolio.from_dict(item) for item in data]