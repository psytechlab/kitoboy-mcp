"""Shared FastMCP server, settings, and lazily-created upstream clients.

Clients are process-lifetime singletons created on first use (inside the serving
event loop). They are deliberately NOT managed by a FastMCP lifespan: in
stateless HTTP mode the low-level server enters the lifespan per request, so
per-request setup/teardown would close shared clients mid-flight.
"""

from __future__ import annotations

import logging

from mcp.server.fastmcp import FastMCP

from .config import Settings, load_settings
from .kitoboy_client import KitoboyClient
from .zoo_client import ZooClient

logger = logging.getLogger(__name__)

settings: Settings = load_settings()


class _State:
    """Holds the process-lifetime upstream client singletons."""

    kitoboy: KitoboyClient | None = None
    zoo: ZooClient | None = None


state = _State()


def require_kitoboy() -> KitoboyClient:
    """Return the shared Kitoboy client, creating it on first use."""
    if state.kitoboy is None:
        state.kitoboy = KitoboyClient(
            settings.kitoboy_api_url,
            settings.kitoboy_user,
            settings.kitoboy_password,
            timeout=settings.request_timeout,
            max_retries=settings.login_max_retries,
            retry_delay=settings.login_retry_delay,
        )
    return state.kitoboy


def require_zoo() -> ZooClient:
    """Return the shared Zoo client, creating it on first use."""
    if state.zoo is None:
        state.zoo = ZooClient(settings.zoo_url, timeout=settings.request_timeout)
    return state.zoo


mcp = FastMCP(
    "kitoboy",
    instructions=(
        "Read-only analysis tools over the Kitoboy suicide-prevention platform. "
        "Use them to summarize risk, triage wards, compare a person's avatars, "
        "explain ML labels, and audit contact leaks. You never change platform "
        "data — the volunteer sets statuses manually in the UI. Attribute labels "
        "carry NO confidence score; reason by class presence and frequency."
    ),
    host=settings.mcp_host,
    port=settings.mcp_port,
    json_response=True,
    stateless_http=True,
)
