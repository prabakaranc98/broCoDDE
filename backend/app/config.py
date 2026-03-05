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

    # ── Model Tier Overrides ──────────────────────────────────────────────────
    # Tier 1: Standard utility — grammar checks, memory writes
    # Tier 2: Balanced — Interviewer, Shaper, majority of conversations
    # Tier 3: Most capable — Strategist Discovery, Analyst post-mortem, deep critique
    tier1_model: str = "anthropic/claude-sonnet-4.6"          # standard utility tasks
    tier2_model: str = "anthropic/claude-sonnet-4.6"          # balanced — main conversations
    tier3_model: str = "google/gemini-3.1-pro-preview"        # critical reasoning and analysis

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

    @field_validator("tier1_model", "tier2_model", "tier3_model", mode="before")
    @classmethod
    def fallback_empty_model(cls, v, info):
        """If the env var is set but blank, fall back to the field default."""
        if isinstance(v, str) and not v.strip():
            defaults = {
                "tier1_model": "anthropic/claude-sonnet-4.6",
                "tier2_model": "anthropic/claude-sonnet-4.6",
                "tier3_model": "google/gemini-3.1-pro-preview",
            }
            return defaults.get(info.field_name, v)
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
