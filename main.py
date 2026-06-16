from __future__ import annotations

import argparse
import sys
from pathlib import Path

ENV_FILE = Path(__file__).resolve().parent / ".env"
SRC_DIR = Path(__file__).resolve().parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from llm import LLMError, OpenRouterClient
from llm.embedding_cli import (
    EMBEDDING_COMMANDS,
    add_embedding_subcommands,
    run_embedding_command,
)
from llm.env import load_env_file
from llm.prompt_builder import build_content_prompt
from llm.qdrant_cli import (
    QDRANT_COMMANDS,
    add_qdrant_subcommands,
    run_qdrant_command,
)


def build_parser() -> argparse.ArgumentParser:
    """Создает CLI parser для команд приложения."""
    parser = argparse.ArgumentParser(
        description="Run the project LLM through OpenRouter.",
    )
    subparsers = parser.add_subparsers(dest="command")

    ask_parser = subparsers.add_parser("ask", help="Generate content by topic")
    _add_client_options(ask_parser)
    ask_parser.add_argument("--topic", required=True, help="Content topic")
    ask_parser.add_argument(
        "--content-type",
        required=True,
        help="Requested content type",
    )
    ask_parser.add_argument("--system", help="Optional system prompt")

    status_parser = subparsers.add_parser(
        "status",
        help="Show OpenRouter connection settings and check the API",
    )
    _add_client_options(status_parser)
    add_embedding_subcommands(subparsers)
    add_qdrant_subcommands(subparsers)

    return parser


def main(argv: list[str] | None = None) -> int:
    """Запускает CLI и возвращает process exit code."""
    load_env_file(ENV_FILE)
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    if args.command in EMBEDDING_COMMANDS:
        return run_embedding_command(args)
    if args.command in QDRANT_COMMANDS:
        return run_qdrant_command(args)

    client = OpenRouterClient.from_env(
        model=args.model,
        base_url=args.base_url,
    )

    if args.command == "ask":
        return _run_ask(client, args.topic, args.content_type, args.system)
    if args.command == "status":
        return _run_status(client)

    parser.error(f"Unknown command: {args.command}")
    return 2


def _add_client_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--model", help="OpenRouter model name")
    parser.add_argument("--base-url", help="OpenRouter base URL")


def _run_ask(
    client: OpenRouterClient,
    topic: str,
    content_type: str,
    system: str | None,
) -> int:
    """Собирает prompt из пользовательских полей и отправляет его в LLM."""
    try:
        prompt = build_content_prompt(topic, content_type)
        print(client.generate(prompt, system=system))
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
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


if __name__ == "__main__":
    raise SystemExit(main())
