"""Tests for the Zoo inference client."""

from __future__ import annotations

import json as _json

import httpx
import pytest
import respx

from kitoboy_mcp.errors import ZooError
from kitoboy_mcp.zoo_client import ZooClient

BASE = "http://testzoo"


@respx.mock
async def test_predict_on_text_sends_text_list_and_returns_classes():
    route = respx.post(f"{BASE}/predict_on_text").mock(
        return_value=httpx.Response(
            200, json=[["клинические проявления/депрессия"], ["нерелевантный"]]
        )
    )
    client = ZooClient(BASE)
    result = await client.predict_on_text(["a", "b"])
    assert result == [["клинические проявления/депрессия"], ["нерелевантный"]]
    body = _json.loads(route.calls.last.request.content)
    assert body == {"text_list": ["a", "b"]}
    await client.aclose()


@respx.mock
async def test_predict_raw_returns_raw_strings():
    respx.post(f"{BASE}/predict").mock(return_value=httpx.Response(200, json=[["x;y"]]))
    client = ZooClient(BASE)
    assert await client.predict_raw(["t"]) == [["x;y"]]
    await client.aclose()


@respx.mock
async def test_list_services():
    respx.get(f"{BASE}/show_services").mock(
        return_value=httpx.Response(
            200, json=[{"url": "u:8000", "model_name": "presui"}]
        )
    )
    client = ZooClient(BASE)
    services = await client.list_services()
    assert services[0]["model_name"] == "presui"
    await client.aclose()


@respx.mock
async def test_zoo_error_on_500():
    respx.post(f"{BASE}/predict").mock(return_value=httpx.Response(500, text="boom"))
    client = ZooClient(BASE)
    with pytest.raises(ZooError):
        await client.predict_raw(["t"])
    await client.aclose()
