"""Environment-backed application configuration."""

from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Shared settings with safeguards around deliberately vulnerable modes."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"
    database_url: str = "sqlite:///./qualitypilot.db"
    jwt_secret: str = "local-development-secret-change-me-32-chars"
    access_token_minutes: int = Field(default=15, ge=1)
    refresh_token_minutes: int = Field(default=1440, ge=2)
    login_rate_limit: int = Field(default=5, ge=1)
    login_rate_window_seconds: int = Field(default=60, ge=1)
    qualitypilot_api_url: str = "http://localhost:8001"
    demo_app_url: str = "http://localhost:8000"
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:3b"

    defect_disable_refresh_rotation: bool = False
    defect_allow_expired_tokens: bool = False
    defect_break_admin_auth: bool = False
    defect_delay_ms: int = Field(default=0, ge=0, le=30_000)
    defect_incorrect_status: bool = False
    defect_unstable_selector: bool = False
    defect_random_failure: bool = False
    defect_malformed_json: bool = False

    @model_validator(mode="after")
    def reject_production_defects(self) -> "Settings":
        defect_values = [
            self.defect_disable_refresh_rotation,
            self.defect_allow_expired_tokens,
            self.defect_break_admin_auth,
            self.defect_delay_ms > 0,
            self.defect_incorrect_status,
            self.defect_unstable_selector,
            self.defect_random_failure,
            self.defect_malformed_json,
        ]
        if self.environment.lower() == "production" and any(defect_values):
            raise ValueError("demo defect flags are forbidden in production")
        if self.environment.lower() == "production" and len(self.jwt_secret) < 32:
            raise ValueError("JWT_SECRET must contain at least 32 characters in production")
        return self


@lru_cache
def get_settings() -> Settings:
    """Return the cached process settings."""

    return Settings()
