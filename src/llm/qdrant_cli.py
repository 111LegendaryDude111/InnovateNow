from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .document_collection import load_documents
from .errors import HuggingFaceEmbeddingsError
from .huggingface_embeddings import (
    DEFAULT_HUGGINGFACE_EMBEDDING_MODEL,
    DEFAULT_HUGGINGFACE_EMBEDDING_TIMEOUT,
    HuggingFaceEmbeddingClient,
)
from .qdrant_vector_store import (
    DEFAULT_QDRANT_COLLECTION,
    DEFAULT_QDRANT_URL,
    QdrantReadinessError,
    ingest_qdrant_documents,
    make_qdrant_client,
    search_qdrant_documents,
)

QDRANT_COMMANDS = {"qdrant-ingest", "qdrant-search", "qdrant-demo"}
DEFAULT_QDRANT_DOCUMENTS_PATH = Path("data/qdrant_sample_documents.json")
DEFAULT_QDRANT_QUERY = "how do I reset my password?"
DEFAULT_QDRANT_DEMO_QUERIES = (
    DEFAULT_QDRANT_QUERY,
    "wireless headphones with microphone and audio controls",
)


def add_qdrant_subcommands(subparsers: argparse._SubParsersAction) -> None:
    ingest_parser = subparsers.add_parser(
        "qdrant-ingest",
        help="Embed sample documents and upsert them into Qdrant",
    )
    _add_provider_options(ingest_parser)
    _add_qdrant_options(ingest_parser)
    ingest_parser.add_argument("--documents", type=Path, default=DEFAULT_QDRANT_DOCUMENTS_PATH)
    ingest_parser.add_argument("--recreate", action="store_true")

    search_parser = subparsers.add_parser(
        "qdrant-search",
        help="Run one semantic query against Qdrant",
    )
    _add_provider_options(search_parser)
    _add_qdrant_options(search_parser)
    search_parser.add_argument("--query", default=DEFAULT_QDRANT_QUERY)
    search_parser.add_argument("--top-k", type=int, default=5)

    demo_parser = subparsers.add_parser(
        "qdrant-demo",
        help="Run password and headphones semantic search demos",
    )
    _add_provider_options(demo_parser)
    _add_qdrant_options(demo_parser)
    demo_parser.add_argument("--top-k", type=int, default=5)


def run_qdrant_command(args: argparse.Namespace) -> int:
    try:
        if args.command == "qdrant-ingest":
            return _run_ingest(args)
        if args.command == "qdrant-search":
            return _run_search(args, [args.query])
        if args.command == "qdrant-demo":
            return _run_search(args, list(DEFAULT_QDRANT_DEMO_QUERIES))
    except (ValueError, OSError, HuggingFaceEmbeddingsError, QdrantReadinessError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    raise ValueError(f"Unknown Qdrant command: {args.command}")


def _add_provider_options(parser: argparse.ArgumentParser) -> None:
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


def _add_qdrant_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--qdrant-url", default=DEFAULT_QDRANT_URL)
    parser.add_argument("--qdrant-timeout", type=int, default=30)
    parser.add_argument("--collection", default=DEFAULT_QDRANT_COLLECTION)


def _run_ingest(args: argparse.Namespace) -> int:
    client = _qdrant_client_from_args(args)
    provider = _embedding_client_from_args(args)
    summary = ingest_qdrant_documents(
        client,
        load_documents(args.documents),
        provider,
        collection_name=args.collection,
        recreate=args.recreate,
    )
    print(f"Collection: {summary.collection_name}")
    print(f"Upserted points: {summary.point_count}")
    print(f"Vector size: {summary.vector_size}")
    print(f"Distance: {summary.distance}")
    print(f"Model: {summary.model}")
    return 0


def _run_search(args: argparse.Namespace, queries: list[str]) -> int:
    client = _qdrant_client_from_args(args)
    provider = _embedding_client_from_args(args)
    for query_index, query in enumerate(queries, start=1):
        if query_index > 1:
            print("")
        print(f"Query: {query}")
        matches = search_qdrant_documents(
            client,
            provider,
            query,
            collection_name=args.collection,
            top_k=args.top_k,
        )
        for index, match in enumerate(matches, start=1):
            print(
                f"{index}. score={match.score:.4f} source_id={match.source_id} "
                f"category={match.category} title={match.title}"
            )
            print(f"   text={match.text}")
    return 0


def _qdrant_client_from_args(args: argparse.Namespace):
    return make_qdrant_client(url=args.qdrant_url, timeout=args.qdrant_timeout)


def _embedding_client_from_args(args: argparse.Namespace) -> HuggingFaceEmbeddingClient:
    return HuggingFaceEmbeddingClient.from_env(
        model=args.model,
        base_url=args.base_url,
        timeout=args.timeout,
    )
