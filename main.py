"""Точка входа."""

from valutatrade_hub.cli.interface import main
from valutatrade_hub.logging_config import setup_logging


def main_entry():
    """Обёртка для скрипта."""
    setup_logging()
    main()


if __name__ == "__main__":
    main_entry()