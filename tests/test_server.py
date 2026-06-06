"""Tests for the server entry point branch selection."""

from __future__ import annotations

import uvicorn

from kitoboy_mcp import deps, server


def test_main_serves_plain_streamable_http_without_token(monkeypatch):
    monkeypatch.setattr(deps.settings, "mcp_auth_token", None)
    captured: dict = {}
    monkeypatch.setattr(
        deps.mcp, "run", lambda transport: captured.update(transport=transport)
    )
    server.main()
    assert captured["transport"] == "streamable-http"


def test_main_wraps_with_bearer_when_token_set(monkeypatch):
    monkeypatch.setattr(deps.settings, "mcp_auth_token", "sek")

    class FakeApp:
        def __init__(self) -> None:
            self.middleware = None

        def add_middleware(self, _cls, **kwargs):
            self.middleware = kwargs

    fake_app = FakeApp()
    monkeypatch.setattr(deps.mcp, "streamable_http_app", lambda: fake_app)

    ran: dict = {}
    monkeypatch.setattr(
        uvicorn,
        "run",
        lambda app, host, port: ran.update(app=app, host=host, port=port),
    )

    server.main()
    assert ran["app"] is fake_app
    assert fake_app.middleware == {"token": "sek"}
