.PHONY: up down migrate lint test test-unit

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



# .PHONY: up down lint test

# up:
# 	docker compose up -d --wait

# down:
# 	docker compose down

# lint:
# 	ruff check .

# test:
# 	LLM_PROVIDER=fake pytest