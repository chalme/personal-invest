.PHONY: setup dev backend frontend init daily check clean

setup:
	./scripts/setup.sh

dev:
	./scripts/dev.sh

backend:
	./scripts/backend.sh

frontend:
	./scripts/frontend.sh

init:
	uv run python scripts/init_db.py

daily:
	uv run python worker/daily_job.py

check:
	./scripts/check.sh

clean:
	rm -rf .venv frontend/node_modules frontend/dist .run logs
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
