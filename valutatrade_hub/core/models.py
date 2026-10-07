import hashlib


class User:
    """Пользователь системы.

    Хранит данные пользователя, хеш пароля с солью и дату регистрации.
    """

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

    @property
    def password(self) -> str:
        """Возвращает хеш пароля (для чтения)."""
        return self._hashed_password

    @username.setter
    def username(self, value: str) -> None:
        """Устанавливает имя, запрещая пустое значение."""
        if not value or not value.strip():
            raise ValueError("Имя пользователя не может быть пустым")
        self._username = value

    @password.setter
    def password(self, new_password: str) -> None:
        """Устанавливает новый пароль (не короче 4 символов)."""
        if len(new_password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов")
        self._hashed_password = self._hash_password(new_password)

    def get_user_info(self) -> str:
        """Возвращает информацию о пользователе без пароля."""
        return (
            f"Пользователь: {self._username} (id={self._user_id}), "
            f"зарегистрирован: {self._registration_date.isoformat()}"
        )

    def change_password(self, new_password: str) -> None:
        """Меняет пароль пользователя с хешированием."""
        self.password = new_password

    def verify_password(self, password: str) -> bool:
        """Проверяет, совпадает ли пароль с сохранённым хешем."""
        return self._hash_password(password) == self._hashed_password

    def _hash_password(self, password: str) -> str:
        """Считает sha256-хеш от пароля с солью."""
        return hashlib.sha256((password + self._salt).encode()).hexdigest()

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
        """ Делает баланс, запрещая отрицательные и нечисловые значения."""
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

