"""CLI."""

import shlex

from prettytable import PrettyTable

from valutatrade_hub.core import usecases
from valutatrade_hub.core.currencies import CURRENCIES
from valutatrade_hub.core.exceptions import (
    ApiRequestError,
    CurrencyNotFoundError,
    InsufficientFundsError,
)
from valutatrade_hub.parser_service.updater import RatesUpdater

_CURRENT_USER = None


def handle_errors(func):
    """Ловит доменные ошибки и печатает пользователю."""

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except InsufficientFundsError as e:
            print(f"Ошибка: {e}")
        except CurrencyNotFoundError as e:
            print(f"Ошибка: {e}")
            print(f"Доступные валюты: {', '.join(CURRENCIES.keys())}")
        except ApiRequestError as e:
            print(f"Ошибка API: {e}. Повторите позже.")
        except Exception as e:
            print(f"Ошибка: {e}")

    return wrapper


def _args(parts: list[str]) -> dict:
    """Разбирает --key value в словарь."""
    return {parts[i][2:]: parts[i + 1] for i in range(1, len(parts), 2)}


def _login():
    """Залогиненный пользователь."""
    if _CURRENT_USER is None:
        raise ValueError("Сначала выполните login")
    return _CURRENT_USER


def _table(headers: list[str], rows: list[list]) -> None:
    """Печатает таблицу."""
    table = PrettyTable(headers)
    table.add_rows(rows)
    print(table)


@handle_errors
def _run(line: str) -> None:
    """Выполняет одну команду."""
    global _CURRENT_USER

    parts = shlex.split(line)
    if not parts:
        return

    cmd = parts[0]
    a = _args(parts)

    match cmd:
        case "register":
            _table(["Результат"], [[usecases.register(a["username"], a["password"])]])

        case "login":
            _CURRENT_USER = usecases.login(a["username"], a["password"])
            _table(["Пользователь"], [[_CURRENT_USER.username]])

        case "show-portfolio":
            base = a.get("base", "USD").upper()
            info = usecases.show_portfolio(_login(), base)
            rows = [
                [c, w.balance, f"{w.balance * usecases.get_rate(c, base)['rate']:.2f}"]
                for c, w in info["portfolio"].wallets.items()
            ]
            rows.append(["ИТОГО", "", f"{info['total']:.2f}"])
            _table(["Валюта", "Баланс", f"В {base}"], rows)

        case "buy":
            r = usecases.buy(_login(), a["currency"], float(a["amount"]))
            _table(["Валюта", "Кол-во", "Курс", "Стоимость"],
                   [[r["currency"], r["amount"], r["rate"], f"{r['cost']:.2f}"]])

        case "sell":
            r = usecases.sell(_login(), a["currency"], float(a["amount"]))
            _table(["Валюта", "Кол-во", "Курс", "Выручка"],
                   [[r["currency"], r["amount"], r["rate"], f"{r['revenue']:.2f}"]])

        case "get-rate":
            r = usecases.get_rate(a["from"], a["to"])
            _table(["Из", "В", "Курс"],
                   [[r["from"], r["to"], r["rate"]],
                    [r["to"], r["from"], r["reverse"]]])

        case "update-rates":
            source = a.get("source")
            result = RatesUpdater().run_update(source=source)
            _table(
                ["Источник", "Пар обновлено"],
                [[source or "all", len(result)]],
            )

        case "show-rates":
            currency = a.get("currency")
            top = int(a["top"]) if "top" in a else None
            data = usecases.show_rates(currency=currency, top=top)
            pairs = data["pairs"]
            if not pairs:
                _table(["Сообщение"], [[f"Курс для '{currency}' не найден в кеше."]])
            else:
                rows = [[pair, f"{rate:.8f}"] for pair, rate in pairs.items()]
                _table(["Пара", "Курс"], rows)
                
        case _:
            _table(["Сообщение"], [[f"Неизвестная команда: {cmd}"]])


def main() -> None:
    """Интерактивный CLI."""
    print("Введите команду (или 'exit'):")
    while True:
        line = input("> ").strip()
        if line == "exit":
            break
        _run(line)