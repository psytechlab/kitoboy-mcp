"""Async HTTP client for the Zoo inference service.

Zoo is unauthenticated and reachable only inside the docker network. All calls
are stateless (they never write to the platform DB). Failures surface as
ZooError. NOTE: Zoo returns class labels only — there are no confidence scores.
"""

from __future__ import annotations

from typing import Any

import httpx

from .errors import ZooError


class ZooClient:
    """Thin async wrapper over the Zoo stateless inference endpoints."""

    def __init__(self, base_url: str, *, timeout: float = 30.0) -> None:
        self._client = httpx.AsyncClient(base_url=base_url.rstrip("/"), timeout=timeout)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def _request(
        self, method: str, path: str, *, json: dict[str, Any] | None = None
    ) -> Any:
        try:
            resp = await self._client.request(method, path, json=json)
        except httpx.RequestError as exc:
            raise ZooError(f"Zoo {method} {path} failed: {exc}") from exc

        if resp.status_code >= 400:
            raise ZooError(
                f"Zoo {method} {path} returned {resp.status_code}: {resp.text[:300]}"
            )

        try:
            return resp.json()
        except ValueError as exc:
            raise ZooError(f"Zoo {method} {path} returned non-JSON body") from exc

    async def predict_on_text(self, texts: list[str]) -> Any:
        """POST /predict_on_text — mapped, post-processed class names."""
        return await self._request(
            "POST", "/predict_on_text", json={"text_list": texts}
        )

    async def predict_raw(self, texts: list[str]) -> Any:
        """POST /predict — raw class strings, no post-processing."""
        return await self._request("POST", "/predict", json={"text_list": texts})

    async def list_services(self) -> Any:
        """GET /show_services — connected Triton model services."""
        return await self._request("GET", "/show_services")
