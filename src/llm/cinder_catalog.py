from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


CINDER_PRODUCT_HEADER = [
    "product_id",
    "title",
    "brand",
    "category",
    "subcategory",
    "description",
    "attribute_color",
    "attribute_material",
    "attribute_size",
    "attribute_style",
    "attribute_room",
    "attribute_finish",
    "price",
    "availability",
    "sku",
    "tags",
    "clicks",
    "add_to_cart_count",
    "conversion_rate",
    "popularity_score",
]


@dataclass(frozen=True, slots=True)
class CinderProduct:
    product_id: str
    title: str
    brand: str
    category: str
    subcategory: str
    description: str
    attribute_color: str
    attribute_material: str
    attribute_size: str
    attribute_style: str
    attribute_room: str
    attribute_finish: str
    price: float
    availability: str
    sku: str
    tags: str
    clicks: int
    add_to_cart_count: int
    conversion_rate: float
    popularity_score: float

    def attribute_texts(self) -> tuple[str, ...]:
        return tuple(
            value
            for value in (
                self.attribute_color,
                self.attribute_material,
                self.attribute_size,
                self.attribute_style,
                self.attribute_room,
                self.attribute_finish,
            )
            if value
        )


def load_cinder_products(path: Path) -> list[CinderProduct]:
    """Загружает synthetic Cinder CSV и проверяет стабильный schema contract."""
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if list(reader.fieldnames or []) != CINDER_PRODUCT_HEADER:
            raise ValueError("cinder product CSV header does not match contract")
        products = [_product_from_row(row, index) for index, row in enumerate(reader)]
    _require_unique(products, "product_id")
    _require_unique(products, "sku")
    return products


def _product_from_row(row: dict[str, str], index: int) -> CinderProduct:
    return CinderProduct(
        product_id=_text(row, "product_id", index),
        title=_text(row, "title", index),
        brand=_text(row, "brand", index),
        category=_text(row, "category", index),
        subcategory=_text(row, "subcategory", index),
        description=row["description"].strip(),
        attribute_color=row["attribute_color"].strip(),
        attribute_material=row["attribute_material"].strip(),
        attribute_size=row["attribute_size"].strip(),
        attribute_style=row["attribute_style"].strip(),
        attribute_room=row["attribute_room"].strip(),
        attribute_finish=row["attribute_finish"].strip(),
        price=_positive_float(row, "price", index),
        availability=_availability(row, index),
        sku=_text(row, "sku", index),
        tags=_text(row, "tags", index),
        clicks=_non_negative_int(row, "clicks", index),
        add_to_cart_count=_non_negative_int(row, "add_to_cart_count", index),
        conversion_rate=_non_negative_float(row, "conversion_rate", index),
        popularity_score=_non_negative_float(row, "popularity_score", index),
    )


def _text(row: dict[str, str], key: str, index: int) -> str:
    value = row[key].strip()
    if not value:
        raise ValueError(f"product at row {index} must have non-empty {key}")
    return value


def _availability(row: dict[str, str], index: int) -> str:
    value = _text(row, "availability", index)
    if value not in {"in_stock", "out_of_stock"}:
        raise ValueError(f"product at row {index} has invalid availability")
    return value


def _positive_float(row: dict[str, str], key: str, index: int) -> float:
    value = _non_negative_float(row, key, index)
    if value <= 0:
        raise ValueError(f"product at row {index} must have positive {key}")
    return value


def _non_negative_float(row: dict[str, str], key: str, index: int) -> float:
    try:
        value = float(row[key])
    except ValueError as exc:
        raise ValueError(f"product at row {index} must have numeric {key}") from exc
    if value < 0:
        raise ValueError(f"product at row {index} must have non-negative {key}")
    return value


def _non_negative_int(row: dict[str, str], key: str, index: int) -> int:
    try:
        value = int(row[key])
    except ValueError as exc:
        raise ValueError(f"product at row {index} must have integer {key}") from exc
    if value < 0:
        raise ValueError(f"product at row {index} must have non-negative {key}")
    return value


def _require_unique(products: list[CinderProduct], field: str) -> None:
    seen: set[str] = set()
    for product in products:
        value = getattr(product, field)
        if value in seen:
            raise ValueError(f"duplicate {field}: {value}")
        seen.add(value)
