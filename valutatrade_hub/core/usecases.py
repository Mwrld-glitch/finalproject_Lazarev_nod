"""Бизнес-логика: регистрация, вход, покупка/продажа, курсы."""

import json
import secrets
from datetime import datetime

from valutatrade_hub.core.currencies import get_currency
from valutatrade_hub.core.models import Portfolio, User
from valutatrade_hub.core.utils import DataStorage
from valutatrade_hub.decorators import log_action
from valutatrade_hub.infra.settings import SettingsLoader


def _rates():
    """Читает rates.json → {код: курс_к_USD}."""
    path = SettingsLoader().get("RATES_FILE")
    raw = json.loads(path.read_text(encoding="utf-8"))
    result = {"USD": 1.0}
    for key, value in raw.items():
        if isinstance(value, dict) and key.endswith("_USD"):
            result[key[:-4]] = value["rate"]
    return result


def _rate(code):
    """Возвращает курс валюты к USD."""
    return _rates()[code]


@log_action
def register(username, password):
    """Регистрирует нового пользователя."""
    users = DataStorage.load_users()
    if any(u.username == username for u in users):
        raise ValueError(f"Имя пользователя '{username}' уже занято")

    user_id = max((u.user_id for u in users), default=0) + 1
    salt = secrets.token_hex(8)
    user = User(user_id, username, "", salt, datetime.now())
    user.change_password(password)
    users.append(user)
    DataStorage.save_users(users)

    portfolios = DataStorage.load_portfolios()
    portfolios.append(Portfolio(user_id))
    DataStorage.save_portfolios(portfolios)

    return f"Пользователь '{username}' зарегистрирован (id={user_id})."


@log_action
def login(username, password):
    """Проверяет логин и пароль."""
    for u in DataStorage.load_users():
        if u.username == username:
            if not u.verify_password(password):
                raise ValueError("Неверный пароль")
            return u
    raise ValueError(f"Пользователь '{username}' не найден")


def _portfolio(user):
    """Возвращает портфель пользователя."""
    for p in DataStorage.load_portfolios():
        if p.user_id == user.user_id:
            p._user = user
            return p
    return Portfolio(user.user_id, user=user)


def _save_portfolio(portfolio):
    """Сохраняет портфель."""
    portfolios = DataStorage.load_portfolios()
    for i, p in enumerate(portfolios):
        if p.user_id == portfolio.user_id:
            portfolios[i] = portfolio
            break
    else:
        portfolios.append(portfolio)
    DataStorage.save_portfolios(portfolios)


def show_portfolio(user, base="USD"):
    """Возвращает портфель и итоговую стоимость."""
    get_currency(base)
    portfolio = _portfolio(user)
    return {
        "portfolio": portfolio,
        "base": base,
        "total": portfolio.get_total_value(_rates(), base),
    }


@log_action
def buy(user, currency, amount):
    """Покупка: списывает USD, зачисляет валюту."""
    currency = currency.upper()
    get_currency(currency)

    if currency == "USD":
        raise ValueError("Нельзя купить USD за USD")

    rate = _rate(currency)
    cost = amount * rate

    portfolio = _portfolio(user)
    usd = portfolio.add_currency("USD")
    usd.withdraw(cost)

    target = portfolio.add_currency(currency)
    before = target.balance
    target.deposit(amount)
    _save_portfolio(portfolio)

    return {
        "currency": currency,
        "amount": amount,
        "before": before,
        "after": target.balance,
        "rate": rate,
        "cost": cost,
    }


@log_action
def sell(user, currency, amount):
    """Продажа: списывает валюту, зачисляет USD."""
    currency = currency.upper()
    get_currency(currency)

    if currency == "USD":
        raise ValueError("Нельзя продать USD за USD")

    rate = _rate(currency)

    portfolio = _portfolio(user)
    target = portfolio.get_wallet(currency)
    if target is None:
        raise ValueError(f"У вас нет кошелька '{currency}'")

    before = target.balance
    target.withdraw(amount)

    usd = portfolio.add_currency("USD")
    usd.deposit(amount * rate)
    _save_portfolio(portfolio)

    return {
        "currency": currency,
        "amount": amount,
        "before": before,
        "after": target.balance,
        "rate": rate,
        "revenue": amount * rate,
    }


def get_rate(from_code, to_code):
    """Возвращает курс между двумя валютами."""
    from_code = from_code.upper()
    to_code = to_code.upper()
    get_currency(from_code)
    get_currency(to_code)
    return {
        "from": from_code,
        "to": to_code,
        "rate": _rate(from_code) / _rate(to_code),
        "reverse": _rate(to_code) / _rate(from_code),
    }