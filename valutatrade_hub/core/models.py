import hashlib
from datetime import datetime


class User:
    """Пользователь системы."""

    def __init__(
        self,
        user_id: int,
        username: str,
        hashed_password: str,
        salt: str,
        registration_date,
    ) -> None:
        """Создаёт пользователя."""
        self._user_id = user_id
        self._username = username
        self._hashed_password = hashed_password
        self._salt = salt
        self._registration_date = registration_date

    @property
    def user_id(self) -> int:
        """Возвращает ID пользователя."""
        return self._user_id

    @property
    def username(self) -> str:
        """Возвращает имя пользователя."""
        return self._username

    @property
    def hashed_password(self) -> str:
        """Возвращает хеш пароля."""
        return self._hashed_password

    @property
    def salt(self) -> str:
        """Возвращает соль."""
        return self._salt

    @property
    def registration_date(self):
        """Возвращает дату регистрации."""
        return self._registration_date

    @username.setter
    def username(self, value: str) -> None:
        """Устанавливает имя, запрещая пустое значение."""
        if not value or not value.strip():
            raise ValueError("Имя пользователя не может быть пустым")
        self._username = value

    def get_user_info(self) -> str:
        """Возвращает информацию о пользователе без пароля."""
        return (
            f"Пользователь: {self._username} (id={self._user_id}), "
            f"зарегистрирован: {self._registration_date.isoformat()}"
        )

    def change_password(self, new_password: str) -> None:
        """Меняет пароль с хешированием (не короче 4 символов)."""
        if len(new_password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов")
        self._hashed_password = hashlib.sha256(
            (new_password + self._salt).encode()
        ).hexdigest()

    def verify_password(self, password: str) -> bool:
        """Проверяет, совпадает ли пароль с сохранённым хешем."""
        hashed = hashlib.sha256((password + self._salt).encode()).hexdigest()
        return hashed == self._hashed_password

    def to_dict(self) -> dict:
        """Превращает объект в словарь для JSON."""
        return {
            "user_id": self._user_id,
            "username": self._username,
            "hashed_password": self._hashed_password,
            "salt": self._salt,
            "registration_date": self._registration_date.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        """Создаёт объект User из словаря."""
        return cls(
            data["user_id"],
            data["username"],
            data["hashed_password"],
            data["salt"],
            datetime.fromisoformat(data["registration_date"]),
        )

class Wallet:
    """Кошелёк пользователя для одной валюты."""

    def __init__(self, currency_code: str, balance: float = 0.0) -> None:
        """Создаёт кошелёк с указанной валютой и балансом."""
        self.currency_code = currency_code
        self._balance = balance

    @property
    def balance(self) -> float:
        """Возвращает текущий баланс."""
        return self._balance

    @balance.setter
    def balance(self, value: float) -> None:
        """Устанавливает баланс, запрещая отрицательные и нечисловые значения."""
        if not isinstance(value, (int, float)):
            raise TypeError("Баланс должен быть числом")
        if value < 0:
            raise ValueError("Баланс не может быть отрицательным")
        self._balance = value

    def deposit(self, amount: float) -> None:
        """Пополняет баланс на указанную сумму."""
        if not isinstance(amount, (int, float)):
            raise TypeError("Сумма должна быть числом")
        if amount <= 0:
            raise ValueError("Сумма пополнения должна быть положительной")
        self.balance = self._balance + amount

    def withdraw(self, amount: float) -> None:
        """Снимает указанную сумму, если баланс позволяет."""
        if not isinstance(amount, (int, float)):
            raise TypeError("Сумма должна быть числом")
        if amount <= 0:
            raise ValueError("Сумма снятия должна быть положительной")
        if amount > self._balance:
            raise ValueError(
                f"Недостаточно средств: доступно {self._balance}, "
                f"требуется {amount}"
            )
        self.balance = self._balance - amount

    def get_balance_info(self) -> str:
        """Возвращает строку с информацией о балансе."""
        return f"{self.currency_code}: {self._balance}"

    def to_dict(self) -> dict:
        """Превращает объект в словарь для JSON."""
        return {
            "currency_code": self.currency_code,
            "balance": self._balance,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Wallet":
        """Создаёт объект Wallet из словаря."""
        return cls(data["currency_code"], data["balance"])

class Portfolio:
    """Портфель пользователя: набор кошельков по валютам."""

    def __init__(self, user) -> None:
        """Создаёт портфель для указанного пользователя."""
        self._user = user
        self._wallets: dict[str, Wallet] = {}

    @property
    def user(self):
        """Возвращает объект пользователя (только для чтения)."""
        return self._user

    @property
    def user_id(self) -> int:
        """Возвращает ID пользователя."""
        return self._user.user_id

    @property
    def wallets(self) -> dict[str, Wallet]:
        """Возвращает копию словаря кошельков."""
        return dict(self._wallets)

    def add_currency(self, currency_code: str) -> Wallet:
        """Добавляет кошелёк, если его ещё нет, и возвращает его."""
        if currency_code not in self._wallets:
            self._wallets[currency_code] = Wallet(currency_code)
        return self._wallets[currency_code]

    def get_wallet(self, currency_code: str) -> Wallet | None:
        """Возвращает кошелёк по коду валюты или None."""
        return self._wallets.get(currency_code)

    def get_total_value(self, base_currency: str = "USD") -> float:
        """Считает общую стоимость всех кошельков в базовой валюте."""
        exchange_rates = {
            "USD": 1.0,
            "EUR": 1.08,
            "RUB": 0.010,
            "BTC": 59337.21,
            "ETH": 3720.00,
            "SOL": 145.12,
        }
        total = 0.0
        for code, wallet in self._wallets.items():
            if code == base_currency:
                total += wallet.balance
                continue
            rate = exchange_rates.get(code)
            if rate is None:
                continue
            total += wallet.balance * rate
        return total

    def to_dict(self) -> dict:
        """Превращает объект в словарь для JSON."""
        return {
            "user_id": self._user.user_id,
            "wallets": {
                code: {"balance": w.balance}
                for code, w in self._wallets.items()
            },
        }

    @classmethod
    def from_dict(cls, data: dict, user) -> "Portfolio":
        """Создаёт объект Portfolio из словаря и объекта User."""
        portfolio = cls(user)
        for code, w in data["wallets"].items():
            wallet = portfolio.add_currency(code)
            wallet.balance = w["balance"]
        return portfolio