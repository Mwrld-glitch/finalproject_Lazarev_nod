"""Точка входа."""

from valutatrade_hub.cli.interface import run
from valutatrade_hub.logging_config import setup_logging


def main():
    """Запускает CLI."""
    setup_logging()
    run()


if __name__ == "__main__":
    main()