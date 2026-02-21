.PHONY: help install test run run-docker docker-build docker-up docker-down clean clean_log

CONFIG_FILE ?= config.yaml
LOG_FILE ?= output.log

help:
	@echo "Available targets:"
	@echo "  make install      - Install uv (if needed) and sync Python dependencies"
	@echo "  make test         - Install dev dependencies and run pytest"
	@echo "  make run          - Sync dependencies and run locally in background logging to $(LOG_FILE)"
	@echo "  make run-docker   - Build and run the Telegram bot using Docker Compose"
	@echo "  make docker-build - Build the Docker image"
	@echo "  make docker-up    - Start services with docker compose"
	@echo "  make docker-down  - Stop services started by docker compose"
	@echo "  make clean        - Remove runtime cache files"
	@echo "  make clean_log    - Remove $(LOG_FILE)"

install:
	@command -v uv >/dev/null 2>&1 || python -m pip install uv
	uv sync --frozen --no-dev

test:
	@command -v uv >/dev/null 2>&1 || python -m pip install uv
	uv sync --frozen --group dev
	uv run pytest

run:
	@test -f $(CONFIG_FILE) || (echo "Missing $(CONFIG_FILE). Copy config_example.yaml to $(CONFIG_FILE) first." && exit 1)
	uv sync --frozen --no-dev
	uv run python src/main.py > $(LOG_FILE) 2>&1 &

run-docker: docker-build docker-up

docker-build:
	docker compose build

docker-up:
	docker compose up -d

docker-down:
	docker compose down

clean:
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

clean_log:
	rm -f $(LOG_FILE)
