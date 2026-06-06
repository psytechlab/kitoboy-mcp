"""Reference-dictionary MCP tools (attributes and statuses)."""

from __future__ import annotations

from ..deps import mcp, require_kitoboy
from ..models import ListAttributesResult, ListStatusesResult


@mcp.tool()
async def kitoboy_list_attributes() -> ListAttributesResult:
    """Dictionary of ML annotation classes (up to 100).

    Each class has a UUID `id`, a human-readable Russian `name`, and a `color`.
    Identify a class by its `name` (ids are random UUIDs and differ per install).
    PIE/contact classes include 'номер телефона', 'номер карты банка', 'эл. почта',
    'телеграм', 'вк'.
    """
    return ListAttributesResult.model_validate(
        await require_kitoboy().list_attributes()
    )


@mcp.tool()
async def kitoboy_list_statuses() -> ListStatusesResult:
    """Dictionary of suicide-risk statuses configured in the platform.

    Returns each status id with its human-readable name and color. Read these at
    runtime rather than assuming a fixed set — the available statuses are defined
    by the platform's data.
    """
    return ListStatusesResult.model_validate(await require_kitoboy().list_statuses())
