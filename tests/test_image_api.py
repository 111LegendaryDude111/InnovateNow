from __future__ import annotations

import sys
import unittest
from pathlib import Path

from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from llm.api import ImageRequest, app, create_image_response
from llm.errors import HuggingFaceImageError
from llm.image_generation import ImageGenerationResult


class FakeImageClient:
    has_api_key = True

    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str]] = []

    def generate_image(
        self,
        prompt: str,
        *,
        aspect_ratio: str,
        style_preset: str,
    ) -> ImageGenerationResult:
        self.calls.append((prompt, aspect_ratio, style_preset))
        return ImageGenerationResult(
            image_base64="abc",
            mime_type="image/png",
            prompt=prompt,
            aspect_ratio=aspect_ratio,
            style_preset=style_preset,
            size="1024x1024",
            model="black-forest-labs/FLUX.1-schnell",
            created=123,
        )


class ImageApiTests(unittest.TestCase):
    def test_app_registers_image_endpoint(self) -> None:
        paths = {route.path for route in app.routes}

        self.assertIn("/images/generate", paths)

    def test_create_image_response_returns_normalized_payload(self) -> None:
        client = FakeImageClient()

        response = create_image_response(
            ImageRequest(
                prompt="A clean SaaS dashboard",
                aspect_ratio="square",
                style_preset="minimal",
            ),
            client=client,
        )

        self.assertEqual(response.image_base64, "abc")
        self.assertEqual(response.provider, "huggingface")
        self.assertEqual(response.size, "1024x1024")
        self.assertEqual(
            client.calls, [("A clean SaaS dashboard", "square", "minimal")]
        )

    def test_blank_prompt_returns_http_error_before_provider_call(self) -> None:
        client = FakeImageClient()

        with self.assertRaises(HTTPException) as raised:
            create_image_response(
                ImageRequest(
                    prompt="   ", aspect_ratio="square", style_preset="minimal"
                ),
                client=client,
            )

        self.assertEqual(raised.exception.status_code, 400)
        self.assertEqual(raised.exception.detail, "prompt must be a non-empty string")
        self.assertEqual(client.calls, [])

    def test_invalid_style_returns_http_error_before_provider_call(self) -> None:
        client = FakeImageClient()

        with self.assertRaises(HTTPException) as raised:
            create_image_response(
                ImageRequest(
                    prompt="Poster", aspect_ratio="square", style_preset="anime"
                ),
                client=client,
            )

        self.assertEqual(raised.exception.status_code, 400)
        self.assertEqual(client.calls, [])

    def test_missing_huggingface_token_returns_http_error(self) -> None:
        class MissingKeyClient(FakeImageClient):
            has_api_key = False

        with self.assertRaises(HTTPException) as raised:
            create_image_response(
                ImageRequest(
                    prompt="Poster",
                    aspect_ratio="square",
                    style_preset="minimal",
                ),
                client=MissingKeyClient(),
            )

        self.assertEqual(raised.exception.status_code, 500)
        self.assertEqual(raised.exception.detail, "HF_TOKEN is required")

    def test_provider_error_returns_bad_gateway(self) -> None:
        class FailingClient(FakeImageClient):
            def generate_image(
                self,
                prompt: str,
                *,
                aspect_ratio: str,
                style_preset: str,
            ) -> ImageGenerationResult:
                raise HuggingFaceImageError(
                    "Hugging Face Images API error 401: invalid token"
                )

        with self.assertRaises(HTTPException) as raised:
            create_image_response(
                ImageRequest(
                    prompt="Poster",
                    aspect_ratio="square",
                    style_preset="minimal",
                ),
                client=FailingClient(),
            )

        self.assertEqual(raised.exception.status_code, 502)
        self.assertIn("Hugging Face Images API error 401", raised.exception.detail)


if __name__ == "__main__":
    unittest.main()
