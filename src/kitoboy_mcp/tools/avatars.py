"""Avatar-centric MCP tools."""

from __future__ import annotations

from ..deps import mcp, require_kitoboy
from ..models import AvatarView, ListAvatarsResult


@mcp.tool()
async def kitoboy_list_avatars(page: int = 1, size: int = 30) -> ListAvatarsResult:
    """List avatars (social accounts) one page at a time, newest first.

    Each avatar carries its person, status, and posts with ML attribute labels.
    Use for triage and weekly review across many wards; page through with
    `page`/`size` and the returned `pages` count. There is no server-side person
    filter here — for one person's avatars use kitoboy_get_person instead.
    """
    return ListAvatarsResult.model_validate(
        await require_kitoboy().list_avatars(page, size)
    )


@mcp.tool()
async def kitoboy_get_avatar(avatar_id: str) -> AvatarView:
    """Full card of a single avatar: linked person, status, and all posts.

    Each post lists its ML attribute labels (class id, human name, color).
    Main read endpoint for analysing one account. Note: labels carry no
    confidence score — reason by class presence and frequency, not weight.
    """
    return AvatarView.model_validate(await require_kitoboy().get_avatar(avatar_id))
