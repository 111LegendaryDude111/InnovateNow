from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .embedding_pipeline import (
    build_embeddings_file,
    search_embedding_artifact,
)
from .embedding_storage import load_embedding_artifact
from .errors import HuggingFaceEmbeddingsError
from .huggingface_embeddings import (
    DEFAULT_HUGGINGFACE_EMBEDDING_MODEL,
    DEFAULT_HUGGINGFACE_EMBEDDING_TIMEOUT,
    HuggingFaceEmbeddingClient,
)

EMBEDDING_COMMANDS = {"embeddings-build", "embeddings-search"}
DEFAULT_DOCUMENTS_PATH = Path("data/internal_knowledge_documents.json")
DEFAULT_ARTIFACT_PATH = Path("artifacts/document_embeddings.json")
DEFAULT_DEMO_QUERY = "how do I reset my password?"
DEFAULT_CHUNK_WORDS = 180
DEFAULT_CHUNK_OVERLAP = 30


def add_embedding_subcommands(subparsers: argparse._SubParsersAction) -> None:
    build_parser = subparsers.add_parser(
        "embeddings-build",
        help="Generate document embeddings through Hugging Face",
    )
    _add_common_provider_options(build_parser)
    build_parser.add_argument("--documents", type=Path, default=DEFAULT_DOCUMENTS_PATH)
    build_parser.add_argument("--output", type=Path, default=DEFAULT_ARTIFACT_PATH)
    build_parser.add_argument("--chunk-words", type=int, default=DEFAULT_CHUNK_WORDS)
    build_parser.add_argument(
        "--chunk-overlap", type=int, default=DEFAULT_CHUNK_OVERLAP
    )

    search_parser = subparsers.add_parser(
        "embeddings-search",
        help="Run semantic similarity search against a local embeddings artifact",
    )
    _add_common_provider_options(search_parser)
    search_parser.add_argument("--artifact", type=Path, default=DEFAULT_ARTIFACT_PATH)
    search_parser.add_argument("--query", default=DEFAULT_DEMO_QUERY)
    search_parser.add_argument("--top-k", type=int, default=5)


def run_embedding_command(args: argparse.Namespace) -> int:
    try:
        if args.command == "embeddings-build":
            return _run_build(args)
        if args.command == "embeddings-search":
            return _run_search(args)
    except (ValueError, OSError, HuggingFaceEmbeddingsError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    raise ValueError(f"Unknown embeddings command: {args.command}")


def _add_common_provider_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--model",
        help=f"Hugging Face embedding model; default {DEFAULT_HUGGINGFACE_EMBEDDING_MODEL}",
    )
    parser.add_argument("--base-url", help="Hugging Face embeddings base URL")
    parser.add_argument(
        "--timeout",
        type=float,
        help=f"Hugging Face timeout seconds; default {DEFAULT_HUGGINGFACE_EMBEDDING_TIMEOUT}",
    )


def _run_build(args: argparse.Namespace) -> int:
    client = _client_from_args(args, model=None)
    artifact = build_embeddings_file(
        args.documents,
        args.output,
        client,
        chunk_words=args.chunk_words,
        chunk_overlap=args.chunk_overlap,
    )
    records = artifact["records"]
    print(f"Wrote {len(records)} embedding records to {args.output}")
    print(f"Model: {client.model}")
    return 0


def _run_search(args: argparse.Namespace) -> int:
    artifact = load_embedding_artifact(args.artifact)
    client = _client_from_args(args, model=_artifact_model(artifact))
    matches = search_embedding_artifact(
        artifact,
        args.query,
        client,
        top_k=args.top_k,
    )
    print(f"Query: {args.query}")
    for index, match in enumerate(matches, start=1):
        print(
            f"{index}. {match.document_id} {match.chunk_id} "
            f"score={match.score:.4f} title={match.title}"
        )
    return 0


def _client_from_args(
    args: argparse.Namespace,
    *,
    model: str | None,
) -> HuggingFaceEmbeddingClient:
    return HuggingFaceEmbeddingClient.from_env(
        model=args.model or model,
        base_url=args.base_url,
        timeout=args.timeout,
    )


def _artifact_model(artifact: dict[str, object]) -> str:
    model = artifact.get("model")
    if not isinstance(model, str) or not model.strip():
        raise ValueError("embedding artifact must contain model")
    return model
