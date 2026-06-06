"""Tests for the optional bearer-token guard."""

from __future__ import annotations

from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from kitoboy_mcp.middleware import BearerAuthMiddleware


def _build_app() -> Starlette:
    async def ok(_request):
        return PlainTextResponse("ok")

    app = Starlette(routes=[Route("/x", ok)])
    app.add_middleware(BearerAuthMiddleware, token="sek")
    return app


def test_rejects_request_without_token():
    client = TestClient(_build_app())
    assert client.get("/x").status_code == 401


def test_rejects_request_with_wrong_token():
    client = TestClient(_build_app())
    assert client.get("/x", headers={"Authorization": "Bearer nope"}).status_code == 401


def test_allows_request_with_correct_token():
    client = TestClient(_build_app())
    response = client.get("/x", headers={"Authorization": "Bearer sek"})
    assert response.status_code == 200
    assert response.text == "ok"
