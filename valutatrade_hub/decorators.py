"""Декораторы проекта."""

import logging

log = logging.getLogger(__name__)


def log_action(func):
    """Логирует вызов функции, не глотая исключения."""

    def wrapper(*args, **kwargs):
        log.info("Вызов %s", func.__name__)
        try:
            result = func(*args, **kwargs)
            log.info("%s — OK", func.__name__)
            return result
        except Exception as e:
            log.error("%s — ERROR: %s", func.__name__, e)
            raise

    return wrapper


def handle_errors(func):
    """Ловит ошибки и печатает пользователю."""

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"Ошибка: {e}")

    return wrapper