from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ENV_FILE = Path(__file__).resolve().parent / ".env"
SRC_DIR = Path(__file__).resolve().parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from llm import LLMError, OpenRouterClient


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the project LLM through OpenRouter.",
    )
    subparsers = parser.add_subparsers(dest="command")

    ask_parser = subparsers.add_parser("ask", help="Send a prompt to the LLM")
    _add_client_options(ask_parser)
    ask_parser.add_argument("prompt", nargs="+", help="Prompt text")
    ask_parser.add_argument("--system", help="Optional system prompt")

    status_parser = subparsers.add_parser(
        "status",
        help="Show OpenRouter connection settings and check the API",
    )
    _add_client_options(status_parser)

    return parser


def main(argv: list[str] | None = None) -> int:
    load_env_file(ENV_FILE)
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    client = OpenRouterClient.from_env(
        model=args.model,
        base_url=args.base_url,
    )

    if args.command == "ask":
        return _run_ask(client, " ".join(args.prompt), args.system)
    if args.command == "status":
        return _run_status(client)

    parser.error(f"Unknown command: {args.command}")
    return 2


def _add_client_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--model", help="OpenRouter model name")
    parser.add_argument("--base-url", help="OpenRouter base URL")


def _run_ask(client: OpenRouterClient, prompt: str, system: str | None) -> int:
    try:
        print(client.generate(prompt, system=system))
    except LLMError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


def _run_status(client: OpenRouterClient) -> int:
    print("Provider: OpenRouter")
    print(f"Model: {client.model}")
    print(f"Base URL: {client.base_url}")
    print(f"API URL: {client.api_base_url}")
    print(f"Port: {client.port if client.port is not None else 'unknown'}")
    print(f"API key: {'configured' if client.has_api_key else 'missing'}")

    if not client.has_api_key:
        print("OpenRouter status: missing OPENROUTER_API_KEY")
        return 1

    try:
        model_available = client.model_available()
    except LLMError as exc:
        print(f"OpenRouter status: unavailable ({exc})")
        return 1

    print("OpenRouter status: available")
    print(f"Model status: {'available' if model_available else 'not found'}")
    if not model_available:
        return 1
    return 0


def load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line.removeprefix("export ").strip()

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


if __name__ == "__main__":
    raise SystemExit(main())
