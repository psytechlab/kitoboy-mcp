"""Entry point: register tools and serve the MCP over Streamable HTTP.

When MCP_AUTH_TOKEN is set, the endpoint is guarded by a static bearer token via
a Starlette middleware; otherwise it is served unauthenticated (intended for the
in-network / local-test deployment).
"""

from __future__ import annotations

import logging

from . import tools  # noqa: F401  -- import registers the tools on `mcp`
from .deps import mcp, settings


def main() -> None:
    logging.basicConfig(level=logging.INFO)

    if settings.mcp_auth_token:
        import uvicorn

        from .middleware import BearerAuthMiddleware

        app = mcp.streamable_http_app()
        app.add_middleware(BearerAuthMiddleware, token=settings.mcp_auth_token)
        uvicorn.run(app, host=settings.mcp_host, port=settings.mcp_port)
    else:
        mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
