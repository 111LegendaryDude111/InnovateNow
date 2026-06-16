from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from llm.errors import HuggingFaceEmbeddingsError
from llm.huggingface_embeddings import (
    HuggingFaceEmbeddingClient,
    parse_embedding_vectors,
    require_embedding_texts,
)


class FakeResponse:
    def __init__(self, payload: object) -> None:
        self.body = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self.body

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None


class HuggingFaceEmbeddingClientTests(unittest.TestCase):
    def test_embed_texts_posts_feature_extraction_request(self) -> None:
        with patch(
            "llm.huggingface_embeddings.request.urlopen",
            return_value=FakeResponse([[0.1, 0.2], [0.3, 0.4]]),
        ) as urlopen:
            client = HuggingFaceEmbeddingClient(api_key="test-key")

            vectors = client.embed_texts(["first text", "second text"])

        request = urlopen.call_args.args[0]
        self.assertEqual(
            request.full_url,
            "https://router.huggingface.co/hf-inference/models/"
            "ibm-granite/granite-embedding-311m-multilingual-r2",
        )
        self.assertEqual(request.headers["Authorization"], "Bearer test-key")
        payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(payload["inputs"], ["first text", "second text"])
        self.assertTrue(payload["normalize"])
        self.assertTrue(payload["truncate"])
        self.assertEqual(vectors, [[0.1, 0.2], [0.3, 0.4]])

    def test_missing_token_fails_before_request(self) -> None:
        with patch("llm.huggingface_embeddings.request.urlopen") as urlopen:
            client = HuggingFaceEmbeddingClient(api_key="")

            with self.assertRaisesRegex(HuggingFaceEmbeddingsError, "HF_TOKEN"):
                client.embed_texts(["hello"])

        urlopen.assert_not_called()

    def test_parse_single_vector_response_for_one_input(self) -> None:
        self.assertEqual(
            parse_embedding_vectors([0.1, 0.2], expected_count=1),
            [[0.1, 0.2]],
        )

    def test_parse_rejects_count_mismatch(self) -> None:
        with self.assertRaisesRegex(HuggingFaceEmbeddingsError, "count mismatch"):
            parse_embedding_vectors([[0.1, 0.2]], expected_count=2)

    def test_require_embedding_texts_rejects_blank_entry(self) -> None:
        with self.assertRaisesRegex(ValueError, "non-empty"):
            require_embedding_texts(["valid", "  "])


if __name__ == "__main__":
    unittest.main()
