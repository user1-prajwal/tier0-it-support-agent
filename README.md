# Tier0 — Permission-Aware IT Support Agent

Python, FastAPI, PostgreSQL with pgvector, Docker, GitHub Actions

![CI](https://github.com/user1-prajwal/tier0-it-support-agent/actions/workflows/ci.yml/badge.svg)

**Status: Phase 1 (ingestion and dense retrieval) complete.** The repository can ingest a small
synthetic corpus with per-document access levels, search it with a permission filter applied
inside the SQL query, and evaluate retrieval on a hand-labelled dev set. There is no
full-text search, reranking, login, LLM answering or agent yet. A baseline is recorded in
`docs/decisions/0001-phase-1.md`. The dev set is small and easy, so those numbers are a
starting point and not a claim about quality.

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
make up
make migrate
make ingest   # downloads the embedding model on first run
make eval ARGS="--no-record"
make test
```

Then open http://localhost:8000/health and http://localhost:8000/health/ready.

## Limitations

- Early-stage learning project. No claims about performance, retrieval quality or
  production use.
- Not yet covered: authentication, document permissions, LLM integration, evaluation.

## Decisions

- Design decisions are recorded in `docs/decisions/`.
- Evaluation so far is dense search only, on a small synthetic corpus labelled by the author.