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
from valutatrade_hub.logging_config import parser_console_logging
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
            print(f"Ошибка API: {e}")
        except ValueError as e:
            print(f"Ошибка: {e}")

    return wrapper


def _args(parts: list[str]) -> dict:
    """Разбирает --key value в словарь."""
    result = {}
    i = 1
    while i < len(parts):
        if parts[i].startswith("--") and i + 1 < len(parts):
            result[parts[i][2:]] = parts[i + 1]
            i += 2
        else:
            i += 1
    return result


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
            print(f"Вы вошли как '{_CURRENT_USER.username}'")

        case "show-portfolio":
            base = a.get("base", "USD").upper()
            info = usecases.show_portfolio(_login().user_id, base)
            print(f"Портфель пользователя '{info['user'].username}' (база: {base}):")
            if not info["portfolio"].wallets:
                print("Портфель пуст.")
                return
            rows = [
                [w.get_balance_info(), f"{info['wallet_values'][code]:.2f} {base}"]
                for code, w in info["portfolio"].wallets.items()
            ]
            rows.append(["ИТОГО", f"{info['total']:,.2f} {base}"])
            _table(["Валюта", f"В {base}"], rows)

        case "buy":
            r = usecases.buy(_login().user_id, a["currency"], a["amount"])
            print(
                f"Покупка выполнена: {r['amount']:.4f} {r['currency']} "
                f"по курсу {r['rate']:,.2f} USD/{r['currency']}"
            )
            print("Изменения в портфеле:")
            print(f"- {r['currency']}: было {r['before']:.4f} → стало {r['after']:.4f}")
            print(f"Оценочная стоимость покупки: {r['cost']:,.2f} USD")

        case "sell":
            r = usecases.sell(_login().user_id, a["currency"], a["amount"])
            print(
                f"Продажа выполнена: {r['amount']:.4f} {r['currency']} "
                f"по курсу {r['rate']:,.2f} USD/{r['currency']}"
            )
            print("Изменения в портфеле:")
            print(f"- {r['currency']}: было {r['before']:.4f} → стало {r['after']:.4f}")
            print(f"Оценочная выручка: {r['revenue']:,.2f} USD")

        case "get-rate":
            r = usecases.get_rate(a["from"], a["to"])
            updated = (r["updated_at"] or "неизвестно").replace("T", " ").split(".")[0].split("+")[0]
            print(f"Курс {r['from']}→{r['to']}: {r['rate']:.8f} (обновлено: {updated})")
            print(f"Обратный курс {r['to']}→{r['from']}: {r['reverse']:.8f}")

        case "update-rates":
            source = a.get("source")
            with parser_console_logging():
                try:
                    result = RatesUpdater().run_update(source=source)
                except ApiRequestError as e:
                    print(f"ERROR: {e}")
                    return
            print(
                f"Update successful. Total rates updated: {result['updated']}. "
                f"Last refresh: {result['last_refresh']}"
            )
            if result["errors"]:
                print(
                    "Update completed with errors. "
                    "Check logs/parser.log for details."
                )
                
        case "show-rates":
            currency = a.get("currency")
            top = int(a["top"]) if "top" in a else None
            data = usecases.show_rates(currency=currency, top=top)
            pairs = data["pairs"]
            if not pairs:
                if currency:
                    print(f"Курс для '{currency.upper()}' не найден в кеше.")
                else:
                    print(
                        "Локальный кеш курсов пуст. "
                        "Выполните 'update-rates', чтобы загрузить данные."
                    )
            else:
                rows = [[pair, f"{rate:.8f}"] for pair, rate in pairs.items()]
                _table(["Пара", "Курс"], rows)

        case _:
            print(f"Неизвестная команда: {cmd}")


def main() -> None:
    """Интерактивный CLI."""
    print("Введите команду (или 'exit'):")
    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if line == "exit":
            break
        _run(line)