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

    def save_rates(
        self,
        rates: dict,
        sources: dict | None = None,
        timestamps: dict | None = None,
    ) -> None:
        """Пишет снимок последних курсов в rates.json."""
        now = datetime.now(timezone.utc).isoformat()
        path = Path(self.config.RATES_FILE_PATH)

        existing = {}
        if path.exists():
            content = path.read_text(encoding="utf-8").strip()
            existing = json.loads(content).get("pairs", {}) if content else {}

        pairs = dict(existing)
        for pair, rate in rates.items():
            updated_at = (timestamps or {}).get(pair) or now
            old = pairs.get(pair)
            if old and old.get("updated_at", "") > updated_at:
                continue
            pairs[pair] = {
                "rate": rate,
                "updated_at": updated_at,
                "source": (sources or {}).get(pair, "ParserService"),
            }
        payload = {"pairs": pairs, "last_refresh": now}
        self._atomic_write(path, payload)

    def append_history(
        self,
        rates: dict,
        sources: dict | None = None,
        meta: dict | None = None,
    ) -> None:
        """Добавляет записи в exchange_rates.json без дублей по id."""
        path = Path(self.config.HISTORY_FILE_PATH)
        history = []
        if path.exists():
            content = path.read_text(encoding="utf-8").strip()
            history = json.loads(content) if content else []

        existing_ids = {rec.get("id") for rec in history}

        now = datetime.now(timezone.utc).isoformat()
        for pair, rate in rates.items():
            record_id = f"{pair}_{now}"
            if record_id in existing_ids:
                continue
            from_code, to_code = pair.split("_")
            record = {
                "id": record_id,
                "from_currency": from_code,
                "to_currency": to_code,
                "rate": rate,
                "timestamp": now,
                "source": (sources or {}).get(pair, "ParserService"),
            }
            if meta and pair in meta:
                record["meta"] = meta[pair]
            history.append(record)
            existing_ids.add(record_id)

        self._atomic_write(path, history)