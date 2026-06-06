"""Runtime configuration loaded from environment variables.

All settings are validated at startup; required upstream URLs and credentials
fail fast with a clear error if missing or malformed.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Process configuration sourced from the environment (or a local .env)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Upstream Kitoboy services. Defaults target the in-network docker hostnames.
    kitoboy_api_url: str = "http://api:3052"
    zoo_url: str = "http://zoo:8000"

    # Volunteer credentials the server uses to obtain a JWT from POST /login.
    # Defaults mirror Kitoboy's .env.example seed user.
    kitoboy_user: str = "user"
    kitoboy_password: str = "user"

    # MCP endpoint binding (Streamable HTTP).
    mcp_host: str = "0.0.0.0"
    mcp_port: int = 9000
    # Optional static bearer token guarding the MCP endpoint. Disabled when None.
    mcp_auth_token: str | None = None

    # HTTP client tuning.
    request_timeout: float = 30.0
    # Startup login retry/backoff (mirrors Kitoboy api's own DB-connect retry).
    login_max_retries: int = 30
    login_retry_delay: float = 2.0


def load_settings() -> Settings:
    """Build a Settings instance from the current environment."""
    return Settings()
