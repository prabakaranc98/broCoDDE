"""
BroCoDDE — Application Configuration
All settings are loaded from environment variables (via .env).
All AI calls are routed through OpenRouter (https://openrouter.ai).
"""

from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Environment ───────────────────────────────────────────────────────────
    environment: Literal["development", "staging", "production"] = "development"
    log_level: str = "INFO"
    secret_key: str = "change-me-in-production"

    # ── OpenRouter (unified AI provider) ──────────────────────────────────────
    # All models accessed via https://openrouter.ai/api/v1 (OpenAI-compatible API)
    openrouter_api_key: str = ""

    # ── Model Tier Overrides (optional — defaults defined in router.py) ───────
    # Set to an OpenRouter model path like "anthropic/claude-opus-4.6" to override
    tier1_model: str = "openai/gpt-4o-mini"
    tier2_model: str = "anthropic/claude-3.5-sonnet"
    tier3_model: str = "anthropic/claude-3.5-sonnet"

    # ── External APIs ─────────────────────────────────────────────────────────
    exa_api_key: str = ""  # https://exa.ai — used for Discovery web search

    # ── Database ──────────────────────────────────────────────────────────────
    database_url: str = "sqlite+aiosqlite:///./brocodde.db"

    # ── CORS ──────────────────────────────────────────────────────────────────
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://0.0.0.0:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    # ── Derived helpers ───────────────────────────────────────────────────────
    @property
    def is_development(self) -> bool:
        return self.environment == "development"

    @property
    def has_any_ai_key(self) -> bool:
        return bool(self.openrouter_api_key)

    @property
    def primary_provider(self) -> str:
        return "openrouter" if self.has_any_ai_key else "mock"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
