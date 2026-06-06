"""Shared test fixtures."""

from __future__ import annotations

import pytest_asyncio

from kitoboy_mcp import deps
from kitoboy_mcp.kitoboy_client import KitoboyClient
from kitoboy_mcp.zoo_client import ZooClient

KITOBOY_BASE = "http://testapi"
ZOO_BASE = "http://testzoo"


@pytest_asyncio.fixture
async def wired():
    """Wire pre-authenticated upstream clients into the shared deps.state."""
    kito = KitoboyClient(KITOBOY_BASE, "user", "pass", max_retries=1, retry_delay=0)
    kito._token = "T"  # skip login in tool-level tests
    zoo = ZooClient(ZOO_BASE)
    deps.state.kitoboy = kito
    deps.state.zoo = zoo
    try:
        yield
    finally:
        await kito.aclose()
        await zoo.aclose()
        deps.state.kitoboy = None
        deps.state.zoo = None
