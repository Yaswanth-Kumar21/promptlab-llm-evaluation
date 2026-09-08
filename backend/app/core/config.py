"""
Application configuration.

All settings are read from environment variables (or a .env file via
python-dotenv).  Pydantic-Settings validates types and provides defaults.

Usage:
    from app.core.config import settings
    print(settings.app_env)
"""

from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",          # silently ignore unknown env vars
    )

    # ── Application ───────────────────────────────────────────────────────────
    app_name: str = "PromptLab"
    app_version: str = "0.1.0"
    app_env: str = "development"
    app_secret_key: str = "change-me-to-a-random-secret-string"
    log_level: str = "INFO"

    # ── Server ────────────────────────────────────────────────────────────────
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000

    # ── CORS ──────────────────────────────────────────────────────────────────
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        """Return CORS origins as a Python list."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    # ── Database ──────────────────────────────────────────────────────────────
    database_url: str = "sqlite:///./promptlab.db"

    # ── LLM Providers ─────────────────────────────────────────────────────────
    openai_api_key: str = ""
    openai_default_model: str = "gpt-4o-mini"

    anthropic_api_key: str = ""
    anthropic_default_model: str = "claude-3-haiku-20240307"

    gemini_api_key: str = ""
    gemini_default_model: str = "gemini-1.5-flash"

    mistral_api_key: str = ""
    mistral_default_model: str = "mistral-small-latest"

    default_provider: str = "mock"

    # ── Embeddings ────────────────────────────────────────────────────────────
    embedding_provider: str = "local"
    embedding_model: str = "all-MiniLM-L6-v2"

    # ── ChromaDB ──────────────────────────────────────────────────────────────
    chroma_persist_dir: str = "./chroma_data"

    # ── File uploads ──────────────────────────────────────────────────────────
    max_upload_size_mb: int = 10
    upload_dir: str = "./rag/documents"

    # ── Rate limiting ─────────────────────────────────────────────────────────
    rate_limit_per_minute: int = 60

    # ── Derived helpers ───────────────────────────────────────────────────────
    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    def provider_is_configured(self, provider: str) -> bool:
        """Return True if the given provider has an API key set."""
        key_map = {
            "openai": self.openai_api_key,
            "anthropic": self.anthropic_api_key,
            "gemini": self.gemini_api_key,
            "mistral": self.mistral_api_key,
            "mock": "always-configured",   # mock never needs a key
        }
        key = key_map.get(provider.lower(), "")
        return bool(key and key.strip())


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached singleton Settings instance."""
    return Settings()


# Convenient module-level alias so callers can simply do:
#   from app.core.config import settings
settings = get_settings()
