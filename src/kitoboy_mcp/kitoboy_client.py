"""Async HTTP client for the Kitoboy `api` service.

Handles JWT lifecycle: logs in with volunteer credentials, caches the token,
and transparently re-logs-in once on a 401 (the platform JWT lives 12h). All
calls are READ-only. Upstream failures are surfaced as KitoboyError, never
swallowed.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from .errors import KitoboyError

logger = logging.getLogger(__name__)


class KitoboyClient:
    """Thin async wrapper over the Kitoboy api READ endpoints."""

    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        *,
        timeout: float = 30.0,
        max_retries: int = 30,
        retry_delay: float = 2.0,
    ) -> None:
        self._client = httpx.AsyncClient(base_url=base_url.rstrip("/"), timeout=timeout)
        self._username = username
        self._password = password
        self._max_retries = max_retries
        self._retry_delay = retry_delay
        self._token: str | None = None
        self._login_lock = asyncio.Lock()

    async def aclose(self) -> None:
        await self._client.aclose()

    # --- auth ---

    def _auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._token}"} if self._token else {}

    async def login(self) -> None:
        """Obtain and cache a fresh JWT via POST /login."""
        async with self._login_lock:
            try:
                resp = await self._client.post(
                    "/login",
                    json={"username": self._username, "password": self._password},
                )
            except httpx.RequestError as exc:
                raise KitoboyError(f"Login request failed: {exc}") from exc

            if resp.status_code != 200:
                raise KitoboyError(f"Login failed with status {resp.status_code}")

            try:
                token = resp.json().get("token")
            except ValueError as exc:
                raise KitoboyError("Login response was not valid JSON") from exc

            if not token:
                raise KitoboyError("Login response did not contain a token")

            self._token = token

    async def wait_for_login(self) -> None:
        """Retry login with backoff at startup (api may still be booting)."""
        last: Exception | None = None
        for attempt in range(1, self._max_retries + 1):
            try:
                await self.login()
                logger.info("Authenticated against Kitoboy API")
                return
            except KitoboyError as exc:
                last = exc
                logger.warning(
                    "Kitoboy login attempt %d/%d failed: %s",
                    attempt,
                    self._max_retries,
                    exc,
                )
                await asyncio.sleep(self._retry_delay)
        raise KitoboyError(
            f"Could not authenticate against Kitoboy after {self._max_retries} attempts"
        ) from last

    # --- core request ---

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> Any:
        if self._token is None:
            await self.login()

        try:
            resp = await self._client.request(
                method, path, params=params, json=json, headers=self._auth_headers()
            )
            if resp.status_code == 401:
                # Token likely expired — re-login once and retry.
                await self.login()
                resp = await self._client.request(
                    method, path, params=params, json=json, headers=self._auth_headers()
                )
        except httpx.RequestError as exc:
            raise KitoboyError(f"Kitoboy {method} {path} failed: {exc}") from exc

        if resp.status_code >= 400:
            raise KitoboyError(
                f"Kitoboy {method} {path} returned {resp.status_code}: {resp.text[:300]}"
            )

        try:
            return resp.json()
        except ValueError as exc:
            raise KitoboyError(
                f"Kitoboy {method} {path} returned non-JSON body"
            ) from exc

    # --- READ endpoints ---

    async def search_person(self, query: str) -> Any:
        return await self._request(
            "GET", "/search-person", params={"searchString": query}
        )

    async def get_avatar(self, avatar_id: str) -> Any:
        return await self._request("GET", f"/get-avatar/{avatar_id}")

    async def get_person_with_avatars(self, person_id: str) -> Any:
        return await self._request("GET", f"/get-person-with-avatars/{person_id}")

    async def list_avatars(self, page: int, size: int) -> Any:
        return await self._request(
            "POST", "/get-avatars", json={"page": page, "size": size}
        )

    async def list_attributes(self) -> Any:
        return await self._request("GET", "/get-attributes")

    async def list_statuses(self) -> Any:
        return await self._request("GET", "/get-statuses")
