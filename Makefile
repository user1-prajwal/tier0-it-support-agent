.PHONY: up down migrate lint test test-unit ingest eval

up:
	docker compose up -d --build --wait

down:
	docker compose down

migrate:
	alembic upgrade head

lint:
	ruff check .

test-unit:
	LLM_PROVIDER=fake pytest tests/unit

test:
	LLM_PROVIDER=fake pytest

ingest:
	python -m app.ingest.cli corpus

eval:
	python -m eval.run_eval $(ARGS)

seed:
	python -m app.db.seed


# .PHONY: up down lint test

# up:
# 	docker compose up -d --wait

# down:
# 	docker compose down

# lint:
# 	ruff check .

# test:
# 	LLM_PROVIDER=fake pytest