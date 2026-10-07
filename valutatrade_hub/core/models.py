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