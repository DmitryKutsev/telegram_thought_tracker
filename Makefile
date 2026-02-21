.PHONY: help install run run-docker docker-build docker-up docker-down clean

CONFIG_FILE ?= config.yaml

help:
	@echo "Available targets:"
	@echo "  make install      - Install uv (if needed) and sync Python dependencies"
	@echo "  make run          - Update uv and run the Telegram bot in the local environment"
	@echo "  make run-docker   - Build and run the Telegram bot using Docker Compose"
	@echo "  make docker-build - Build the Docker image"
	@echo "  make docker-up    - Start services with docker compose"
	@echo "  make docker-down  - Stop services started by docker compose"
	@echo "  make clean        - Remove runtime cache files"

install:
	@command -v uv >/dev/null 2>&1 || python -m pip install uv
	uv sync --frozen --no-dev

run:
	@test -f $(CONFIG_FILE) || (echo "Missing $(CONFIG_FILE). Copy config_example.yaml to $(CONFIG_FILE) first." && exit 1)
	python -m pip install --upgrade uv
	uv run python src/main.py

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
