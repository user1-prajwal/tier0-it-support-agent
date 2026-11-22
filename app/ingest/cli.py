"""Ingest every .md and .txt file under a folder. Safe to run again.

    python -m app.ingest.cli corpus
"""

import argparse
from pathlib import Path

from app.config import Settings
from app.db.session import get_engine
from app.ingest.loader import DocumentError
from app.ingest.pipeline import EmbeddingModelMismatch, ingest_file
from app.retrieval.embedder import FastEmbedEmbedder

SUFFIXES = {".md", ".txt"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ingest documents into Tier0.")
    parser.add_argument("root", nargs="?", type=Path, default=Path("corpus"))
    args = parser.parse_args(argv)

    files = sorted(p for p in args.root.rglob("*") if p.is_file() and p.suffix.lower() in SUFFIXES)
    if not files:
        print(f"no .md or .txt files found under {args.root}")
        return 1

    settings = Settings()
    embedder = FastEmbedEmbedder(settings.embed_model, cache_dir=settings.embed_cache_dir)
    engine = get_engine()

    failed = 0
    for path in files:
        try:
            result = ingest_file(engine, path, args.root, embedder)
        except DocumentError as exc:
            failed += 1
            print(f"FAILED     {path}: {exc}")
        except EmbeddingModelMismatch as exc:
            print(f"STOPPED    {exc}")
            return 2
        else:
            print(f"{result.action:<10} {result.source_uri} ({result.chunks_written} chunks)")

    print(f"done: {len(files) - failed} ok, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())