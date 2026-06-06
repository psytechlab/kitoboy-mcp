"""Tests for environment-driven configuration."""

from __future__ import annotations

from kitoboy_mcp.config import Settings


def test_defaults_target_in_network_hosts():
    settings = Settings(_env_file=None)
    assert settings.kitoboy_api_url == "http://api:3052"
    assert settings.zoo_url == "http://zoo:8000"
    assert settings.mcp_port == 9000
    assert settings.mcp_auth_token is None


def test_env_overrides(monkeypatch):
    monkeypatch.setenv("KITOBOY_API_URL", "http://x:1")
    monkeypatch.setenv("MCP_PORT", "1234")
    monkeypatch.setenv("MCP_AUTH_TOKEN", "sekret")
    settings = Settings(_env_file=None)
    assert settings.kitoboy_api_url == "http://x:1"
    assert settings.mcp_port == 1234
    assert settings.mcp_auth_token == "sekret"
