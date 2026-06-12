"""Registry client helpers.

Provides `discover(task)` to look up an agent endpoint from the registry,
and `register(agent_info)` for agents to self-register on startup.
"""

import os
import asyncio
import logging

import httpx

from common.security import auth_headers

REGISTRY_URL = os.getenv("REGISTRY_URL", "http://localhost:10000")
REGISTRY_RETRY_ATTEMPTS = int(os.getenv("REGISTRY_RETRY_ATTEMPTS", "3"))
REGISTRY_RETRY_BASE_DELAY = float(os.getenv("REGISTRY_RETRY_BASE_DELAY", "0.5"))

logger = logging.getLogger(__name__)


async def discover(task: str) -> str:
    """Return the endpoint URL of the agent that handles the given task.

    Args:
        task: The task identifier (e.g. "legal_question", "tax_question").

    Returns:
        The HTTP endpoint base URL of the matching agent.

    Raises:
        httpx.HTTPStatusError: If no agent is found or the registry is unreachable.
    """
    async with httpx.AsyncClient(timeout=10.0, headers=auth_headers()) as client:
        resp = await _request_with_retry(client, "GET", f"{REGISTRY_URL}/discover/{task}")
        return resp.json()["endpoint"]


async def register(agent_info: dict) -> None:
    """Register an agent with the registry.

    Args:
        agent_info: Dict with keys: agent_name, version, description,
                    tasks, endpoint, tags.

    Raises:
        httpx.HTTPStatusError: If registration fails.
    """
    async with httpx.AsyncClient(timeout=10.0, headers=auth_headers()) as client:
        await _request_with_retry(client, "POST", f"{REGISTRY_URL}/register", json=agent_info)


async def _request_with_retry(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    **kwargs,
) -> httpx.Response:
    """Run a registry request with small exponential-backoff retries."""
    last_exc: Exception | None = None
    for attempt in range(1, REGISTRY_RETRY_ATTEMPTS + 1):
        try:
            resp = await client.request(method, url, **kwargs)
            resp.raise_for_status()
            return resp
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code < 500:
                raise
            last_exc = exc
        except (httpx.ConnectError, httpx.ReadTimeout, httpx.ConnectTimeout) as exc:
            last_exc = exc

        if attempt < REGISTRY_RETRY_ATTEMPTS:
            delay = REGISTRY_RETRY_BASE_DELAY * (2 ** (attempt - 1))
            logger.warning("Registry %s %s failed on attempt %d: %s", method, url, attempt, last_exc)
            await asyncio.sleep(delay)

    assert last_exc is not None
    raise last_exc
