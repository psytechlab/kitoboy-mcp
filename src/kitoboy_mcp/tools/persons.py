"""Person-centric MCP tools."""

from __future__ import annotations

from ..deps import mcp, require_kitoboy
from ..models import PersonWithAvatars, SearchPersonsResult


@mcp.tool()
async def kitoboy_search_person(query: str) -> SearchPersonsResult:
    """Search people (objects of observation) by a substring of their name.

    Matches surname / name / secondName case-insensitively and returns up to 20
    people with their profile fields and overall status id. Use this to resolve
    a person_id before calling kitoboy_get_person.
    """
    return SearchPersonsResult.model_validate(
        await require_kitoboy().search_person(query)
    )


@mcp.tool()
async def kitoboy_get_person(person_id: str) -> PersonWithAvatars:
    """Full card of one person: profile, overall status, and ALL their avatars.

    Each avatar includes its own status and posts with ML attribute labels.
    Use for cross-avatar comparison (e.g. public vs anonymous account), case
    similarity, and status decision support.
    """
    return PersonWithAvatars.model_validate(
        await require_kitoboy().get_person_with_avatars(person_id)
    )
