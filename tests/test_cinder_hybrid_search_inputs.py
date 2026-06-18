from __future__ import annotations

import csv
import sys
import unittest
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


ROOT = Path(__file__).resolve().parents[1]
PRODUCTS_PATH = ROOT / "data/cinder_home_goods_products.csv"
QUERIES_PATH = ROOT / "data/cinder_home_goods_queries.csv"

PRODUCT_HEADER = [
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

QUERY_HEADER = [
    "query_id",
    "query_text",
    "query_type",
    "filter_category",
    "filter_subcategory",
    "filter_brand",
    "filter_color",
    "filter_material",
    "filter_price_min",
    "filter_price_max",
    "filter_availability",
    "expected_keyword_fields",
    "expected_vector_fields",
    "expected_ranking_signals",
    "notes",
]

ATTRIBUTE_FIELDS = [
    "attribute_color",
    "attribute_material",
    "attribute_size",
    "attribute_style",
    "attribute_room",
    "attribute_finish",
]


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


class CinderHybridSearchInputsTests(unittest.TestCase):
    def test_product_csv_schema_and_minimum_records(self) -> None:
        header, rows = read_csv(PRODUCTS_PATH)
        raw = PRODUCTS_PATH.read_text(encoding="utf-8")

        self.assertEqual(header, PRODUCT_HEADER)
        self.assertGreaterEqual(len(rows), 40)
        self.assertEqual(len({row["product_id"] for row in rows}), len(rows))
        self.assertEqual(len({row["sku"] for row in rows}), len(rows))
        self.assertNotIn("HF_TOKEN", raw)
        self.assertNotIn("Authorization", raw)
        self.assertNotIn("hf_", raw)

    def test_product_csv_edge_cases_are_present(self) -> None:
        _, rows = read_csv(PRODUCTS_PATH)
        title_counts = Counter(row["title"] for row in rows)
        normalized_brands = Counter(_brand_key(row["brand"]) for row in rows)

        self.assertTrue(any(count > 1 for count in title_counts.values()))
        self.assertTrue(any(row["description"] == "" for row in rows))
        self.assertTrue(any(row["availability"] == "out_of_stock" for row in rows))
        self.assertTrue(any(count > 1 for count in normalized_brands.values()))
        self.assertIn("decor", {row["category"] for row in rows})
        self.assertIn("decorative accents", {row["category"] for row in rows})
        self.assertTrue(
            any(
                sum(1 for field in ATTRIBUTE_FIELDS if row[field] == "") >= 3
                for row in rows
            )
        )

    def test_product_numeric_fields_are_parseable(self) -> None:
        _, rows = read_csv(PRODUCTS_PATH)
        for row in rows:
            self.assertGreater(float(row["price"]), 0)
            self.assertGreaterEqual(int(row["clicks"]), 0)
            self.assertGreaterEqual(int(row["add_to_cart_count"]), 0)
            self.assertGreaterEqual(float(row["conversion_rate"]), 0)
            self.assertGreaterEqual(float(row["popularity_score"]), 0)

    def test_query_csv_schema_and_query_types(self) -> None:
        header, rows = read_csv(QUERIES_PATH)
        query_types = {row["query_type"] for row in rows}

        self.assertEqual(header, QUERY_HEADER)
        self.assertGreaterEqual(len(rows), 15)
        self.assertEqual(len({row["query_id"] for row in rows}), len(rows))
        self.assertTrue(
            {
                "exact_sku",
                "exact_product_name",
                "broad_category",
                "attribute_based",
                "vague_intent",
            }.issubset(query_types)
        )

    def test_queries_reference_product_inputs_without_merging_filters(self) -> None:
        _, products = read_csv(PRODUCTS_PATH)
        _, queries = read_csv(QUERIES_PATH)
        skus = {row["sku"] for row in products}
        titles = {row["title"] for row in products}

        self.assertTrue(any(row["query_text"] in skus for row in queries))
        self.assertTrue(any(row["query_text"] in titles for row in queries))
        self.assertTrue(any(row["filter_price_max"] for row in queries))
        self.assertTrue(any(row["filter_material"] for row in queries))
        self.assertTrue(any(row["filter_availability"] for row in queries))
        self.assertTrue(
            all(
                row["expected_keyword_fields"]
                and row["expected_vector_fields"]
                and row["expected_ranking_signals"]
                for row in queries
            )
        )


def _brand_key(value: str) -> str:
    return "".join(char for char in value.casefold() if char.isalnum())


if __name__ == "__main__":
    unittest.main()
