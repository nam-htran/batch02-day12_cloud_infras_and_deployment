"""Lightweight request metrics for FastAPI services."""

from __future__ import annotations

import time
from collections import defaultdict
from collections.abc import Callable

from fastapi import FastAPI, Request
from starlette.responses import PlainTextResponse


def add_monitoring(app: FastAPI, service_name: str) -> None:
    """Add request counters, latency tracking, and a Prometheus-style /metrics endpoint."""
    counters: dict[tuple[str, str, str], int] = defaultdict(int)
    latency_sum: dict[tuple[str, str], float] = defaultdict(float)

    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next: Callable):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - start
        route = request.url.path
        method = request.method
        status = str(response.status_code)
        counters[(method, route, status)] += 1
        latency_sum[(method, route)] += elapsed
        return response

    @app.get("/metrics")
    async def metrics() -> PlainTextResponse:
        lines = [
            f'# HELP a2a_requests_total Total requests handled by {service_name}.',
            '# TYPE a2a_requests_total counter',
        ]
        for (method, route, status), count in sorted(counters.items()):
            lines.append(
                f'a2a_requests_total{{service="{service_name}",method="{method}",'
                f'route="{route}",status="{status}"}} {count}'
            )

        lines.extend(
            [
                f'# HELP a2a_request_latency_seconds_sum Total request latency for {service_name}.',
                '# TYPE a2a_request_latency_seconds_sum counter',
            ]
        )
        for (method, route), total in sorted(latency_sum.items()):
            lines.append(
                f'a2a_request_latency_seconds_sum{{service="{service_name}",method="{method}",'
                f'route="{route}"}} {total:.6f}'
            )
        return PlainTextResponse("\n".join(lines) + "\n")
