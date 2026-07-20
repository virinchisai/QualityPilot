"""Correlation IDs, structured logging, and request metrics."""

import json
import logging
import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from qualitypilot.observability.metrics import HTTP_LATENCY, HTTP_REQUESTS

logger = logging.getLogger("qualitypilot.http")


class ObservabilityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, app_name: str) -> None:
        super().__init__(app)
        self.app_name = app_name

    async def dispatch(self, request: Request, call_next):
        correlation_id = request.headers.get("x-correlation-id", str(uuid.uuid4()))[:128]
        started = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - started
        route = request.scope.get("route")
        path = getattr(route, "path", request.url.path)
        response.headers["X-Correlation-ID"] = correlation_id
        HTTP_REQUESTS.labels(self.app_name, request.method, path, response.status_code).inc()
        HTTP_LATENCY.labels(self.app_name, request.method, path).observe(duration)
        logger.info(
            json.dumps(
                {
                    "event": "http_request",
                    "app": self.app_name,
                    "correlation_id": correlation_id,
                    "method": request.method,
                    "path": path,
                    "status": response.status_code,
                    "duration_ms": round(duration * 1000, 2),
                }
            )
        )
        return response
