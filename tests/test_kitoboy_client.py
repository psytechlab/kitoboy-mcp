"""Tests for the Kitoboy API client: auth lifecycle and error handling."""

from __future__ import annotations

import httpx
import pytest
import respx

from kitoboy_mcp.errors import KitoboyError
from kitoboy_mcp.kitoboy_client import KitoboyClient

BASE = "http://testapi"


def make_client() -> KitoboyClient:
    return KitoboyClient(BASE, "user", "pass", max_retries=2, retry_delay=0)


@respx.mock
async def test_login_caches_token():
    route = respx.post(f"{BASE}/login").mock(
        return_value=httpx.Response(200, json={"token": "tok123"})
    )
    client = make_client()
    await client.login()
    assert client._token == "tok123"
    assert route.called
    await client.aclose()


@respx.mock
async def test_request_attaches_bearer_and_returns_json():
    respx.post(f"{BASE}/login").mock(
        return_value=httpx.Response(200, json={"token": "T"})
    )
    route = respx.get(f"{BASE}/get-avatar/11").mock(
        return_value=httpx.Response(200, json={"id": "11"})
    )
    client = make_client()
    data = await client.get_avatar("11")
    assert data == {"id": "11"}
    assert route.calls.last.request.headers["authorization"] == "Bearer T"
    await client.aclose()


@respx.mock
async def test_relogin_once_on_401():
    login = respx.post(f"{BASE}/login").mock(
        side_effect=[
            httpx.Response(200, json={"token": "T1"}),
            httpx.Response(200, json={"token": "T2"}),
        ]
    )
    avatar = respx.get(f"{BASE}/get-avatar/11").mock(
        side_effect=[
            httpx.Response(401),
            httpx.Response(200, json={"id": "11"}),
        ]
    )
    client = make_client()
    data = await client.get_avatar("11")
    assert data == {"id": "11"}
    assert login.call_count == 2
    assert avatar.calls.last.request.headers["authorization"] == "Bearer T2"
    await client.aclose()


@respx.mock
async def test_error_status_raises_kitoboy_error():
    respx.post(f"{BASE}/login").mock(
        return_value=httpx.Response(200, json={"token": "T"})
    )
    respx.get(f"{BASE}/get-avatar/x").mock(
        return_value=httpx.Response(404, text="nope")
    )
    client = make_client()
    with pytest.raises(KitoboyError):
        await client.get_avatar("x")
    await client.aclose()


@respx.mock
async def test_login_bad_status_raises():
    respx.post(f"{BASE}/login").mock(return_value=httpx.Response(401))
    client = make_client()
    with pytest.raises(KitoboyError):
        await client.login()
    await client.aclose()


@respx.mock
async def test_login_missing_token_raises():
    respx.post(f"{BASE}/login").mock(
        return_value=httpx.Response(200, json={"message": "ok"})
    )
    client = make_client()
    with pytest.raises(KitoboyError):
        await client.login()
    await client.aclose()


@respx.mock
async def test_wait_for_login_retries_then_succeeds():
    respx.post(f"{BASE}/login").mock(
        side_effect=[
            httpx.Response(500),
            httpx.Response(200, json={"token": "T"}),
        ]
    )
    client = make_client()
    await client.wait_for_login()
    assert client._token == "T"
    await client.aclose()


@respx.mock
async def test_wait_for_login_exhausts_retries():
    respx.post(f"{BASE}/login").mock(return_value=httpx.Response(500))
    client = make_client()
    with pytest.raises(KitoboyError):
        await client.wait_for_login()
    await client.aclose()


@respx.mock
async def test_search_person_passes_query():
    respx.post(f"{BASE}/login").mock(
        return_value=httpx.Response(200, json={"token": "T"})
    )
    route = respx.get(f"{BASE}/search-person").mock(
        return_value=httpx.Response(200, json={"persons": []})
    )
    client = make_client()
    await client.search_person("Пупкин")
    assert route.calls.last.request.url.params["searchString"] == "Пупкин"
    await client.aclose()


@respx.mock
async def test_list_avatars_sends_pagination_body():
    respx.post(f"{BASE}/login").mock(
        return_value=httpx.Response(200, json={"token": "T"})
    )
    route = respx.post(f"{BASE}/get-avatars").mock(
        return_value=httpx.Response(200, json={"avatars": [], "page": 2, "pages": 5})
    )
    client = make_client()
    await client.list_avatars(2, 10)
    import json as _json

    body = _json.loads(route.calls.last.request.content)
    assert body == {"page": 2, "size": 10}
    await client.aclose()


@respx.mock
async def test_non_json_body_raises():
    respx.post(f"{BASE}/login").mock(
        return_value=httpx.Response(200, json={"token": "T"})
    )
    respx.get(f"{BASE}/get-statuses").mock(
        return_value=httpx.Response(200, text="not json")
    )
    client = make_client()
    with pytest.raises(KitoboyError):
        await client.list_statuses()
    await client.aclose()
