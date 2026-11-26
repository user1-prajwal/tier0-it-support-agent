"""Retrieval evaluation on the DEV split (dense search only, for now).

    python -m eval.run_eval               # no query prefix
    python -m eval.run_eval --prefix bge  # with the BGE query instruction

Commit corpus/ and eval/questions/ before a recorded run, so the commit hash identifies
exactly what was measured. The test split is deliberately not available yet: it is run
once, at the end of the project.
"""

import argparse
import json
import subprocess
from pathlib import Path

from sqlalchemy import Engine, text

from app.config import Settings
from app.db.session import get_engine
from app.db.users import get_user_by_email
from app.retrieval.embedder import BGE_QUERY_PREFIX, FastEmbedEmbedder
from app.retrieval.search import dense_search
from eval.dataset import load_questions, missing_gold, split_of
from eval.metrics import first_gold_rank, mean_reciprocal_rank, recall_at_k

QUESTIONS_FILE = Path("eval/questions/questions.jsonl")
RETRIEVED = 10  # chunks fetched per question: enough for Recall@10

SECTIONS_SQL = text(
    """
    SELECT DISTINCT d.source_uri, c.heading_path, c.embedding_model
    FROM chunks c JOIN documents d ON d.id = c.document_id
    WHERE d.status = 'active'
    """
)
READABLE_SQL = text(
    """
    SELECT DISTINCT d.source_uri, c.heading_path
    FROM chunks c JOIN documents d ON d.id = c.document_id
    WHERE d.status = 'active'
      AND EXISTS (
          SELECT 1 FROM document_acl a
          WHERE a.document_id = d.id AND a.group_id = ANY(CAST(:group_ids AS bigint[]))
      )
    """
)
RECORD_SQL = text(
    """
    INSERT INTO eval_runs (git_commit, split, n_questions, config, metrics)
    VALUES (:commit, 'dev', :n, CAST(:config AS jsonb), CAST(:metrics AS jsonb))
    RETURNING id
    """
)


def git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout.strip()


def group_ids_of(engine: Engine, email: str) -> list[int]:
    """Group ids for an active seeded user, read from the database on every call."""
    user = get_user_by_email(engine, email)
    if user is None or not user.is_active:
        raise SystemExit(f"{email} is not an active user in the database. Run `make seed`.")
    return list(user.group_ids)


def unreachable_gold(engine: Engine, questions) -> list:
    """Gold labels the asking user may not read: such a question can never be found."""
    readable: dict[str, set[tuple[str, str]]] = {}
    problems = []
    for q in questions:
        if q.asked_by not in readable:
            group_ids = group_ids_of(engine, q.asked_by)
            with engine.connect() as conn:
                rows = conn.execute(READABLE_SQL, {"group_ids": group_ids}).all()
            readable[q.asked_by] = {(r.source_uri, r.heading_path) for r in rows}
        problems += [(q.id, q.asked_by, g) for g in q.gold if g not in readable[q.asked_by]]
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate retrieval on the dev split.")
    parser.add_argument("--prefix", choices=["none", "bge"], default="none")
    parser.add_argument("--no-record", action="store_true", help="print metrics, write no row")
    args = parser.parse_args(argv)

    questions = load_questions(QUESTIONS_FILE)
    settings = Settings()
    engine = get_engine()

    with engine.connect() as conn:
        rows = conn.execute(SECTIONS_SQL).all()
    known = {(r.source_uri, r.heading_path) for r in rows}
    models = {r.embedding_model for r in rows}

    bad = missing_gold(questions, known)
    if bad:
        print("These gold labels match no ingested section (a typo, or run `make ingest`):")
        for question_id, (uri, heading) in bad:
            print(f"  {question_id}: {uri} | {heading}")
        return 1
    unreachable = unreachable_gold(engine, questions)
    if unreachable:
        print("These questions can never be answered by the user who asks them (no read access):")
        for question_id, asker, (uri, heading) in unreachable:
            print(f"  {question_id}: {asker} cannot read {uri} | {heading}")
        return 1
    if models != {settings.embed_model}:
        print(
            f"the database holds {sorted(models)} "
            f"but the configured model is {settings.embed_model}"
        )
        return 1

    scored = [q for q in questions if q.answerable and split_of(q.id) == "dev"]
    if not scored:
        print("no answerable dev questions to score")
        return 1

    embedder = FastEmbedEmbedder(
        settings.embed_model,
        cache_dir=settings.embed_cache_dir,
        query_prefix=BGE_QUERY_PREFIX if args.prefix == "bge" else "",
    )

    ranks: list[int | None] = []
    for q in scored:
        group_ids = group_ids_of(engine, q.asked_by)
        hits = dense_search(engine, embedder.embed_query(q.question), group_ids, limit=RETRIEVED)
        ranks.append(first_gold_rank([(h.source_uri, h.heading_path) for h in hits], list(q.gold)))

    n = len(scored)
    found5 = sum(1 for r in ranks if r is not None and r <= 5)
    found10 = sum(1 for r in ranks if r is not None and r <= 10)

    by_category: dict[str, list[int | None]] = {}
    for q, rank in zip(scored, ranks, strict=True):
        by_category.setdefault(q.category, []).append(rank)

    metrics = {
        "n": n,
        "recall_at_5": round(recall_at_k(ranks, 5), 4),
        "recall_at_10": round(recall_at_k(ranks, 10), 4),
        "mrr": round(mean_reciprocal_rank(ranks), 4),
        "by_category": {
            category: {
                "n": len(cat_ranks),
                "recall_at_5": round(recall_at_k(cat_ranks, 5), 4),
                "mrr": round(mean_reciprocal_rank(cat_ranks), 4),
            }
            for category, cat_ranks in sorted(by_category.items())
        },
    }

    print(f"dense search | query prefix: {args.prefix} | split: dev | n = {n}")
    print(f"  Recall@5  = {metrics['recall_at_5']:.3f}  ({found5} of {n} questions)")
    print(f"  Recall@10 = {metrics['recall_at_10']:.3f}  ({found10} of {n} questions)")
    print(f"  MRR       = {metrics['mrr']:.3f}")
    for category, stats in metrics["by_category"].items():
        print(
            f"  {category:<16} n={stats['n']:<3} "
            f"Recall@5={stats['recall_at_5']:.2f}  "
            f"MRR={stats['mrr']:.2f}"
        )
    for q, rank in zip(scored, ranks, strict=True):
        if rank != 1:
            print(f"  not ranked first: {q.id} ({q.category}) -> rank {rank or 'beyond 10'}")

    if args.no_record:
        print("not recorded (--no-record)")
        return 0

    commit, dirty = git("rev-parse", "HEAD"), bool(git("status", "--porcelain"))
    if dirty:
        print("warning: uncommitted changes, so this commit hash does not reproduce the run")
    config = {
        "method": "dense",
        "embedding_model": settings.embed_model,
        "query_prefix": args.prefix,
        "retrieved_per_question": RETRIEVED,
        "n_documents": len({uri for uri, _ in known}),
        "n_sections": len(known),
        "dirty_worktree": dirty,
    }
    with engine.begin() as conn:
        run_id = conn.execute(
            RECORD_SQL,
            {"commit": commit, "n": n, "config": json.dumps(config),
             "metrics": json.dumps(metrics)},
        ).scalar_one()
    print(f"recorded eval_runs id={run_id} at commit {commit[:10]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())