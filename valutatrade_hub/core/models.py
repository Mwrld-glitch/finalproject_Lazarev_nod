"""Модели данных: User, Wallet, Portfolio."""

import hashlib
from datetime import datetime

from valutatrade_hub.core.exceptions import InsufficientFundsError


class User:
    """Пользователь системы."""

    def __init__(self, user_id, username, hashed_password, salt, registration_date):
        """Создаёт пользователя."""
        self._user_id = user_id
        self._username = username
        self._hashed_password = hashed_password
        self._salt = salt
        self._registration_date = registration_date

    @property
    def user_id(self):
        """Возвращает ID."""
        return self._user_id

    @property
    def username(self):
        """Возвращает имя."""
        return self._username

    @property
    def hashed_password(self):
        """Возвращает хеш пароля."""
        return self._hashed_password

    @property
    def salt(self):
        """Возвращает соль."""
        return self._salt

    @property
    def registration_date(self):
        """Возвращает дату регистрации."""
        return self._registration_date

    @username.setter
    def username(self, value):
        """Устанавливает имя с проверкой."""
        if not value or not value.strip():
            raise ValueError("Имя пользователя не может быть пустым")
        self._username = value

    def change_password(self, new_password):
        """Меняет пароль с хешированием."""
        if len(new_password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов")
        self._hashed_password = hashlib.sha256(
            (new_password + self._salt).encode()
        ).hexdigest()

    def verify_password(self, password):
        """Проверяет пароль по хешу."""
        hashed = hashlib.sha256((password + self._salt).encode()).hexdigest()
        return hashed == self._hashed_password

    def get_user_info(self):
        """Возвращает информацию без пароля."""
        return (
            f"Пользователь: {self._username} (id={self._user_id}), "
            f"зарегистрирован: {self._registration_date.isoformat()}"
        )

    def to_dict(self):
        """Объект → словарь."""
        return {
            "user_id": self._user_id,
            "username": self._username,
            "hashed_password": self._hashed_password,
            "salt": self._salt,
            "registration_date": self._registration_date.isoformat(),
        }

    @classmethod
    def from_dict(cls, data):
        """Словарь → объект."""
        return cls(
            data["user_id"],
            data["username"],
            data["hashed_password"],
            data["salt"],
            datetime.fromisoformat(data["registration_date"]),
        )


class Wallet:
    """Кошелёк для одной валюты."""

    def __init__(self, currency_code, balance=0.0):
        """Создаёт кошелёк."""
        self.currency_code = currency_code
        self._balance = balance

    @property
    def balance(self):
        """Возвращает баланс."""
        return self._balance

    @balance.setter
    def balance(self, value):
        """Устанавливает баланс с проверкой."""
        if not isinstance(value, (int, float)):
            raise TypeError("Баланс должен быть числом")
        if value < 0:
            raise ValueError("Баланс не может быть отрицательным")
        self._balance = value

    def deposit(self, amount):
        """Пополняет баланс."""
        if not isinstance(amount, (int, float)):
            raise TypeError("Сумма должна быть числом")
        if amount <= 0:
            raise ValueError("Сумма пополнения должна быть положительной")
        self._balance += amount

    def withdraw(self, amount):
        """Снимает с баланса."""
        if not isinstance(amount, (int, float)):
            raise TypeError("Сумма должна быть числом")
        if amount <= 0:
            raise ValueError("Сумма снятия должна быть положительной")
        if amount > self._balance:
            raise InsufficientFundsError(
                f"Недостаточно средств: доступно {self._balance} "
                f"{self.currency_code}, требуется {amount} {self.currency_code}"
            )
        self._balance -= amount

    def get_balance_info(self):
        """Возвращает строку о балансе."""
        return f"{self.currency_code}: {self._balance}"

    def to_dict(self):
        """Объект → словарь."""
        return {"currency_code": self.currency_code, "balance": self._balance}

    @classmethod
    def from_dict(cls, data):
        """Словарь → объект."""
        return cls(data["currency_code"], data["balance"])


class Portfolio:
    """Портфель пользователя."""

    def __init__(self, user):
        """Создаёт портфель для пользователя."""
        self._user = user
        self._wallets = {}

    @property
    def user(self):
        """Возвращает пользователя."""
        return self._user

    @property
    def user_id(self):
        """Возвращает ID пользователя."""
        return self._user.user_id

    @property
    def wallets(self):
        """Возвращает копию словаря кошельков."""
        return dict(self._wallets)

    def add_currency(self, currency_code):
        """Добавляет кошелёк, если его нет. Возвращает кошелёк."""
        if currency_code not in self._wallets:
            self._wallets[currency_code] = Wallet(currency_code)
        return self._wallets[currency_code]

    def get_wallet(self, currency_code):
        """Возвращает кошелёк или None."""
        return self._wallets.get(currency_code)

    def get_total_value(self, rates, base_currency="USD"):
        """Считает стоимость всех кошельков по переданным курсам."""
        total = 0.0
        for code, wallet in self._wallets.items():
            if code in rates:
                total += wallet.balance * rates[code]
        base_rate = rates.get(base_currency, 1.0)
        return total / base_rate

    def to_dict(self):
        """Объект → словарь."""
        return {
            "user_id": self._user.user_id,
            "wallets": {c: w.to_dict() for c, w in self._wallets.items()},
        }

    @classmethod
    def from_dict(cls, data, user):
        """Словарь → объект."""
        portfolio = cls(user)
        for code, w in data["wallets"].items():
            wallet = portfolio.add_currency(code)
            wallet.balance = w["balance"]
        return portfolio