# Tier0 — Permission-Aware IT Support Agent

Python, FastAPI, PostgreSQL with pgvector, Docker, GitHub Actions

![CI](https://github.com/user1-prajwal/tier0-it-support-agent/actions/workflows/ci.yml/badge.svg)

**Status: Phase 1 (ingestion and dense retrieval) complete.** The repository can ingest a small
synthetic corpus with per-document access levels, search it with a permission filter applied
inside the SQL query, and evaluate retrieval on a hand-labelled dev set. There is no
full-text search, reranking, login, LLM answering or agent yet. A baseline is recorded in
`docs/decisions/0001-phase-1.md`. The dev set is small and easy, so those numbers are a
starting point and not a claim about quality.

**Status: Phase 2 (hybrid retrieval, users, login, leakage test) complete.** The repository
ingests a small synthetic corpus with per-document access levels, searches it with dense,
full-text and hybrid retrieval plus a reranker (permissions are applied inside the SQL of
each search), authenticates demo users, and measures retrieval on a hand-labelled dev set.
There is no LLM answering, abstention or agent yet. The documents and part of the question
set were first drafted with an LLM and then edited by the author.

## Goal

Tier0 is planned as an IT-support assistant that answers questions from a knowledge base
where every document has an access level, and performs routine IT actions only after a
policy check and, for state-changing actions, a human approval. The design is described
in the build brief.

## What is simulated

Everything. The workspace is a "demo workspace" with synthetic users, groups and documents.
Any IT systems (accounts, groups, ticketing) will be simulated tables. There is no real
directory, Okta or ServiceNow integration, and there are no real users.

## Quick start (current state)

Requires Docker, Python 3.12 and make (developed on WSL2 with Ubuntu 24.04).

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.lock && pip install -e . --no-deps
cp .env.example .env
sed -i "s/change-me/$(openssl rand -hex 16)/g" .env
```

The `.env` file also requires `DEMO_PASSWORD` and `JWT_SECRET`. Set suitable local secret values before running the application. The `.env` file is git-ignored; never commit it.

```bash
make up
make migrate
make seed
make ingest   # downloads the embedding model on first run
make eval ARGS="--no-record"
make ablation
make test
```

Then open http://localhost:8000/health and http://localhost:8000/health/ready.


## Results

Dev split, 45 answerable questions, a synthetic corpus of 20 documents (110 chunks), row
[FILL: id] at commit [FILL: hash]. Tables, paired tests and limits: [docs/EVAL.md](docs/EVAL.md).

| Method | Recall@1 | Recall@5 | Recall@10 | MRR | Median latency (ms) | n |
|---|---|---|---|---|---|---|
| Dense only | 0.733 (33/45) | 1.000 (45/45) | 1.000 (45/45) | 0.838 | 20.0 | 45 |
| Full-text only | 0.622 (28/45) | 0.889 (40/45) | 0.911 (41/45) | 0.723 | 4.5 | 45 |
| Hybrid (RRF) | 0.711 (32/45) | 0.933 (42/45) | 0.956 (43/45) | 0.803 | 27.2 | 45 |
| Hybrid + rerank | 0.800 (36/45) | 0.978 (44/45) | 0.978 (44/45) | 0.863 | 1217.3 | 45 |

On this corpus no method detectably beats dense-only retrieval (paired sign tests, see
`docs/decisions/0003-ablation.md`), and reranking costs about 60 times the latency. Hybrid
retrieval beats full-text alone. The corpus is small and the questions are partly correlated,
so these are descriptive results, not a claim about retrieval quality in general.

**Permission leakage:** 80 user-document pairs, 0 leaks, 0 misses (row [FILL: id], commit
[FILL: hash]). It covers the retrieval function. The chat endpoint and the payload sent to the
language model are tested in later phases. Response timing is not measured or claimed.

## Limitations

- Early-stage learning project. No claims about performance, retrieval quality or
  production use.
- Not yet covered: authentication, document permissions, LLM integration, evaluation.

## Decisions

- Design decisions are recorded in `docs/decisions/`.
- Evaluation so far is dense search only, on a small synthetic corpus labelled by the author.