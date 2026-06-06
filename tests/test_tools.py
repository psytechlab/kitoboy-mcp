"""Tests for tool registration and response parsing."""

from __future__ import annotations

import httpx
import respx

from kitoboy_mcp.deps import mcp
from kitoboy_mcp.tools.avatars import kitoboy_get_avatar, kitoboy_list_avatars
from kitoboy_mcp.tools.classify import (
    zoo_classify_text,
    zoo_classify_text_raw,
    zoo_list_services,
)
from kitoboy_mcp.tools.persons import kitoboy_get_person, kitoboy_search_person
from kitoboy_mcp.tools.reference import kitoboy_list_attributes, kitoboy_list_statuses

KITO = "http://testapi"
ZOO = "http://testzoo"

EXPECTED_TOOLS = {
    "kitoboy_search_person",
    "kitoboy_get_person",
    "kitoboy_list_avatars",
    "kitoboy_get_avatar",
    "kitoboy_list_attributes",
    "kitoboy_list_statuses",
    "zoo_classify_text",
    "zoo_classify_text_raw",
    "zoo_list_services",
}


async def test_all_nine_tools_registered():
    tools = await mcp.list_tools()
    assert {t.name for t in tools} == EXPECTED_TOOLS


@respx.mock
async def test_search_person_parses_and_drops_extra_fields(wired):
    respx.get(f"{KITO}/search-person").mock(
        return_value=httpx.Response(
            200,
            json={
                "persons": [
                    {
                        "id": "123",
                        "surname": "Пупкин",
                        "name": "Василий",
                        "phone": "+7(999)999-99-99",
                        "createdAt": "2025-01-01T00:00:00Z",
                        "deletedAt": None,
                    }
                ]
            },
        )
    )
    result = await kitoboy_search_person("Пупкин")
    assert result.persons[0].surname == "Пупкин"
    assert result.persons[0].phone == "+7(999)999-99-99"
    # Noise fields are ignored, not surfaced to the LLM.
    assert "createdAt" not in result.persons[0].model_dump()


@respx.mock
async def test_get_avatar_handles_empty_relations_and_no_weight(wired):
    respx.get(f"{KITO}/get-avatar/11").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "11",
                "username": "kroko_Gen_04",
                "url": "https://soc.net/kroko_Gen_04",
                "person": {},
                "status": {},
                "posts": [
                    {
                        "id": "801",
                        "text": "сегодня тяжело",
                        "postedAt": "2025-04-10T12:38:22.922Z",
                        "attributes": [
                            {
                                "id": "uuid-1",
                                "name": "клинические проявления/депрессия",
                                "color": "#fff",
                            }
                        ],
                    }
                ],
            },
        )
    )
    result = await kitoboy_get_avatar("11")
    assert result.id == "11"
    attribute = result.posts[0].attributes[0]
    assert attribute.name == "клинические проявления/депрессия"
    # weight does not exist anywhere in the platform.
    assert "weight" not in attribute.model_dump()


@respx.mock
async def test_get_person_parses_status_and_avatars(wired):
    respx.get(f"{KITO}/get-person-with-avatars/123").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "123",
                "surname": "Пупкин",
                "name": "Василий",
                "status": {"id": "suicide", "name": "Опасный", "color": "#FFBC42"},
                "avatars": [
                    {"id": "11", "username": "k", "url": "u", "status": {}, "posts": []}
                ],
            },
        )
    )
    result = await kitoboy_get_person("123")
    assert result.status.id == "suicide"
    assert result.avatars[0].id == "11"


@respx.mock
async def test_list_avatars_parses_pagination(wired):
    respx.post(f"{KITO}/get-avatars").mock(
        return_value=httpx.Response(200, json={"avatars": [], "page": 1, "pages": 3})
    )
    result = await kitoboy_list_avatars(1, 30)
    assert result.page == 1
    assert result.pages == 3


@respx.mock
async def test_reference_tools_parse(wired):
    respx.get(f"{KITO}/get-attributes").mock(
        return_value=httpx.Response(
            200,
            json={
                "attributes": [{"id": "u", "name": "номер телефона", "color": "#fff"}]
            },
        )
    )
    respx.get(f"{KITO}/get-statuses").mock(
        return_value=httpx.Response(
            200,
            json={
                "statuses": [{"id": "suicide", "name": "Опасный", "color": "#FFBC42"}]
            },
        )
    )
    attributes = await kitoboy_list_attributes()
    statuses = await kitoboy_list_statuses()
    assert attributes.attributes[0].name == "номер телефона"
    assert statuses.statuses[0].id == "suicide"


@respx.mock
async def test_zoo_tools_parse(wired):
    respx.post(f"{ZOO}/predict_on_text").mock(
        return_value=httpx.Response(200, json=[["клинические проявления/депрессия"]])
    )
    respx.post(f"{ZOO}/predict").mock(return_value=httpx.Response(200, json=[["x;y"]]))
    respx.get(f"{ZOO}/show_services").mock(
        return_value=httpx.Response(
            200, json=[{"url": "u:8000", "model_name": "presui"}]
        )
    )
    assert await zoo_classify_text(["a"]) == [["клинические проявления/депрессия"]]
    assert await zoo_classify_text_raw(["a"]) == [["x;y"]]
    services = await zoo_list_services()
    assert services[0].model_name == "presui"
