from pathlib import Path

import yaml
from pydantic_settings import BaseSettings


class ProjectSettings(BaseSettings):
    TOGETHER_API_KEY: str
    OPENAI_API_KEY: str
    GOOGLE_API_KEY: str
    BOT_KEY: str
    DATABASE_FILE: str = "thoughts.db"
    MAX_DB_SIZE: float
    MAX_AUDIO_FILE_SIZE_MB: int = 25  # Whisper API limit (can be overridden in .env)
    CLASSIFIER_PROMPT: str = ""
    CUSTOM_RETRIEVER_PROMPT: str = ""
    ANALYZING_PROMPT: str = ""


settings = ProjectSettings(_env_file=".env", _env_file_encoding="utf-8")

# Load prompts from YAML
curr_dir = Path(__file__).parent
yaml_path = curr_dir / "prompts.yaml"
if yaml_path.exists():
    with open(yaml_path, "r") as file:
        yaml_data = yaml.safe_load(file) or {}
    # Update prompts in settings
    settings.CLASSIFIER_PROMPT = yaml_data.get("CLASSIFIER_PROMPT", "")
    settings.CUSTOM_RETRIEVER_PROMPT = yaml_data.get("CUSTOM_RETRIEVER_PROMPT", "")
    settings.ANALYZING_PROMPT = yaml_data.get("ANALYZING_PROMPT", "")

if __name__ == "__main__":
    print(f"Together API Key: {settings.TOGETHER_API_KEY}")
    print(f"OpenAI API Key: {settings.OPENAI_API_KEY}")
    print(f"Google API Key: {settings.GOOGLE_API_KEY}")
    print(f"Telegram Bot Key: {settings.BOT_KEY}")
    print(f"Database file: {settings.DATABASE_FILE}")
    print(f"Max db size: {settings.MAX_DB_SIZE}")
