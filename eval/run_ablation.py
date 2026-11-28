"""Retrieval ablation on the DEV split: dense, full-text, hybrid (RRF), hybrid + rerank.

    python -m eval.run_ablation                # measure, record a row, write docs/EVAL.md
    python -m eval.run_ablation --prefix bge   # same, with the BGE query instruction
    python -m eval.run_ablation --no-record    # print only

Commit before a recorded run, so the commit hash identifies what was measured. docs/EVAL.md
is only written for a clean tree and for the default (no prefix) setting. The test split is
deliberately not available: it is run once, at the end of the project.
"""

import argparse
import json
import statistics
import time
from collections.abc import Callable
from pathlib import Path

from sqlalchemy import text

from app.config import Settings
from app.db.session import get_engine
from app.retrieval.embedder import BGE_QUERY_PREFIX, FastEmbedEmbedder
from app.retrieval.fusion import RRF_K
from app.retrieval.rerank import FastEmbedReranker, rerank_hits
from app.retrieval.retrieve import CANDIDATES, KEEP
from app.retrieval.search import PER_ARM, dense_search, fulltext_search, hybrid_search
from eval.dataset import load_questions, missing_gold, split_of
from eval.metrics import (
    all_gold_in_top_k,
    compare_ranks,
    first_gold_rank,
    mean_reciprocal_rank,
    recall_at_k,
    sign_test_p,
)
from eval.run_eval import (
    QUESTIONS_FILE,
    RECORD_SQL,
    SECTIONS_SQL,
    git,
    group_ids_of,
    unreachable_gold,
)

DEPTH = 10  # chunks kept per question: enough for Recall@10
DOC_PATH = Path("docs/EVAL.md")
METHODS = [
    ("dense", "Dense only"),
    ("fulltext", "Full-text only"),
    ("hybrid", "Hybrid (RRF)"),
    ("hybrid_rerank", "Hybrid + rerank"),
]
LABEL = dict(METHODS)
COMPARISONS = [  # (base, other): how does `other` do compared with `base`?
    ("dense", "hybrid"),
    ("fulltext", "hybrid"),
    ("hybrid", "hybrid_rerank"),
    ("dense", "hybrid_rerank"),
]

CHUNKS_SQL = text(
    "SELECT count(*) FROM chunks c JOIN documents d ON d.id = c.document_id"
    " WHERE d.status = 'active'"
)
READABLE_SQL = text(
    """
    SELECT count(*) FROM chunks c JOIN documents d ON d.id = c.document_id
    WHERE d.status = 'active'
      AND EXISTS (
          SELECT 1 FROM document_acl a
          WHERE a.document_id = d.id AND a.group_id = ANY(CAST(:group_ids AS bigint[]))
      )
    """
)
SECTION_SIZE_SQL = text(
    """
    SELECT count(*) FROM chunks c JOIN documents d ON d.id = c.document_id
    WHERE d.status = 'active' AND d.source_uri = :uri AND c.heading_path = :heading
    """
)


def build_methods(engine, embedder, reranker) -> dict[str, Callable]:
    """Each method goes from a question to a ranked list, including embedding the question."""

    def dense(question, group_ids):
        return dense_search(engine, embedder.embed_query(question), group_ids, limit=DEPTH)

    def fulltext(question, group_ids):
        return fulltext_search(engine, question, group_ids, limit=DEPTH)

    def hybrid(question, group_ids):
        hits = hybrid_search(engine, embedder, question, group_ids, limit=CANDIDATES)
        return hits[:DEPTH]

    def hybrid_rerank(question, group_ids):
        hits = hybrid_search(engine, embedder, question, group_ids, limit=CANDIDATES)
        return rerank_hits(reranker, question, hits, keep=DEPTH)

    return {
        "dense": dense,
        "fulltext": fulltext,
        "hybrid": hybrid,
        "hybrid_rerank": hybrid_rerank,
    }


def summarize(ranks: list[int | None]) -> dict:
    stats: dict = {"n": len(ranks), "mrr": round(mean_reciprocal_rank(ranks), 4)}
    for k in (1, 5, 10):
        stats[f"found_at_{k}"] = sum(1 for r in ranks if r is not None and r <= k)
        stats[f"recall_at_{k}"] = round(recall_at_k(ranks, k), 4)
    return stats


def count_all_gold(found: dict, questions: list, k: int) -> int:
    return sum(all_gold_in_top_k(found[q.id], list(q.gold), k) for q in questions)


def md_table(headers: list[str], rows: list[list]) -> list[str]:
    lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    lines += ["| " + " | ".join(str(cell) for cell in row) + " |" for row in rows]
    return lines


def recall_cell(stats: dict, k: int) -> str:
    return f"{stats[f'recall_at_{k}']:.3f} ({stats[f'found_at_{k}']}/{stats['n']})"


def render_doc(config: dict, metrics: dict, run_id: int, commit: str) -> str:
    n, stats = metrics["n"], metrics["methods"]
    low, high, arm = (
        config["readable_chunks_min"],
        config["readable_chunks_max"],
        config["per_arm_candidates"],
    )
    reach = f"Each search arm returns up to {arm} chunks and the askers may read {low} to {high}"
    if high <= arm:
        coverage = (
            f"{reach} chunks, so every arm can return everything the asker may read. "
            "Candidate generation cannot miss here, and the table measures ranking only."
        )
    else:
        coverage = f"{reach} chunks, so an arm can miss a relevant chunk."

    out = [
        "# Retrieval evaluation",
        "",
        f"Generated by `make ablation` from `eval_runs` row {run_id}, measured at commit "
        f"`{commit}` on the dev split. Do not edit by hand: re-run the command instead.",
        "",
        "## Setup",
        "",
        f"- Corpus: {config['n_documents']} synthetic documents, {config['n_chunks']} chunks.",
        f"- Questions: {config['n_questions_total']} labelled in total. This run scored the "
        f"{n} answerable questions in the dev split. The test split was not run.",
        f"- Models: embedding `{config['embedding_model']}`, reranker "
        f"`{config['rerank_model']}`. Query prefix: `{config['query_prefix']}`.",
        f"- Fusion: RRF with k = {config['rrf_k']}. The top {config['rerank_candidates']} "
        f"fused chunks go to the reranker. Metrics use the top {config['metric_depth']}. "
        f"The service keeps {config['production_keep']}.",
        f"- {coverage}",
        "",
        "## Ablation",
        "",
        *md_table(
            ["Method", "Recall@1", "Recall@5", "Recall@10", "MRR", "Median latency (ms)", "n"],
            [
                [
                    label,
                    recall_cell(stats[key], 1),
                    recall_cell(stats[key], 5),
                    recall_cell(stats[key], 10),
                    f"{stats[key]['mrr']:.3f}",
                    f"{stats[key]['median_ms']:.1f}",
                    n,
                ]
                for key, label in METHODS
            ],
        ),
        "",
    ]

    categories = list(metrics["by_category"])
    headers = ["Method"] + [
        f"{c} (n={metrics['by_category'][c]['dense']['n']})" for c in categories
    ]
    rows = [
        [label] + [f"{metrics['by_category'][c][key]['mrr']:.3f}" for c in categories]
        for key, label in METHODS
    ]
    out += ["## MRR by question category", "", *md_table(headers, rows), ""]

    multi = metrics["multi_chunk_all_gold"]
    if multi:
        m = multi["dense"]["n"]
        rows = [
            [label, f"{multi[key]['at_5']}/{m}", f"{multi[key]['at_10']}/{m}"]
            for key, label in METHODS
        ]
        out += [
            f"## Multi-chunk questions: all gold sections retrieved (n = {m})",
            "",
            *md_table(["Method", "All gold in top 5", "All gold in top 10"], rows),
            "",
        ]

    rows = [
        [
            f"{LABEL[c['other']]} vs {LABEL[c['base']]}",
            c["better"],
            c["worse"],
            c["same"],
            f"{c['p']:.3f}",
        ]
        for c in metrics["comparisons"]
    ]
    out += [
        "## Paired comparisons",
        "",
        "For each pair: on how many questions the second method ranked the first correct chunk "
        "higher (better), lower (worse) or equally (same) than the first. The p-value is a "
        "two-sided exact sign test over the questions that differ.",
        "",
        *md_table(["Comparison", "Better", "Worse", "Same", "Sign-test p"], rows),
        "",
        "## Questions the final configuration did not rank first",
        "",
    ]
    if metrics["not_ranked_first"]:
        for item in metrics["not_ranked_first"]:
            found = ", ".join(
                f"{LABEL[key]} {rank if rank is not None else '>10'}"
                for key, rank in item["ranks"].items()
            )
            out.append(f"- {item['id']} ({item['category']}): {found}")
    else:
        out.append("None.")

    out += [
        "",
        "## Limits of this evaluation",
        "",
        f"- A small synthetic corpus and {config['n_questions_total']} questions labelled by "
        "the author. No real users.",
        f"- {config['llm_drafted_questions']} of the {config['n_questions_total']} questions "
        "are marked `llm_drafted`: first drafted by an LLM, then reviewed and edited by the "
        "author.",
        "- The corpus documents were first drafted with an LLM and then edited by the author.",
        "- Gold labels are sections (document plus heading path). A hit means some chunk of the "
        f"gold section was retrieved. {config['gold_sections_split']} of the "
        f"{config['gold_sections']} gold sections span more than one chunk; for those, a hit "
        "may not be the chunk that holds the answer.",
        "- Several questions share a gold section, so the questions are not independent and "
        "the effective n is smaller than listed. The sign-test p-values ignore this and are "
        "optimistic.",
        "- Only the dev split was run. The test split is run once, at the end of the project.",
        f"- Latency is the median over {n} questions on one machine (CPU only). It includes "
        "embedding the question and the database round trips, and excludes one warm-up call. "
        "It describes this laptop and is not a benchmark.",
        "- Group memberships were read once per run. An offline evaluation changes none. The "
        "running service reads them on every request.",
        "",
    ]
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Retrieval ablation on the dev split.")
    parser.add_argument("--prefix", choices=["none", "bge"], default="none")
    parser.add_argument("--no-record", action="store_true", help="print only")
    args = parser.parse_args(argv)

    settings = Settings()
    engine = get_engine()
    questions = load_questions(QUESTIONS_FILE)
    records = [json.loads(line) for line in QUESTIONS_FILE.read_text().splitlines() if line.strip()]
    llm_drafted = sum(1 for r in records if r.get("llm_drafted") is True)

    with engine.connect() as conn:
        rows = conn.execute(SECTIONS_SQL).all()
        total_chunks = conn.execute(CHUNKS_SQL).scalar_one()
    known = {(r.source_uri, r.heading_path) for r in rows}
    models = {r.embedding_model for r in rows}

    bad = missing_gold(questions, known)
    if bad:
        print("gold labels that match no ingested section:", bad)
        return 1
    unreachable = unreachable_gold(engine, questions)
    if unreachable:
        print("questions whose gold the asker may not read:", unreachable)
        return 1
    if models != {settings.embed_model}:
        print(f"the database holds {sorted(models)},the configured model is {settings.embed_model}")
        return 1

    scored = [q for q in questions if q.answerable and split_of(q.id) == "dev"]
    if not scored:
        print("no answerable dev questions to score")
        return 1
    n = len(scored)

    embedder = FastEmbedEmbedder(
        settings.embed_model,
        cache_dir=settings.embed_cache_dir,
        query_prefix=BGE_QUERY_PREFIX if args.prefix == "bge" else "",
    )
    reranker = FastEmbedReranker(settings.rerank_model, cache_dir=settings.embed_cache_dir)
    methods = build_methods(engine, embedder, reranker)

    # Groups are read once per run: an offline evaluation changes no memberships.
    groups = {email: group_ids_of(engine, email) for email in {q.asked_by for q in scored}}

    first = scored[0]
    for method in methods.values():  # one untimed call each: the first ONNX call is slower
        method(first.question, groups[first.asked_by])

    retrieved: dict[str, dict[str, list[tuple[str, str]]]] = {}
    millis: dict[str, list[float]] = {}
    for key, method in methods.items():
        retrieved[key], millis[key] = {}, []
        for q in scored:
            started = time.perf_counter()
            hits = method(q.question, groups[q.asked_by])
            millis[key].append((time.perf_counter() - started) * 1000)
            retrieved[key][q.id] = [(h.source_uri, h.heading_path) for h in hits][:DEPTH]

    ranks = {
        key: [first_gold_rank(retrieved[key][q.id], list(q.gold)) for q in scored]
        for key in methods
    }

    method_stats = {
        key: {**summarize(ranks[key]), "median_ms": round(statistics.median(millis[key]), 1)}
        for key in methods
    }
    by_category = {}
    for category in sorted({q.category for q in scored}):
        idx = [i for i, q in enumerate(scored) if q.category == category]
        by_category[category] = {
            key: summarize([ranks[key][i] for i in idx]) for key in methods
        }
    multi = [q for q in scored if q.category == "multi_chunk"]
    multi_all = {}
    if multi:
        multi_all = {
            key: {
                "n": len(multi),
                "at_5": count_all_gold(retrieved[key], multi, 5),
                "at_10": count_all_gold(retrieved[key], multi, 10),
            }
            for key in methods
        }

    comparisons = []
    for base, other in COMPARISONS:
        better, worse, same = compare_ranks(ranks[base], ranks[other])
        p = round(sign_test_p(better, worse), 4)
        comparisons.append(
            {"base": base, "other": other, "better": better, "worse": worse, "same": same, "p": p}
        )

    final = ranks["hybrid_rerank"]
    not_first = [
        {"id": q.id, "category": q.category, "ranks": {key: ranks[key][i] for key in methods}}
        for i, q in enumerate(scored)
        if final[i] != 1
    ]

    with engine.connect() as conn:
        readable = [
            conn.execute(READABLE_SQL, {"group_ids": ids}).scalar_one() for ids in groups.values()
        ]
        gold_sections = {g for q in scored for g in q.gold}
        sizes = [
            conn.execute(SECTION_SIZE_SQL, {"uri": uri, "heading": heading}).scalar_one()
            for uri, heading in gold_sections
        ]

    print(f"ablation | split: dev | n = {n} | query prefix: {args.prefix}")
    print(f"{'method':<17}{'R@1':>10}{'R@5':>10}{'R@10':>10}{'MRR':>8}{'ms':>9}")
    for key, label in METHODS:
        s = method_stats[key]
        print(
            f"{label:<17}{s['recall_at_1']:>10.3f}{s['recall_at_5']:>10.3f}"
            f"{s['recall_at_10']:>10.3f}{s['mrr']:>8.3f}{s['median_ms']:>9.1f}"
        )
    for c in comparisons:
        print(
            f"  {LABEL[c['other']]} vs {LABEL[c['base']]}: better {c['better']}, "
            f"worse {c['worse']}, same {c['same']}, p = {c['p']:.3f}"
        )
    print(f"  not ranked first by the final configuration: {[x['id'] for x in not_first]}")
    print(f"  readable chunks per asker: {min(readable)} to {max(readable)}")

    if args.no_record:
        print("not recorded (--no-record)")
        return 0

    commit, dirty = git("rev-parse", "HEAD"), bool(git("status", "--porcelain"))
    config = {
        "kind": "ablation",
        "query_prefix": args.prefix,
        "embedding_model": settings.embed_model,
        "rerank_model": settings.rerank_model,
        "per_arm_candidates": PER_ARM,
        "rrf_k": RRF_K,
        "rerank_candidates": CANDIDATES,
        "metric_depth": DEPTH,
        "production_keep": KEEP,
        "n_documents": len({uri for uri, _ in known}),
        "n_chunks": total_chunks,
        "n_questions_total": len(questions),
        "llm_drafted_questions": llm_drafted,
        "gold_sections": len(sizes),
        "gold_sections_split": sum(1 for size in sizes if size > 1),
        "readable_chunks_min": min(readable),
        "readable_chunks_max": max(readable),
        "dirty_worktree": dirty,
    }
    metrics = {
        "n": n,
        "methods": method_stats,
        "by_category": by_category,
        "multi_chunk_all_gold": multi_all,
        "comparisons": comparisons,
        "not_ranked_first": not_first,
    }
    with engine.begin() as conn:
        run_id = conn.execute(
            RECORD_SQL,
            {
                "commit": commit,
                "n": n,
                "config": json.dumps(config),
                "metrics": json.dumps(metrics),
            },
        ).scalar_one()
    print(f"recorded eval_runs id={run_id} at commit {commit[:10]}")

    if dirty:
        print("warning: uncommitted changes. The row is flagged dirty and EVAL.md was NOT written")
    elif args.prefix != "none":
        print("docs/EVAL.md was not written: it always describes the default (no prefix) setting")
    else:
        DOC_PATH.write_text(render_doc(config, metrics, run_id, commit), encoding="utf-8")
        print(f"wrote {DOC_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())