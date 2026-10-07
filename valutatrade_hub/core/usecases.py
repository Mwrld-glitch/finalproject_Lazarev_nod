"""Бизнес-логика: регистрация, вход, покупка/продажа, курсы."""

import secrets
from datetime import datetime

from valutatrade_hub.core.exceptions import (
    CurrencyNotFoundError,
)
from valutatrade_hub.core.models import Portfolio, User
from valutatrade_hub.core.utils import read, write


def _rates() -> dict:
    """Читает rates.json и возвращает {код: курс_к_USD}."""
    raw = read("rates.json")
    result = {"USD": 1.0}
    for key, value in raw.items():
        if isinstance(value, dict) and key.endswith("_USD"):
            result[key[:-4]] = value["rate"]
    return result


def _rate(code: str) -> float:
    """Возвращает курс валюты к USD или кидает CurrencyNotFoundError."""
    rates = _rates()
    if code not in rates:
        raise CurrencyNotFoundError(f"Неизвестная валюта '{code}'")
    return rates[code]


def _portfolio(user: User) -> Portfolio:
    """Читает портфель пользователя из portfolios.json."""
    for item in read("portfolios.json"):
        if item["user_id"] == user.user_id:
            return Portfolio.from_dict(item, user)
    return Portfolio(user)


def _save_portfolio(portfolio: Portfolio) -> None:
    """Сохраняет портфель в portfolios.json."""
    raw = read("portfolios.json")
    data = portfolio.to_dict()
    for i, item in enumerate(raw):
        if item["user_id"] == portfolio.user_id:
            raw[i] = data
            break
    else:
        raw.append(data)
    write("portfolios.json", raw)


def register(username: str, password: str) -> str:
    """Регистрирует нового пользователя и создаёт пустой портфель."""
    users = [User.from_dict(u) for u in read("users.json")]
    if any(u.username == username for u in users):
        raise ValueError(f"Имя пользователя '{username}' уже занято")

    user_id = max((u.user_id for u in users), default=0) + 1
    user = User(user_id, username, "", secrets.token_hex(8), datetime.now())
    user.change_password(password)
    users.append(user)
    write("users.json", [u.to_dict() for u in users])

    raw = read("portfolios.json")
    raw.append({"user_id": user_id, "wallets": {}})
    write("portfolios.json", raw)

    return f"Пользователь '{username}' зарегистрирован (id={user_id})."


def login(username: str, password: str) -> User:
    """Проверяет логин и пароль, возвращает User."""
    users = [User.from_dict(u) for u in read("users.json")]
    user = next((u for u in users if u.username == username), None)
    if user is None:
        raise ValueError(f"Пользователь '{username}' не найден")
    if not user.verify_password(password):
        raise ValueError("Неверный пароль")
    return user


def show_portfolio(user: User, base: str = "USD") -> dict:
    """Показать все кошельки и итоговую стоимость в базовой валюте."""
    _rate(base)
    portfolio = _portfolio(user)
    return {
        "portfolio": portfolio,
        "base": base,
        "total": portfolio.get_total_value(_rates(), base),
    }


def buy(user: User, currency: str, amount: float) -> dict:
    """Покупает валюту."""
    currency = currency.upper()
    rate = _rate(currency)

    portfolio = _portfolio(user)
    wallet = portfolio.add_currency(currency)
    before = wallet.balance
    wallet.deposit(amount)
    _save_portfolio(portfolio)

    return {
        "currency": currency,
        "amount": amount,
        "before": before,
        "after": wallet.balance,
        "rate": rate,
        "cost": amount * rate,
    }


def sell(user: User, currency: str, amount: float) -> dict:
    """Продаёт валюту."""
    currency = currency.upper()

    portfolio = _portfolio(user)
    wallet = portfolio.get_wallet(currency)
    if wallet is None:
        raise CurrencyNotFoundError(f"У вас нет кошелька '{currency}'")

    before = wallet.balance
    wallet.withdraw(amount)
    _save_portfolio(portfolio)

    rate = _rate(currency)
    return {
        "currency": currency,
        "amount": amount,
        "before": before,
        "after": wallet.balance,
        "rate": rate,
        "revenue": amount * rate,
    }


def get_rate(from_code: str, to_code: str) -> dict:
    """Возвращает курс между двумя валютами."""
    from_code = from_code.upper()
    to_code = to_code.upper()
    return {
        "from": from_code,
        "to": to_code,
        "rate": _rate(from_code) / _rate(to_code),
        "reverse": _rate(to_code) / _rate(from_code),
    }