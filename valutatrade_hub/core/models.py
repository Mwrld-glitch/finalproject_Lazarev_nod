"""Модели данных системы ValutaTrade Hub."""

import hashlib
from datetime import datetime
from typing import Dict, Optional

from valutatrade_hub.core.exceptions import InsufficientFundsError


class User:
    """Класс пользователя системы."""

    def __init__(
        self,
        user_id: int,
        username: str,
        hashed_password: str,
        salt: str,
        registration_date: datetime,
    ):
        self._user_id = user_id
        self.username = username
        self._hashed_password = hashed_password
        self._salt = salt
        self._registration_date = registration_date

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def username(self) -> str:
        return self._username

    @username.setter
    def username(self, value: str):
        if not value or not value.strip():
            raise ValueError("Имя пользователя не может быть пустым.")
        self._username = value.strip()

    @property
    def hashed_password(self) -> str:
        return self._hashed_password

    @property
    def salt(self) -> str:
        return self._salt

    @property
    def registration_date(self) -> datetime:
        return self._registration_date

    @staticmethod
    def _hash_password(password: str, salt: str) -> str:
        return hashlib.sha256((password + salt).encode("utf-8")).hexdigest()

    def get_user_info(self) -> str:
        """Выводит информацию о пользователе (без пароля)."""
        return (
            f"ID: {self._user_id} | "
            f"Имя: {self._username} | "
            f"Дата регистрации: "
            f"{self._registration_date.strftime('%Y-%m-%d %H:%M:%S')}"
        )

    def change_password(self, new_password: str):
        """Изменяет пароль пользователя с хешированием."""
        if len(new_password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов.")
        self._hashed_password = self._hash_password(new_password, self._salt)

    def verify_password(self, password: str) -> bool:
        """Проверяет введённый пароль на совпадение."""
        return self._hash_password(password, self._salt) == self._hashed_password

    def to_dict(self) -> dict:
        """Сериализация в словарь."""
        return {
            "user_id": self._user_id,
            "username": self._username,
            "hashed_password": self._hashed_password,
            "salt": self._salt,
            "registration_date": self._registration_date.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        """Десериализация из словаря."""
        return cls(
            data["user_id"],
            data["username"],
            data["hashed_password"],
            data["salt"],
            datetime.fromisoformat(data["registration_date"]),
        )

class Wallet:
    """Класс кошелька пользователя для одной конкретной валюты."""

    def __init__(self, currency_code: str, balance: float = 0.0):
        self.currency_code = currency_code
        self.balance = balance

    @property
    def balance(self) -> float:
        return self._balance

    @balance.setter
    def balance(self, value: float):
        if not isinstance(value, (int, float)):
            raise TypeError("Баланс должен быть числом (int или float).")
        if value < 0:
            raise ValueError("Баланс не может быть отрицательным.")
        self._balance = float(value)

    def deposit(self, amount: float):
        """Пополнение баланса."""
        if not isinstance(amount, (int, float)) or amount <= 0:
            raise ValueError("Сумма пополнения должна быть положительным числом.")
        self.balance += amount

    def withdraw(self, amount: float):
        """Снятие средств."""
        if not isinstance(amount, (int, float)) or amount <= 0:
            raise ValueError("Сумма снятия должна быть положительным числом.")
        if amount > self.balance:
            raise InsufficientFundsError(
                f"Недостаточно средств: доступно {self.balance} "
                f"{self.currency_code}, требуется {amount} {self.currency_code}"
            )
        self.balance -= amount

    def get_balance_info(self) -> str:
        """Вывод информации о текущем балансе."""
        return f"Кошелёк {self.currency_code}: {self.balance:.2f}"

    def to_dict(self) -> dict:
        """Сериализация кошелька в словарь."""
        return {
            "currency_code": self.currency_code,
            "balance": self._balance
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Wallet':
        """Десериализация из словаря в объект."""
        return cls(
            currency_code=data["currency_code"],
            balance=data["balance"]
        )


class Portfolio:
    """Класс управления всеми кошельками одного пользователя."""

    def __init__(
        self,
        user_id: int,
        wallets: Optional[Dict[str, Wallet]] = None,
        user: Optional[User] = None,
    ):
        self._user_id = user_id
        self._wallets = wallets if wallets is not None else {}
        self._user = user

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def user(self) -> Optional[User]:
        """Геттер, возвращающий объект пользователя."""
        return self._user

    @property
    def wallets(self) -> Dict[str, Wallet]:
        """Геттер, возвращающий копию словаря кошельков."""
        return self._wallets.copy()

    def add_currency(self, currency_code: str):
        """Добавляет кошелёк, если его ещё нет, и возвращает его."""
        if currency_code not in self._wallets:
            self._wallets[currency_code] = Wallet(currency_code)
        return self._wallets[currency_code]

    def get_wallet(self, currency_code: str) -> Optional[Wallet]:
        """Возвращает объект Wallet по коду валюты."""
        return self._wallets.get(currency_code)

    def get_total_value(self, rates: dict, base_currency: str = "USD") -> float:
        """Возвращает общую стоимость всех валют в базовой валюте.

        Курсы передаются извне (например, из rates.json).
        """
        if base_currency not in rates:
            raise ValueError(
                f"Курс для базовой валюты {base_currency} не задан в системе."
            )

        total_in_usd = 0.0
        for code, wallet in self._wallets.items():
            if code not in rates:
                raise ValueError(f"Курс для валюты {code} не задан в системе.")
            total_in_usd += wallet.balance * rates[code]

        base_rate = rates[base_currency]
        return total_in_usd / base_rate

    def to_dict(self) -> dict:
        """Сериализация портфеля в словарь."""
        return {
            "user_id": self._user_id,
            "wallets": {
                code: wallet.to_dict()
                for code, wallet in self._wallets.items()
            }
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Portfolio":
        """Десериализация из словаря в объект."""
        wallets = {
            code: Wallet.from_dict(wallet_data)
            for code, wallet_data in data["wallets"].items()
        }
        return cls(
            user_id=data["user_id"],
            wallets=wallets
        )


