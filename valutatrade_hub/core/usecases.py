import json
import secrets
from datetime import datetime
from pathlib import Path

from valutatrade_hub.core.models import Portfolio, User

DATA_DIR = Path("data")
USERS_FILE = DATA_DIR / "users.json"
PORTFOLIOS_FILE = DATA_DIR / "portfolios.json"

STUB_RATES = {
    "USD": 1.0,
    "EUR": 1.08,
    "RUB": 0.010,
    "BTC": 59337.21,
    "ETH": 3720.00,
    "SOL": 145.12,
}


def _load_json(path: Path) -> list:
    """Читает JSON-файл, возвращает пустой список, если файла нет."""
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        content = f.read().strip()
        if not content:
            return []
        return json.loads(content)


def _save_json(path: Path, data) -> None:
    """Записывает данные в JSON-файл."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _load_users() -> list[User]:
    """Читает users.json и возвращает список объектов User."""
    return [User.from_dict(u) for u in _load_json(USERS_FILE)]


def _save_users(users: list[User]) -> None:
    """Сохраняет список объектов User в users.json."""
    _save_json(USERS_FILE, [u.to_dict() for u in users])


def _load_portfolio(user: User) -> Portfolio:
    """Загружает портфель пользователя или создаёт пустой."""
    for item in _load_json(PORTFOLIOS_FILE):
        if item["user_id"] == user.user_id:
            return Portfolio.from_dict(item, user)
    return Portfolio(user)


def _save_portfolio(portfolio: Portfolio) -> None:
    """Сохраняет портфель в portfolios.json (обновляет или добавляет)."""
    raw = _load_json(PORTFOLIOS_FILE)
    new_item = portfolio.to_dict()
    for i, item in enumerate(raw):
        if item["user_id"] == portfolio.user_id:
            raw[i] = new_item
            break
    else:
        raw.append(new_item)
    _save_json(PORTFOLIOS_FILE, raw)


def register(username: str, password: str) -> str:
    """Регистрирует нового пользователя и создаёт пустой портфель."""
    if not username or not username.strip():
        raise ValueError("Имя пользователя не может быть пустым")

    users = _load_users()
    if any(u.username == username for u in users):
        raise ValueError(f"Имя пользователя '{username}' уже занято")

    user_id = max((u.user_id for u in users), default=0) + 1
    salt = secrets.token_hex(8)
    user = User(user_id, username, "", salt, datetime.now())
    user.change_password(password)
    users.append(user)
    _save_users(users)

    _save_portfolio(Portfolio(user))

    return f"Пользователь '{username}' зарегистрирован (id={user_id})."


def login(username: str, password: str) -> User:
    """Находит пользователя и проверяет пароль. Возвращает объект User."""
    users = _load_users()
    user = next((u for u in users if u.username == username), None)
    if user is None:
        raise ValueError(f"Пользователь '{username}' не найден")
    if not user.verify_password(password):
        raise ValueError("Неверный пароль")
    return user


def show_portfolio(user: User, base: str = "USD") -> dict:
    """Возвращает портфель и итоговую стоимость в базовой валюте."""
    if base not in STUB_RATES:
        raise ValueError(f"Неизвестная базовая валюта '{base}'")
    portfolio = _load_portfolio(user)
    return {
        "portfolio": portfolio,
        "base": base,
        "total": portfolio.get_total_value(base),
    }


def buy(user: User, currency: str, amount: float) -> dict:
    """Покупает валюту: увеличивает баланс кошелька."""
    currency = currency.upper()
    if currency not in STUB_RATES:
        raise ValueError(f"Неизвестная валюта '{currency}'")
    if not isinstance(amount, (int, float)):
        raise ValueError("'amount' должен быть числом")
    if amount <= 0:
        raise ValueError("'amount' должен быть положительным числом")

    portfolio = _load_portfolio(user)
    wallet = portfolio.add_currency(currency)
    before = wallet.balance
    wallet.deposit(amount)
    _save_portfolio(portfolio)

    rate = STUB_RATES[currency]
    return {
        "currency": currency,
        "amount": amount,
        "before": before,
        "after": wallet.balance,
        "rate": rate,
        "cost": amount * rate,
    }


def sell(user: User, currency: str, amount: float) -> dict:
    """Продаёт валюту: уменьшает баланс кошелька."""
    currency = currency.upper()
    if not isinstance(amount, (int, float)):
        raise ValueError("'amount' должен быть числом")
    if amount <= 0:
        raise ValueError("'amount' должен быть положительным числом")

    portfolio = _load_portfolio(user)
    wallet = portfolio.get_wallet(currency)
    if wallet is None:
        raise ValueError(f"У вас нет кошелька '{currency}'")

    before = wallet.balance
    wallet.withdraw(amount)
    _save_portfolio(portfolio)

    rate = STUB_RATES.get(currency, 0.0)
    return {
        "currency": currency,
        "amount": amount,
        "before": before,
        "after": wallet.balance,
        "rate": rate,
        "revenue": amount * rate,
    }


def get_rate(from_code: str, to_code: str) -> dict:
    """Возвращает курс из одной валюты в другую (по заглушке)."""
    from_code = from_code.upper()
    to_code = to_code.upper()
    if from_code not in STUB_RATES:
        raise ValueError(f"Неизвестная валюта '{from_code}'")
    if to_code not in STUB_RATES:
        raise ValueError(f"Неизвестная валюта '{to_code}'")

    return {
        "from": from_code,
        "to": to_code,
        "rate": STUB_RATES[from_code] / STUB_RATES[to_code],
        "reverse": STUB_RATES[to_code] / STUB_RATES[from_code],
    }