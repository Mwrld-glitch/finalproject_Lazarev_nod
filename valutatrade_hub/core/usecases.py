"""Бизнес-логика: регистрация, вход, покупка/продажа, курсы."""

import secrets
from datetime import datetime, timezone

from valutatrade_hub.core.currencies import get_currency
from valutatrade_hub.core.exceptions import (
    ApiRequestError,
    InsufficientFundsError,
)
from valutatrade_hub.core.models import Portfolio, User
from valutatrade_hub.core.utils import convert
from valutatrade_hub.decorators import log_action
from valutatrade_hub.infra.database import DatabaseManager
from valutatrade_hub.infra.settings import SettingsLoader


def _load_user(user_id: int) -> User:
    """Возвращает User по id или бросает ValueError."""
    for u in DatabaseManager().load_users():
        if u.user_id == user_id:
            return u
    raise ValueError(f"Пользователь с id={user_id} не найден")


def _rates() -> dict:
    """Плоский словарь {код: курс_к_USD} из rates.json."""
    return DatabaseManager().load_rates_map()


def _rate(code: str) -> float:
    """Курс к USD. Бросает CurrencyNotFoundError, если валюты нет."""
    get_currency(code)
    rates = _rates()
    if code not in rates:
        raise ApiRequestError(f"Курс {code}->USD недоступен")
    return rates[code]


def _is_stale() -> bool:
    """Проверяет свежесть кэша по TTL."""
    raw = DatabaseManager().load_rates()
    last = raw.get("last_refresh")
    if not last:
        return True
    ttl = SettingsLoader().get("RATES_TTL_SECONDS", 300)
    try:
        last_dt = datetime.fromisoformat(last)
    except ValueError:
        return True
    if last_dt.tzinfo is None:
        last_dt = last_dt.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - last_dt).total_seconds() > ttl


def _try_refresh() -> bool:
    """Пробует обновить курсы через Parser Service. True — если успешно."""
    try:
        from valutatrade_hub.parser_service.updater import RatesUpdater
        RatesUpdater().run_update()
        return True
    except Exception:
        return False


def _validate_amount(amount) -> float:
    """Проверяет, что amount — положительное число."""
    try:
        value = float(amount)
    except (TypeError, ValueError):
        raise ValueError("'amount' должен быть числом")
    if value <= 0:
        raise ValueError("'amount' должен быть положительным числом")
    return value


@log_action
def register(username: str, password: str) -> str:
    """Регистрирует нового пользователя."""
    db = DatabaseManager()
    users = db.load_users()
    if any(u.username == username for u in users):
        raise ValueError(f"Имя пользователя '{username}' уже занято")

    user_id = max((u.user_id for u in users), default=0) + 1
    salt = secrets.token_hex(8)
    user = User(user_id, username, "", salt, datetime.now())
    user.change_password(password)
    users.append(user)
    db.save_users(users)

    portfolios = db.load_portfolios()
    portfolios.append(Portfolio(user_id))
    db.save_portfolios(portfolios)

    return (
        f"Пользователь '{username}' зарегистрирован (id={user_id}). "
        f"Войдите: login --username {username} --password ****"
    )


@log_action
def login(username: str, password: str) -> User:
    """Проверяет логин и пароль, возвращает User."""
    for u in DatabaseManager().load_users():
        if u.username == username:
            if not u.verify_password(password):
                raise ValueError("Неверный пароль")
            return u
    raise ValueError(f"Пользователь '{username}' не найден")


def _load_portfolio(user: User) -> Portfolio:
    """Возвращает портфель пользователя, привязывая объект User."""
    for p in DatabaseManager().load_portfolios():
        if p.user_id == user.user_id:
            return Portfolio(user_id=p.user_id, wallets=p.wallets, user=user)
    return Portfolio(user.user_id, user=user)


def _save_portfolio(portfolio: Portfolio) -> None:
    """Сохраняет портфель (замена или добавление)."""
    db = DatabaseManager()
    portfolios = db.load_portfolios()
    for i, p in enumerate(portfolios):
        if p.user_id == portfolio.user_id:
            portfolios[i] = portfolio
            break
    else:
        portfolios.append(portfolio)
    db.save_portfolios(portfolios)


def show_portfolio(user_id: int, base: str = "USD") -> dict:
    """Возвращает портфель, базу, итоговую стоимость и курсы."""
    get_currency(base)
    user = _load_user(user_id)
    portfolio = _load_portfolio(user)
    rates = _rates()
    total = portfolio.get_total_value(base_currency=base, rates=rates)

    wallet_values = {
        code: wallet.balance * rates[code] / rates[base]
        for code, wallet in portfolio.wallets.items()
    }

    return {
        "portfolio": portfolio,
        "user": user,
        "base": base,
        "total": total,
        "rates": rates,
        "wallet_values": wallet_values,
    }

@log_action
def buy(user_id: int, currency: str, amount) -> dict:
    """Покупка: зачисляет валюту, считает оценочную стоимость в USD."""
    amount = _validate_amount(amount)
    currency = currency.strip().upper()
    get_currency(currency)

    rate = _rate(currency)
    cost = convert(amount, rate)

    user = _load_user(user_id)
    portfolio = _load_portfolio(user)
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
        "base": "USD",
    }

@log_action
def sell(user_id: int, currency: str, amount) -> dict:
    """Продажа: списывает валюту, считает оценочную выручку в USD."""
    amount = _validate_amount(amount)
    currency = currency.strip().upper()
    get_currency(currency)

    rate = _rate(currency)

    user = _load_user(user_id)
    portfolio = _load_portfolio(user)
    target = portfolio.get_wallet(currency)
    if target is None:
        raise InsufficientFundsError(
            f"У вас нет кошелька '{currency}'. "
            f"Добавьте валюту: она создаётся автоматически при первой покупке."
        )
    before = target.balance
    target.withdraw(amount)
    _save_portfolio(portfolio)

    return {
        "currency": currency,
        "amount": amount,
        "before": before,
        "after": target.balance,
        "rate": rate,
        "revenue": convert(amount, rate),
        "base": "USD",
    }

def get_rate(from_code: str, to_code: str) -> dict:
    """Курс между валютами с проверкой TTL кэша."""
    from_code = from_code.strip().upper()
    to_code = to_code.strip().upper()
    get_currency(from_code)
    get_currency(to_code)

    if _is_stale() and not _try_refresh():
        raise ApiRequestError(
            f"Курс {from_code}->{to_code} недоступен. "
            f"Повторите попытку позже или выполните update-rates."
        )

    rates = _rates()
    if from_code not in rates or to_code not in rates:
        raise ApiRequestError(
            f"Курс {from_code}->{to_code} недоступен. "
            f"Повторите попытку позже или выполните update-rates."
        )

    raw_rate = rates[from_code] / rates[to_code]
    reverse = rates[to_code] / rates[from_code]

    raw = DatabaseManager().load_rates()
    key = f"{from_code}_{to_code}"
    updated = (
        raw.get("pairs", {}).get(key, {}).get("updated_at")
        or raw.get("last_refresh")
    )

    return {
        "from": from_code,
        "to": to_code,
        "rate": raw_rate,
        "reverse": reverse,
        "updated_at": updated,
    }


def show_rates(currency: str | None = None, top: int | None = None) -> dict:
    """Курсы из rates.json с фильтрацией."""
    raw = DatabaseManager().load_rates()
    pairs = {k: v["rate"] for k, v in raw.get("pairs", {}).items()}
    updated_at = raw.get("last_refresh")

    if currency:
        currency = currency.strip().upper()
        if currency == "USD":
            pairs = {"USD_USD": 1.0}
        else:
            key = f"{currency}_USD"
            pairs = {key: pairs[key]} if key in pairs else {}
        return {"pairs": pairs, "updated_at": updated_at}

    if top:
        fiat = {"EUR", "GBP", "RUB"}
        crypto = {
            k: v for k, v in pairs.items()
            if k.split("_")[0] not in fiat
        }
        sorted_pairs = sorted(crypto.items(), key=lambda x: x[1], reverse=True)
        pairs = dict(sorted_pairs[:top])

    return {"pairs": pairs, "updated_at": updated_at}