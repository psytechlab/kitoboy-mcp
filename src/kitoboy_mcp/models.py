"""Pydantic models mirroring the real Kitoboy / Zoo response shapes.

Fields are intentionally permissive: the upstream API serializes missing
relations as empty objects (`{}`) and uses loose typing, so every field is
optional. Unknown/extra fields (timestamps, soft-delete markers) are ignored to
keep tool output focused.

Important real-API facts reflected here: post attributes carry NO weight /
confidence score, attribute ids are UUIDs (identify a class by `name`).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class _Base(BaseModel):
    model_config = ConfigDict(extra="ignore")


class AttributeRef(_Base):
    """An ML annotation class attached to a post (or in the dictionary)."""

    id: str | None = None
    name: str | None = None
    color: str | None = None


class StatusRef(_Base):
    """A suicide-risk status reference."""

    id: str | None = None
    name: str | None = None
    color: str | None = None


class PostView(_Base):
    """A post with its ML attribute labels (no confidence score exists)."""

    id: str | None = None
    text: str | None = None
    postedAt: str | None = None
    attributes: list[AttributeRef] = []


class PersonRef(_Base):
    """The person summary embedded inside an avatar card."""

    id: str | None = None
    surname: str | None = None
    name: str | None = None
    secondName: str | None = None
    age: str | None = None


class AvatarView(_Base):
    """Full avatar (social account) card: person, status, posts with attributes."""

    id: str | None = None
    username: str | None = None
    url: str | None = None
    person: PersonRef | None = None
    status: StatusRef | None = None
    posts: list[PostView] = []


class AvatarInPerson(_Base):
    """Avatar as returned inside a person card (without the nested person field)."""

    id: str | None = None
    username: str | None = None
    url: str | None = None
    status: StatusRef | None = None
    posts: list[PostView] = []


class Person(_Base):
    """A person row as returned by search-person (full profile fields)."""

    id: str | None = None
    surname: str | None = None
    name: str | None = None
    secondName: str | None = None
    age: str | None = None
    address: str | None = None
    phone: str | None = None
    organization: str | None = None
    description: str | None = None
    statusId: str | None = None


class PersonWithAvatars(_Base):
    """A person card with overall status and all their avatars."""

    id: str | None = None
    surname: str | None = None
    name: str | None = None
    secondName: str | None = None
    age: str | None = None
    address: str | None = None
    phone: str | None = None
    organization: str | None = None
    description: str | None = None
    status: StatusRef | None = None
    avatars: list[AvatarInPerson] = []


class ServiceInfo(_Base):
    """A connected Triton model service."""

    url: str | None = None
    model_name: str | None = None


# --- Tool result envelopes (mirror the API's response wrappers) ---


class SearchPersonsResult(_Base):
    persons: list[Person] = []


class ListAvatarsResult(_Base):
    avatars: list[AvatarView] = []
    page: int | None = None
    pages: int | None = None


class ListAttributesResult(_Base):
    attributes: list[AttributeRef] = []


class ListStatusesResult(_Base):
    statuses: list[StatusRef] = []
