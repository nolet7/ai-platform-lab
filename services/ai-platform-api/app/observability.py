import logging
import time
import uuid

from fastapi import Request
from prometheus_client import Counter, Histogram


logger = logging.getLogger("ai-platform-api")


HTTP_REQUESTS = Counter(
    "ai_platform_http_requests_total",
    "Total HTTP requests handled by the AI Platform API",
    [
        "method",
        "route",
        "status_code",
    ],
)


HTTP_REQUEST_DURATION = Histogram(
    "ai_platform_http_request_duration_seconds",
    "AI Platform API request duration in seconds",
    [
        "method",
        "route",
    ],
    buckets=(
        0.005,
        0.01,
        0.025,
        0.05,
        0.1,
        0.25,
        0.5,
        1.0,
        2.5,
        5.0,
    ),
)


AUTH_FAILURES = Counter(
    "ai_platform_auth_failures_total",
    "Authentication failures",
    [
        "reason",
    ],
)


RBAC_DENIALS = Counter(
    "ai_platform_rbac_denials_total",
    "RBAC authorization denials",
    [
        "route",
    ],
)


AUTHENTICATED_REQUESTS = Counter(
    "ai_platform_authenticated_requests_total",
    "Successfully authenticated requests",
    [
        "client_id",
    ],
)


async def request_observability_middleware(
    request: Request,
    call_next,
):
    request_id = request.headers.get(
        "X-Request-ID",
        str(uuid.uuid4()),
    )

    request.state.request_id = request_id

    started = time.perf_counter()
    status_code = 500

    try:
        response = await call_next(request)

        status_code = response.status_code

        response.headers["X-Request-ID"] = request_id

        return response

    finally:
        duration = time.perf_counter() - started

        route_object = request.scope.get("route")

        route = getattr(
            route_object,
            "path",
            request.url.path,
        )

        if request.url.path != "/metrics":
            HTTP_REQUESTS.labels(
                method=request.method,
                route=route,
                status_code=str(status_code),
            ).inc()

            HTTP_REQUEST_DURATION.labels(
                method=request.method,
                route=route,
            ).observe(duration)

        logger.info(
            "http_request",
            extra={
                "event": "http_request",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "route": route,
                "status_code": status_code,
                "duration_ms": round(
                    duration * 1000,
                    2,
                ),
            },
        )
