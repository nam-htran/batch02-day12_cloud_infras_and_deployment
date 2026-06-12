"""Small MCP-style stdio client used by worker agents."""

from __future__ import annotations

import asyncio
import json
import sys
from typing import Any
from uuid import uuid4


class MCPToolError(RuntimeError):
    """Raised when the external MCP tool server returns an error."""


async def call_tax_code_mcp(query: str, timeout: float = 10.0) -> str:
    """Call the external tax-law MCP tool server and return text content."""
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "mcp_tools.tax_law_server",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    try:
        await _rpc(process, "initialize", {}, timeout)
        result = await _rpc(
            process,
            "tools/call",
            {
                "name": "search_tax_code",
                "arguments": {"query": query},
            },
            timeout,
        )
        content = result.get("content", [])
        return "\n".join(part.get("text", "") for part in content if part.get("type") == "text")
    finally:
        process.terminate()
        try:
            await asyncio.wait_for(process.wait(), timeout=2.0)
        except asyncio.TimeoutError:
            process.kill()


async def _rpc(
    process: asyncio.subprocess.Process,
    method: str,
    params: dict[str, Any],
    timeout: float,
) -> dict[str, Any]:
    """Send one line-delimited JSON-RPC request and read one response."""
    if process.stdin is None or process.stdout is None:
        raise MCPToolError("MCP process is missing stdio pipes")

    request = {
        "jsonrpc": "2.0",
        "id": str(uuid4()),
        "method": method,
        "params": params,
    }
    process.stdin.write((json.dumps(request) + "\n").encode("utf-8"))
    await process.stdin.drain()

    raw = await asyncio.wait_for(process.stdout.readline(), timeout=timeout)
    if not raw:
        raise MCPToolError("MCP server closed stdout without a response")

    response = json.loads(raw.decode("utf-8"))
    if "error" in response:
        raise MCPToolError(response["error"].get("message", "Unknown MCP error"))
    return response.get("result", {})
