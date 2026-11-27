"""Run the leakage matrix on the REAL database with the real models, and record the result.

    python -m eval.run_leakage

The query for each active document is its title plus the heading of its first section.
Run `make ingest` first, and commit before a recorded run so the hash identifies what was
measured.
"""

import json

from sqlalchemy import text

from app.config import Settings
from app.db.demo_users import DEMO_USERS
from app.db.session import get_engine
from app.db.users import get_user_by_email
from app.retrieval.embedder import FastEmbedEmbedder
from app.retrieval.rerank import FastEmbedReranker
from app.retrieval.retrieve import retrieve
from eval.leakage import Probe, run_matrix
from eval.run_eval import git

USERS = [user.email for user in DEMO_USERS if user.is_active]
EVERYONE = {"alice@demo.local", "bob@demo.local", "carol@demo.local", "dave@demo.local"}
# Who may read what, by classification. Written out by hand and NOT imported from the
# ingestion code, so the matrix checks that code instead of trusting it.
READERS_BY_CLASSIFICATION = {
    "public": EVERYONE,
    "internal": EVERYONE,
    "it_restricted": {"bob@demo.local", "carol@demo.local"},
    "security_restricted": {"carol@demo.local"},
    "hr_confidential": {"dave@demo.local"},
}

DOCS_SQL = text(
    """
    SELECT d.source_uri, d.title, d.classification,
           (SELECT c.heading_path FROM chunks c
            WHERE c.document_id = d.id ORDER BY c.ordinal LIMIT 1) AS first_heading
    FROM documents d
    WHERE d.status = 'active'
    ORDER BY d.source_uri
    """
)
RECORD_SQL = text(
    """
    INSERT INTO eval_runs (git_commit, split, n_questions, config, metrics)
    VALUES (:commit, 'none', :n, CAST(:config AS jsonb), CAST(:metrics AS jsonb))
    RETURNING id
    """
)


def main() -> int:
    settings = Settings()
    engine = get_engine()
    with engine.connect() as conn:
        docs = conn.execute(DOCS_SQL).all()
    if not docs:
        print("no active documents. Run `make ingest` first.")
        return 1

    classification = {d.source_uri: d.classification for d in docs}
    probes = [Probe(d.source_uri, f"{d.title}. {d.first_heading}") for d in docs]
    embedder = FastEmbedEmbedder(settings.embed_model, cache_dir=settings.embed_cache_dir)
    reranker = FastEmbedReranker(settings.rerank_model, cache_dir=settings.embed_cache_dir)

    def fetch(email: str, question: str) -> list[str]:
        user = get_user_by_email(engine, email)
        hits = retrieve(engine, embedder, reranker, question, user.group_ids)
        return [hit.source_uri for hit in hits]

    def may_read(email: str, uri: str) -> bool:
        return email in READERS_BY_CLASSIFICATION[classification[uri]]

    result = run_matrix(USERS, probes, fetch, may_read)

    print(f"leakage matrix | hybrid + rerank | {len(USERS)} users x {len(docs)} documents")
    print(f"  pairs  = {result.pairs}")
    print(f"  leaks  = {len(result.leaks)}   (must be 0)")
    print(f"  misses = {len(result.misses)}   (a readable document that was not returned)")
    for user, probed, leaked in result.leaks:
        print(f"  LEAK: {user} asking about {probed} was shown {leaked}")
    for user, uri in result.misses:
        print(f"  miss: {user} did not get {uri}")

    commit, dirty = git("rev-parse", "HEAD"), bool(git("status", "--porcelain"))
    if dirty:
        print("warning: uncommitted changes, so this commit hash does not reproduce the run")
    config = {
        "kind": "leakage_matrix",
        "retrieval": "hybrid+rerank",
        "embedding_model": settings.embed_model,
        "rerank_model": settings.rerank_model,
        "users": USERS,
        "documents": len(docs),
        "probe": "title + first heading",
        "dirty_worktree": dirty,
    }
    metrics = {"pairs": result.pairs, "leaks": len(result.leaks), "misses": len(result.misses)}
    with engine.begin() as conn:
        run_id = conn.execute(
            RECORD_SQL,
            {
                "commit": commit,
                "n": result.pairs,
                "config": json.dumps(config),
                "metrics": json.dumps(metrics),
            },
        ).scalar_one()
    print(f"recorded eval_runs id={run_id} at commit {commit[:10]}")
    return 1 if result.leaks else 0


if __name__ == "__main__":
    raise SystemExit(main())