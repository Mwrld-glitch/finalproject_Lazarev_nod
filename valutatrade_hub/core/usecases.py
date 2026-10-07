"""Бизнес-логика: регистрация, вход, покупка/продажа, курсы."""

import json
from pathlib import Path

from valutatrade_hub.core.exceptions import CurrencyNotFoundError
from valutatrade_hub.core.models import Portfolio, User

USERS_FILE = Path("data/users.json")
PORTFOLIOS_FILE = Path("data/portfolios.json")
RATES_FILE = Path("data/rates.json")


def _read(path):
    """Читает JSON-файл."""
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path, data):
    """Пишет JSON-файл."""
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _rates():
    """Читает rates.json → {код: курс_к_USD}."""
    raw = _read(RATES_FILE)
    result = {"USD": 1.0}
    for key, value in raw.items():
        if isinstance(value, dict) and key.endswith("_USD"):
            result[key[:-4]] = value["rate"]
    return result


def _rate(code):
    """Возвращает курс валюты к USD."""
    rates = _rates()
    if code not in rates:
        raise CurrencyNotFoundError(f"Неизвестная валюта '{code}'")
    return rates[code]


def _portfolio(user):
    """Читает портфель пользователя."""
    for item in _read(PORTFOLIOS_FILE):
        if item["user_id"] == user.user_id:
            return Portfolio.from_dict(item, user)
    return Portfolio(user)


def _save_portfolio(portfolio):
    """Пишет портфель в portfolios.json."""
    raw = _read(PORTFOLIOS_FILE)
    data = portfolio.to_dict()
    for i, item in enumerate(raw):
        if item["user_id"] == portfolio.user_id:
            raw[i] = data
            break
    else:
        raw.append(data)
    _write(PORTFOLIOS_FILE, raw)


def register(username, password):
    """Регистрирует нового пользователя."""
    users = [User.from_dict(u) for u in _read(USERS_FILE)]
    if any(u.username == username for u in users):
        raise ValueError(f"Имя пользователя '{username}' уже занято")

    user_id = max((u.user_id for u in users), default=0) + 1
    user = User(user_id, username)
    user.change_password(password)
    users.append(user)
    _write(USERS_FILE, [u.to_dict() for u in users])

    raw = _read(PORTFOLIOS_FILE)
    raw.append({"user_id": user_id, "wallets": {}})
    _write(PORTFOLIOS_FILE, raw)

    return f"Пользователь '{username}' зарегистрирован (id={user_id})."


def login(username, password):
    """Проверяет логин и пароль."""
    users = [User.from_dict(u) for u in _read(USERS_FILE)]
    user = next((u for u in users if u.username == username), None)
    if user is None:
        raise ValueError(f"Пользователь '{username}' не найден")
    if not user.verify_password(password):
        raise ValueError("Неверный пароль")
    return user


def show_portfolio(user, base="USD"):
    """Возвращает портфель и итоговую стоимость."""
    _rate(base)
    portfolio = _portfolio(user)
    return {
        "portfolio": portfolio,
        "base": base,
        "total": portfolio.get_total_value(_rates(), base),
    }


def buy(user, currency, amount):
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


def sell(user, currency, amount):
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


def get_rate(from_code, to_code):
    """Возвращает курс между двумя валютами."""
    from_code = from_code.upper()
    to_code = to_code.upper()
    return {
        "from": from_code,
        "to": to_code,
        "rate": _rate(from_code) / _rate(to_code),
        "reverse": _rate(to_code) / _rate(from_code),
    }