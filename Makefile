.PHONY: dev seed db-reset test up down

dev:
	cd backend && uvicorn app.main:app --reload --port 8000

seed:
	cd backend && python -m app.db.seed

db-reset:
	cd backend && python -m app.db.seed --reset

test:
	cd backend && pytest -q

up:
	docker compose up --build -d

down:
	docker compose down