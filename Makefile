.PHONY: help install run docker-build docker-up docker-down clean

UV ?= uv
PYTHON ?= python
CONFIG_FILE ?= config.yaml

help:
	@echo "Available targets:"
	@echo "  make install      - Sync Python dependencies using uv"
	@echo "  make run          - Run the Telegram bot locally"
	@echo "  make docker-build - Build the Docker image"
	@echo "  make docker-up    - Start services with docker compose"
	@echo "  make docker-down  - Stop services started by docker compose"
	@echo "  make clean        - Remove runtime cache files"

install:
	$(UV) sync --frozen --no-dev

run:
	@test -f $(CONFIG_FILE) || (echo "Missing $(CONFIG_FILE). Copy config_example.yaml to $(CONFIG_FILE) first." && exit 1)
	$(UV) run $(PYTHON) src/main.py

docker-build:
	docker compose build

docker-up:
	docker compose up -d

docker-down:
	docker compose down

clean:
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
