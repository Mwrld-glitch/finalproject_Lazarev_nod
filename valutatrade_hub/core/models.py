"""Модели данных: User, Wallet, Portfolio."""

import hashlib
import secrets
from datetime import datetime

from valutatrade_hub.core.exceptions import InsufficientFundsError


class User:
    """Пользователь системы."""

    def __init__(self, user_id: int, username: str,
                 hashed_password: str = "", salt: str = "",
                 registration_date: datetime = None):
        self.user_id = user_id
        self.username = username
        self._hashed_password = hashed_password or ""
        self._salt = salt or ""
        self.registration_date = registration_date or datetime.now()

    @property
    def user_id(self) -> int:
        return self._user_id

    @user_id.setter
    def user_id(self, value: int):
        if not isinstance(value, int) or value <= 0:
            raise ValueError("user_id должен быть положительным целым числом")
        self._user_id = value

    @property
    def username(self) -> str:
        return self._username

    @username.setter
    def username(self, value: str):
        if not value or not value.strip():
            raise ValueError("Имя пользователя не может быть пустым")
        self._username = value.strip()

    @property
    def registration_date(self) -> datetime:
        return self._registration_date

    @registration_date.setter
    def registration_date(self, value: datetime):
        if not isinstance(value, datetime):
            raise TypeError("registration_date должен быть datetime")
        self._registration_date = value

    @property
    def hashed_password(self) -> str:
        return self._hashed_password

    @property
    def salt(self) -> str:
        return self._salt

    @staticmethod
    def _hash(password: str, salt: str) -> str:
        return hashlib.sha256((password + salt).encode("utf-8")).hexdigest()

    def get_user_info(self) -> str:
        """Возвращает информацию о пользователе без пароля."""
        return (
            f"ID: {self.user_id}\n"
            f"Имя: {self.username}\n"
            f"Дата регистрации: {self.registration_date.isoformat()}"
        )

    def change_password(self, new_password: str) -> None:
        """Меняет пароль с хешированием."""
        if len(new_password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов")
        self._salt = secrets.token_hex(8)
        self._hashed_password = self._hash(new_password, self._salt)

    def verify_password(self, password: str) -> bool:
        """Проверяет, совпадает ли пароль с сохранённым хешем."""
        return self._hash(password, self._salt) == self._hashed_password

    def to_dict(self) -> dict:
        """Объект → словарь."""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "hashed_password": self.hashed_password,
            "salt": self.salt,
            "registration_date": self.registration_date.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        """Словарь → объект."""
        return cls(
            user_id=data["user_id"],
            username=data["username"],
            hashed_password=data.get("hashed_password", ""),
            salt=data.get("salt", ""),
            registration_date=datetime.fromisoformat(data["registration_date"]),
        )


class Wallet:
    """Кошелёк пользователя для одной валюты."""

    def __init__(self, currency_code: str, balance: float = 0.0):
        self.currency_code = currency_code
        self.balance = balance

    @property
    def balance(self) -> float:
        return self._balance

    @balance.setter
    def balance(self, value: float):
        if not isinstance(value, (int, float)):
            raise TypeError("Баланс должен быть числом")
        if value < 0:
            raise ValueError("Баланс не может быть отрицательным")
        self._balance = value

    def deposit(self, amount: float) -> None:
        """Пополняет баланс."""
        if not isinstance(amount, (int, float)):
            raise TypeError("Сумма должна быть числом")
        if amount <= 0:
            raise ValueError("Сумма пополнения должна быть положительной")
        self.balance = self.balance + amount

    def withdraw(self, amount: float) -> None:
        """Снимает с баланса."""
        if not isinstance(amount, (int, float)):
            raise TypeError("Сумма должна быть числом")
        if amount <= 0:
            raise ValueError("Сумма снятия должна быть положительной")
        if amount > self.balance:
            raise InsufficientFundsError(
                f"Недостаточно средств: доступно {self.balance} "
                f"{self.currency_code}, требуется {amount} {self.currency_code}"
            )
        self.balance = self.balance - amount

    def get_balance_info(self) -> str:
        """Возвращает строку о балансе."""
        return f"{self.currency_code}: {self.balance}"

    def to_dict(self) -> dict:
        """Объект → словарь."""
        return {"currency_code": self.currency_code, "balance": self.balance}

    @classmethod
    def from_dict(cls, data: dict) -> "Wallet":
        """Словарь → объект."""
        return cls(data["currency_code"], data["balance"])


class Portfolio:
    """Портфель пользователя."""

    def __init__(self, user: User):
        self._user = user
        self._wallets: dict[str, Wallet] = {}

    @property
    def user(self) -> User:
        return self._user

    @property
    def user_id(self) -> int:
        return self._user.user_id

    @property
    def wallets(self) -> dict[str, Wallet]:
        return dict(self._wallets)

    def add_currency(self, currency_code: str) -> Wallet:
        """Добавляет кошелёк, если его ещё нет."""
        if currency_code not in self._wallets:
            self._wallets[currency_code] = Wallet(currency_code)
        return self._wallets[currency_code]

    def get_wallet(self, currency_code: str) -> Wallet | None:
        """Возвращает кошелёк или None."""
        return self._wallets.get(currency_code)

    def get_total_value(self, rates: dict, base_currency: str = "USD") -> float:
        """Считает стоимость всех кошельков по переданным курсам."""
        total = 0.0
        for code, wallet in self._wallets.items():
            if code in rates:
                total += wallet.balance * rates[code]
        base_rate = rates.get(base_currency, 1.0)
        return total / base_rate

    def to_dict(self) -> dict:
        """Объект → словарь (по формату portfolios.json)."""
        return {
            "user_id": self._user.user_id,
            "wallets": {
                code: {"balance": w.balance}
                for code, w in self._wallets.items()
            },
        }

    @classmethod
    def from_dict(cls, data: dict, user: User) -> "Portfolio":
        """Словарь → объект."""
        portfolio = cls(user)
        for code, w in data["wallets"].items():
            wallet = portfolio.add_currency(code)
            wallet.balance = w["balance"]
        return portfolio