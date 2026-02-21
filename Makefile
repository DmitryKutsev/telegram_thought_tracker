.PHONY: help install run run-docker docker-build docker-up docker-down clean

CONFIG_FILE ?= config.yaml
LOG_FILE ?= output.log

help:
	@echo "Available targets:"
	@echo "  make install      - Install uv (if needed) and sync Python dependencies"
	@echo "  make run          - Sync dependencies, run locally, and write logs to $(LOG_FILE)"
	@echo "  make run-docker   - Build and run the Telegram bot using Docker Compose"
	@echo "  make docker-build - Build the Docker image"
	@echo "  make docker-up    - Start services with docker compose"
	@echo "  make docker-down  - Stop services started by docker compose"
	@echo "  make clean        - Remove runtime cache files and $(LOG_FILE)"

install:
	@command -v uv >/dev/null 2>&1 || python -m pip install uv
	uv sync --frozen --no-dev

run:
	@test -f $(CONFIG_FILE) || (echo "Missing $(CONFIG_FILE). Copy config_example.yaml to $(CONFIG_FILE) first." && exit 1)
	uv sync --frozen --no-dev
	uv run python src/main.py 2>&1 | tee $(LOG_FILE)

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
	rm -f $(LOG_FILE)
