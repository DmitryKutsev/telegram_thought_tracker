from pathlib import Path
from typing import Any

import yaml
from pydantic import model_validator
from pydantic_settings import BaseSettings

_root = Path(__file__).parent.parent


class ProjectSettings(BaseSettings):
    TOGETHER_API_KEY: str
    OPENAI_API_KEY: str
    GOOGLE_API_KEY: str
    BOT_KEY: str

    @model_validator(mode="after")
    def _require_keys(self) -> "ProjectSettings":
        missing = [
            k
            for k in ("TOGETHER_API_KEY", "OPENAI_API_KEY", "GOOGLE_API_KEY", "BOT_KEY")
            if not getattr(self, k)
        ]
        if missing:
            raise ValueError(f"Missing required env vars: {missing}")
        return self

    DATABASE_FILE: str = ""
    MAX_DB_SIZE: float = 0.0
    MAX_AUDIO_FILE_SIZE_MB: int = 0
    AUDIO_TRANSCRIPTION_MODEL: str = ""
    AUDIO_SILENCE_MIN_LEN_MS: int = 0
    AUDIO_SILENCE_THRESH_DB: int = 0
    AUDIO_KEEP_SILENCE_MS: int = 0
    AUDIO_FALLBACK_CHUNK_MIN: int = 0
    MAX_TOKENS_FOR_ANALYSIS: int = 0
    CHUNK_SIZE_TOKENS: int = 0
    DEFAULT_MODEL: str = ""
    OPENAI_MODELS_LIST: list[str] = []
    TOGETHER_MODELS_LIST: list[str] = []
    PLACEHOLDER_USER_INPUT: str = ""
    PLACEHOLDER_DREAMS_THOUGHTS: str = ""
    PLACEHOLDER_DREAMS_CONTENT: str = ""
    CLASSIFIER_PROMPT: str = ""
    CUSTOM_RETRIEVER_PROMPT: str = ""
    ANALYZING_PROMPT: str = ""
    SUMMARIZATION_PROMPT: str = ""


settings = ProjectSettings(_env_file=_root / ".env", _env_file_encoding="utf-8")  # pyright: ignore[reportCallIssue]

with open(_root / "config.yaml") as f:
    _cfg: dict[str, Any] = yaml.safe_load(f) or {}

for _key, _value in _cfg.items():
    if hasattr(settings, _key):
        setattr(settings, _key, _value)

_prompts_path = Path(__file__).parent / "prompts.yaml"

if _prompts_path.exists():
    with open(_prompts_path) as f:
        _prompts: dict[str, Any] = yaml.safe_load(f) or {}

    settings.CLASSIFIER_PROMPT = _prompts.get("CLASSIFIER_PROMPT", "")
    settings.CUSTOM_RETRIEVER_PROMPT = _prompts.get("CUSTOM_RETRIEVER_PROMPT", "")
    settings.ANALYZING_PROMPT = _prompts.get("ANALYZING_PROMPT", "")
    settings.SUMMARIZATION_PROMPT = _prompts.get("SUMMARIZATION_PROMPT", "")
