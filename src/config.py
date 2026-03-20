"""
Centralized configuration loaded from environment variables.
All secrets and settings live here — never hardcode them elsewhere.
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    # Google Gemini
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "models/embedding-001")

    # GitHub
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")

    # AstraDB
    ASTRA_DB_API_ENDPOINT: str = os.getenv("ASTRA_DB_API_ENDPOINT", "")
    ASTRA_DB_APPLICATION_TOKEN: str = os.getenv("ASTRA_DB_APPLICATION_TOKEN", "")
    ASTRA_DB_KEYSPACE: str = os.getenv("ASTRA_DB_KEYSPACE", "")
    ASTRA_COLLECTION_NAME: str = os.getenv("ASTRA_COLLECTION_NAME", "github")

    # App
    APP_PASSWORD: str = os.getenv("APP_PASSWORD", "")
    RATE_LIMIT_MAX: int = int(os.getenv("RATE_LIMIT_MAX", "20"))
    RATE_LIMIT_WINDOW: int = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
    PORT: int = int(os.getenv("PORT", "8000"))

    @property
    def auth_enabled(self) -> bool:
        return bool(self.APP_PASSWORD)

    @property
    def astra_namespace(self) -> str | None:
        return self.ASTRA_DB_KEYSPACE or None


settings = Settings()
