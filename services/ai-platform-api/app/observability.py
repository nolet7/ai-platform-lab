import logging
import time
import uuid

from fastapi import Request
from opentelemetry import trace
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
    ["reason"],
)


RBAC_DENIALS = Counter(
    "ai_platform_rbac_denials_total",
    "RBAC authorization denials",
    ["route"],
)


AUTHENTICATED_REQUESTS = Counter(
    "ai_platform_authenticated_requests_total",
    "Successfully authenticated requests",
    ["client_id"],
)


def current_trace_context():
    span = trace.get_current_span()
    context = span.get_span_context()

    if not context.is_valid:
        return None, None

    trace_id = format(
        context.trace_id,
        "032x",
    )

    span_id = format(
        context.span_id,
        "016x",
    )

    return trace_id, span_id


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
    trace_id = None
    span_id = None

    try:
        response = await call_next(request)

        status_code = response.status_code

        response.headers[
            "X-Request-ID"
        ] = request_id

        trace_id, span_id = (
            current_trace_context()
        )

        if trace_id:
            response.headers[
                "X-Trace-ID"
            ] = trace_id

        return response

    finally:
        duration = (
            time.perf_counter()
            - started
        )

        # If the trace context was not captured
        # during normal response processing,
        # try one final time before logging.
        if trace_id is None:
            trace_id, span_id = (
                current_trace_context()
            )

        route_object = (
            request.scope.get("route")
        )

        route = getattr(
            route_object,
            "path",
            request.url.path,
        )

        HTTP_REQUESTS.labels(
            method=request.method,
            route=route,
            status_code=str(
                status_code
            ),
        ).inc()

        HTTP_REQUEST_DURATION.labels(
            method=request.method,
            route=route,
        ).observe(duration)

        log_fields = {
            "event":
                "http_request",
            "request_id":
                request_id,
            "method":
                request.method,
            "path":
                request.url.path,
            "route":
                route,
            "status_code":
                status_code,
            "duration_ms":
                round(
                    duration * 1000,
                    2,
                ),
        }

        if trace_id:
            log_fields[
                "trace_id"
            ] = trace_id

        if span_id:
            log_fields[
                "span_id"
            ] = span_id

        logger.info(
            "http_request",
            extra=log_fields,
        )
