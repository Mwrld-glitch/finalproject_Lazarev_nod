"""Настройка логирования проекта."""

import logging
from contextlib import contextmanager
from logging.handlers import RotatingFileHandler

from valutatrade_hub.infra.settings import SettingsLoader


_FILE_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"
_CONSOLE_FORMAT = "%(levelname)s %(message)s"

_PARSER_LOGGER_NAME = "valutatrade_hub.parser_service"


def _make_file_handler(path, level):
    """Создаёт RotatingFileHandler с указанным уровнем."""
    path.parent.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(
        path,
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(
        _FILE_FORMAT, datefmt="%Y-%m-%dT%H:%M:%S",
    ))
    return handler


def setup_logging() -> None:
    """Настраивает корневой логгер и логгер парсера."""
    settings = SettingsLoader()
    log_file = settings.get("LOG_FILE")
    parser_log_file = log_file.parent / "parser.log"

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    if not any(isinstance(h, RotatingFileHandler) for h in root.handlers):
        root.addHandler(_make_file_handler(log_file, logging.DEBUG))

    parser_logger = logging.getLogger(_PARSER_LOGGER_NAME)
    parser_logger.setLevel(logging.DEBUG)
    if not any(
        isinstance(h, RotatingFileHandler) for h in parser_logger.handlers
    ):
        parser_logger.addHandler(
            _make_file_handler(parser_log_file, logging.DEBUG)
        )
    parser_logger.propagate = False

    logging.getLogger("urllib3").setLevel(logging.WARNING)


@contextmanager
def parser_console_logging():
    """Временно подключает консольный хендлер для логгера парсера."""
    parser_logger = logging.getLogger(_PARSER_LOGGER_NAME)
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter(_CONSOLE_FORMAT))
    parser_logger.addHandler(handler)
    try:
        yield
    finally:
        parser_logger.removeHandler(handler)