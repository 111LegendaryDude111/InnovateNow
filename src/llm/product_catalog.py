from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class Product:
    product_id: str
    name: str
    description: str
    category: str
    price: float
    features: tuple[str, ...]


def load_products(path: Path) -> list[Product]:
    """Загружает committed product catalog и проверяет обязательные поля."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("product catalog must be a JSON array")

    products = [
        _product_from_payload(item, index) for index, item in enumerate(payload)
    ]
    require_unique_product_ids(products)
    return products


def require_unique_product_ids(products: list[Product]) -> list[Product]:
    seen: set[str] = set()
    for product in products:
        if product.product_id in seen:
            raise ValueError(f"duplicate product_id: {product.product_id}")
        seen.add(product.product_id)
    return products


def _product_from_payload(item: object, index: int) -> Product:
    if not isinstance(item, Mapping):
        raise ValueError(f"product at index {index} must be an object")
    return Product(
        product_id=_required_text(item, "product_id", index),
        name=_required_text(item, "name", index),
        description=_required_text(item, "description", index),
        category=_required_text(item, "category", index),
        price=_required_price(item, index),
        features=tuple(_required_text_list(item, "features", index)),
    )


def _required_text(item: Mapping[str, Any], key: str, index: int) -> str:
    value = item.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"product at index {index} must have non-empty {key}")
    return value.strip()


def _required_text_list(item: Mapping[str, Any], key: str, index: int) -> list[str]:
    value = item.get(key)
    if not isinstance(value, list) or not value:
        raise ValueError(f"product at index {index} must have non-empty {key}")
    return [_required_list_text(part, key, index) for part in value]


def _required_list_text(value: object, key: str, index: int) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"product at index {index} must have text entries in {key}")
    return value.strip()


def _required_price(item: Mapping[str, Any], index: int) -> float:
    value = item.get("price")
    if isinstance(value, bool) or not isinstance(value, int | float) or value <= 0:
        raise ValueError(f"product at index {index} must have positive numeric price")
    return float(value)
