"""Optional API-key authentication helpers for local A2A services."""

from __future__ import annotations

import os
from collections.abc import Callable

from fastapi import FastAPI, Request
from starlette.responses import JSONResponse

AUTH_HEADER = "X-Agent-API-Key"


def get_agent_api_key() -> str:
    """Return the configured shared API key, or an empty string if auth is off."""
    return os.getenv("AGENT_API_KEY", "").strip()


def auth_headers() -> dict[str, str]:
    """Headers clients should send when optional agent auth is enabled."""
    key = get_agent_api_key()
    return {AUTH_HEADER: key} if key else {}


def add_api_key_middleware(
    app: FastAPI,
    *,
    exempt_paths: set[str] | None = None,
) -> None:
    """Require X-Agent-API-Key for requests when AGENT_API_KEY is configured."""
    exempt = exempt_paths or {"/health", "/metrics"}

    @app.middleware("http")
    async def api_key_auth(request: Request, call_next: Callable):
        key = get_agent_api_key()
        if not key or request.url.path in exempt:
            return await call_next(request)
        if request.headers.get(AUTH_HEADER) != key:
            return JSONResponse({"detail": "Invalid or missing API key"}, status_code=401)
        return await call_next(request)
