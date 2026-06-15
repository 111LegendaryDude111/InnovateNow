from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from llm.errors import HuggingFaceImageError
from llm.image_generation import HuggingFaceImageClient
from llm.image_options import (
    build_styled_image_prompt,
    require_image_aspect_ratio,
    require_image_prompt,
    require_image_style_preset,
)


class FakeResponse:
    def __init__(
        self,
        body: bytes,
        content_type: str = "image/png",
    ) -> None:
        self.body = body
        self.headers = {"Content-Type": content_type}

    def read(self) -> bytes:
        return self.body

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None


class HuggingFaceImageClientTests(unittest.TestCase):
    def test_generate_image_posts_huggingface_request(self) -> None:
        with patch(
            "llm.transport.request.urlopen",
            return_value=FakeResponse(b"image-bytes"),
        ) as urlopen:
            client = HuggingFaceImageClient(api_key="test-key")

            result = client.generate_image(
                "A launch poster",
                aspect_ratio="landscape",
                style_preset="product",
            )

        request = urlopen.call_args.args[0]
        self.assertEqual(
            request.full_url,
            "https://router.huggingface.co/hf-inference/models/"
            "black-forest-labs/FLUX.1-schnell",
        )
        self.assertEqual(request.headers["Authorization"], "Bearer test-key")
        payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(payload["parameters"], {"width": 1536, "height": 1024})
        self.assertIn("Style preset:", payload["inputs"])
        self.assertEqual(result.image_base64, "aW1hZ2UtYnl0ZXM=")
        self.assertEqual(result.mime_type, "image/png")
        self.assertEqual(result.size, "1536x1024")
        self.assertEqual(result.provider, "huggingface")

    def test_missing_api_key_fails_before_request(self) -> None:
        with patch("llm.transport.request.urlopen") as urlopen:
            client = HuggingFaceImageClient(api_key="")

            with self.assertRaisesRegex(HuggingFaceImageError, "HF_TOKEN"):
                client.generate_image(
                    "A poster",
                    aspect_ratio="square",
                    style_preset="minimal",
                )

        urlopen.assert_not_called()

    def test_unexpected_provider_response_raises_image_error(self) -> None:
        with patch(
            "llm.transport.request.urlopen",
            return_value=FakeResponse(b'{"error":"bad"}', "application/json"),
        ):
            client = HuggingFaceImageClient(api_key="test-key")

            with self.assertRaisesRegex(HuggingFaceImageError, "non-image"):
                client.generate_image(
                    "A poster",
                    aspect_ratio="square",
                    style_preset="minimal",
                )

    def test_prompt_validation_rejects_blank_text(self) -> None:
        with self.assertRaisesRegex(ValueError, "non-empty"):
            require_image_prompt("  ")

    def test_aspect_ratio_validation_rejects_unknown_value(self) -> None:
        with self.assertRaisesRegex(ValueError, "aspect_ratio"):
            require_image_aspect_ratio("panorama")

    def test_style_validation_rejects_unknown_value(self) -> None:
        with self.assertRaisesRegex(ValueError, "style_preset"):
            require_image_style_preset("anime")

    def test_none_style_keeps_prompt_unchanged(self) -> None:
        self.assertEqual(build_styled_image_prompt("Clean logo", "none"), "Clean logo")


if __name__ == "__main__":
    unittest.main()
