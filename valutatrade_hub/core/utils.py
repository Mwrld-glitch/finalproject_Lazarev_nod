"""Вспомогательные функции: работа с JSON-хранилищем."""

import json
from pathlib import Path

DATA_DIR = Path("data")


def read(name: str):
    """Читает JSON-файл из data/."""
    return json.loads((DATA_DIR / name).read_text(encoding="utf-8"))


def write(name: str, data) -> None:
    """Пишет JSON-файл в data/."""
    (DATA_DIR / name).write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )