"""Исключения проекта ValutaTrade Hub."""


class InsufficientFundsError(Exception):
    """Недостаточно средств на кошельке.

    Сообщение: «Недостаточно средств: доступно {available} {code},
    требуется {required} {code}»
    """


class CurrencyNotFoundError(Exception):
    """Запрошена неизвестная валюта.

    Сообщение: «Неизвестная валюта '{code}'»
    """


class ApiRequestError(Exception):
    """Сбой при обращении к внешнему API.

    Сообщение: «Ошибка при обращении к внешнему API: {reason}»
    """