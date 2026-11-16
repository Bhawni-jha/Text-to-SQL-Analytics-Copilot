import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    sample_db_url: str = os.getenv("SAMPLE_DB_URL", "")
    app_db_url: str = os.getenv("APP_DB_URL", "")
    groq_model: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    max_rows: int = int(os.getenv("MAX_ROWS", "1000"))
    timeout_seconds: int = int(os.getenv("QUERY_TIMEOUT_SECONDS", "10"))
    # 2 = first try + one retry with the error message sent back to the model
    max_attempts: int = int(os.getenv("MAX_ATTEMPTS", "2"))
    cors_origins: tuple = ("http://localhost:5173", "http://127.0.0.1:5173")


settings = Settings()
