from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_HAVEN_SUPPORT_PATH = (
    Path(__file__).resolve().parents[2] / "data/haven_support_knowledge.json"
)


def load_haven_support_config(path: Path = DEFAULT_HAVEN_SUPPORT_PATH) -> dict[str, Any]:
    """Загружает Haven support policy и проверяет ссылки между routing и KB."""
    with path.open(encoding="utf-8") as handle:
        config = json.load(handle)
    _validate_config(config)
    return config


def _validate_config(config: dict[str, Any]) -> None:
    entry_ids = {entry["id"] for entry in config["knowledge"]}
    if len(entry_ids) != len(config["knowledge"]):
        raise ValueError("duplicate Haven support knowledge id")
    flow_intents = {flow["intent"] for flow in config["flows"]}
    for route in config["supported_requests"]:
        missing = set(route["entry_ids"]) - entry_ids
        if missing:
            raise ValueError(f"unknown Haven support entry: {sorted(missing)[0]}")
        if route["intent"] not in flow_intents:
            raise ValueError(f"missing Haven support flow: {route['intent']}")
