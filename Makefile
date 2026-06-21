.PHONY: setup dev dev\:server prod prod-server doctor doctor-server health health-server backend backend-prod frontend frontend-prod init daily check backup clean

setup:
	./scripts/setup.sh

dev:
	./scripts/dev.sh

dev\:server:
	ENV_FILE=.env.server ./scripts/dev.sh

prod:
	./scripts/prod.sh

prod-server:
	ENV_FILE=.env.server ./scripts/prod.sh

doctor:
	./scripts/doctor.sh

doctor-server:
	ENV_FILE=.env.server ./scripts/doctor.sh


health:
	./scripts/health.sh

health-server:
	ENV_FILE=.env.server ./scripts/health.sh

backend:
	./scripts/backend.sh

backend-prod:
	./scripts/backend_prod.sh

frontend:
	./scripts/frontend.sh

frontend-prod:
	./scripts/frontend_prod.sh

init:
	./.venv/bin/python scripts/init_db.py

daily:
	./.venv/bin/python worker/daily_job.py

check:
	./scripts/check.sh

backup:
	./scripts/backup.sh

clean:
	rm -rf .venv frontend/node_modules frontend/dist .run logs
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
