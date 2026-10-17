"""Настройка логирования проекта."""

import logging
from contextlib import contextmanager
from logging.handlers import RotatingFileHandler

from valutatrade_hub.infra.settings import SettingsLoader

_FILE_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"
_CONSOLE_FORMAT = "%(levelname)s %(message)s"

_console_handler: logging.Handler | None = None


def setup_logging() -> None:
    """Настраивает корневой логгер: файл (DEBUG) + опционально консоль."""
    settings = SettingsLoader()
    log_file = settings.get("LOG_FILE")
    log_file.parent.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    # защита от дублирования хендлеров при повторном вызове
    if any(isinstance(h, RotatingFileHandler) for h in root.handlers):
        return

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        _FILE_FORMAT, datefmt="%Y-%m-%dT%H:%M:%S",
    ))
    root.addHandler(file_handler)


@contextmanager
def parser_console_logging():
    """Временно подключает консольный хендлер (INFO).

    Используется только на время CLI-команды update-rates,
    чтобы логи парсера не сыпались в консоль при других командах.
    """
    root = logging.getLogger()
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter(_CONSOLE_FORMAT))
    root.addHandler(handler)
    try:
        yield
    finally:
        root.removeHandler(handler)