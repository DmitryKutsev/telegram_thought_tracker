from pydantic_settings import BaseSettings


class ProjectSettings(BaseSettings):
    TOGETHER_API_KEY: str
    OPENAI_API_KEY: str
    GOOGLE_API_KEY: str
    BOT_KEY: str
    DATABASE_FILE: str = "thoughts.db"
    MAX_DB_SIZE: float

settings = ProjectSettings(_env_file=".env", _env_file_encoding="utf-8")

if __name__ == "__main__":
    print(f"Together API Key: {settings.TOGETHER_API_KEY}")
    print(f"OpenAI API Key: {settings.OPENAI_API_KEY}")
    print(f"Google API Key: {settings.GOOGLE_API_KEY}")
    print(f"Telegram Bot Key: {settings.TG_BOT_KEY}")
    print(f"Database file: {settings.DATABASE_FILE}")
    print(f"Max db size: {settings.MAX_DB_SIZE}")
