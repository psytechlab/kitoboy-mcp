"""Exceptions raised by the upstream service clients."""

from __future__ import annotations


class UpstreamError(RuntimeError):
    """Base class for failures talking to an upstream Kitoboy service."""


class KitoboyError(UpstreamError):
    """The Kitoboy API call failed (transport error or non-2xx response)."""


class ZooError(UpstreamError):
    """The Zoo inference service call failed (transport error or non-2xx response)."""
