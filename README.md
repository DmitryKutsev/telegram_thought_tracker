# Thoughts Tracker

## Overview

**Thoughts Tracker** is a Telegram bot for logging and exploring your dreams, along with thoughts and plans. Send a text or voice message and the bot automatically classifies it, stores it in a local SQLite database, and lets you query or analyze your entries using natural language — all powered by LLMs.

## Features

- **Dream journaling**: Effortlessly capture dreams by text or voice right after waking up
- **Auto-classification**: Messages are classified as `dream`, `thought`, `plans`, `retrieve`, or `analyze` automatically
- **Voice-to-text**: Send a voice message and it gets transcribed before processing
- **Natural language retrieval**: Ask for your past dreams in plain text; the bot generates and runs the SQL query
- **LLM-powered dream analysis**: Ask for analysis of your dreams and get an LLM summary and interpretation
- **Multi-model support**: Switch between OpenAI and Together AI models via `/model`
- **Per-user isolation**: All data is scoped to the Telegram user ID

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (installed automatically by `make install`)
- Docker + Docker Compose (optional, for containerized deployment)
- API keys: OpenAI, Together AI, and/or Google

## Installation

### 1. Clone the repository

```bash
git clone <repo-url>
cd telegram_thought_tracker
```

### 2. Configure environment variables

```bash
cp .env_example .env
```

Edit `.env` and fill in your API keys:

```env
TOGETHER_API_KEY=your_together_api_key
OPENAI_API_KEY=your_openai_api_key
GOOGLE_API_KEY=your_google_api_key
BOT_KEY=your_telegram_bot_token
DATABASE_FILE=thoughts.db
MAX_DB_SIZE=1020054732.8
MAX_AUDIO_FILE_SIZE_MB=25
```

### 3. Configure the bot settings

```bash
cp config_example.yaml config.yaml
```

Edit `config.yaml` to adjust models, audio processing thresholds, and other settings.

### 4. Install dependencies

```bash
make install
```

This installs `uv` if needed and syncs all Python dependencies.

## Running

### Local

```bash
make run
```

Starts the bot in the background and logs output to `output.log`.

```bash
tail -f output.log   # follow logs
make clean_log       # clear the log file
```

### Docker

```bash
make run-docker
```

Builds the Docker image and starts the bot via Docker Compose. The `config.yaml` is mounted read-only and a `./data` volume is used for persistent storage.

```bash
make docker-down     # stop the bot
```

## Bot Usage

Once the bot is running, open it in Telegram and interact with it:

| Action | What to do |
|--------|-----------|
| Log a dream | Describe your dream — best done right after waking up |
| Use voice | Send a voice message — it will be transcribed automatically |
| Retrieve dreams | Ask in natural language, e.g. *"Show me my dreams from last week"* |
| Analyze dreams | Ask e.g. *"Analyze my dreams from this month"* |
| Log a thought or plan | Send any other text and it gets classified and stored |
| Switch model | Send `/model` and pick from the inline keyboard |

The bot auto-detects intent from the message — no special syntax or commands needed.

## Development

### Run tests

```bash
make test
```

### Clean cache

```bash
make clean
```

## Makefile reference

```
make install      Install uv and sync dependencies
make test         Run pytest
make run          Start bot locally in background
make run-docker   Build and start with Docker Compose
make docker-build Build Docker image
make docker-up    Start Docker Compose services
make docker-down  Stop Docker Compose services
make clean        Remove __pycache__ and .pyc files
make clean_log    Remove output.log
```
