"""Zoo ML inference MCP tools (stateless classification)."""

from __future__ import annotations

from ..deps import mcp, require_zoo
from ..models import ServiceInfo


@mcp.tool()
async def zoo_classify_text(texts: list[str]) -> list[list[str]]:
    """Classify free text, post-processed: human-readable class names per input.

    Drops the 'нерелевантный' (irrelevant) class when any relevant class is
    present. Stateless — does NOT touch the platform DB. Use for pre-flight
    checks of a draft message. No confidence scores are returned.
    """
    return await require_zoo().predict_on_text(texts)


@mcp.tool()
async def zoo_classify_text_raw(texts: list[str]) -> list[list[str]]:
    """Raw classification: raw model class strings per input, no post-processing.

    Multi-label results are joined by ';' and may include 'нерелевантный'.
    Stateless. No confidence scores are returned.
    """
    return await require_zoo().predict_raw(texts)


@mcp.tool()
async def zoo_list_services() -> list[ServiceInfo]:
    """List the Triton model services currently connected to the Zoo hub."""
    data = await require_zoo().list_services()
    return [ServiceInfo.model_validate(item) for item in data]
