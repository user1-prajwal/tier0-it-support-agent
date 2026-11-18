.PHONY: up down lint test

up:
	docker compose up -d --wait

down:
	docker compose down

lint:
	ruff check .

test:
	LLM_PROVIDER=fake pytest