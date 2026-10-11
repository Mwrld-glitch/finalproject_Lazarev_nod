"""Хранилище курсов Parser Service."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from valutatrade_hub.parser_service.config import ParserConfig


class RatesStorage:
    """Чтение и запись rates.json и exchange_rates.json."""

    def __init__(self, config: ParserConfig | None = None):
        self.config = config or ParserConfig()

    def _atomic_write(self, path: Path, data) -> None:
        """Атомарная запись: tmp → rename."""
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        os.replace(tmp, path)

    def save_rates(self, rates: dict, sources: dict | None = None) -> None:
        """Пишет снимок последних курсов в rates.json."""
        now = datetime.now(timezone.utc).isoformat()
        pairs = {}
        for pair, rate in rates.items():
            pairs[pair] = {
                "rate": rate,
                "updated_at": now,
                "source": (sources or {}).get(pair, "ParserService"),
            }
        payload = {"pairs": pairs, "last_refresh": now}
        self._atomic_write(Path(self.config.RATES_FILE_PATH), payload)

    def append_history(self, rates: dict, sources: dict | None = None) -> None:
        """Добавляет запись в exchange_rates.json (история)."""
        path = Path(self.config.HISTORY_FILE_PATH)
        history = []
        if path.exists():
            content = path.read_text(encoding="utf-8").strip()
            history = json.loads(content) if content else []

        now = datetime.now(timezone.utc).isoformat()
        for pair, rate in rates.items():
            from_code, to_code = pair.split("_")
            record_id = f"{pair}_{now}"
            history.append({
                "id": record_id,
                "from_currency": from_code,
                "to_currency": to_code,
                "rate": rate,
                "timestamp": now,
                "source": (sources or {}).get(pair, "ParserService"),
            })
        self._atomic_write(path, history)