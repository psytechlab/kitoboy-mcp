"""Tests for the lazily-created upstream client singletons."""

from __future__ import annotations

from kitoboy_mcp import deps


async def test_require_helpers_create_and_reuse_singletons():
    deps.state.kitoboy = None
    deps.state.zoo = None
    try:
        kitoboy_first = deps.require_kitoboy()
        kitoboy_second = deps.require_kitoboy()
        zoo_first = deps.require_zoo()
        zoo_second = deps.require_zoo()
        # Same instance is reused across calls (one client per process).
        assert kitoboy_first is kitoboy_second
        assert zoo_first is zoo_second
    finally:
        if deps.state.kitoboy is not None:
            await deps.state.kitoboy.aclose()
        if deps.state.zoo is not None:
            await deps.state.zoo.aclose()
        deps.state.kitoboy = None
        deps.state.zoo = None
