import json
import logging
import sys
from datetime import datetime, timezone

from opentelemetry import trace


EXTRA_FIELDS = (
    "event",
    "request_id",
    "method",
    "path",
    "route",
    "status_code",
    "duration_ms",
    "reason",
    "client_id",
    "username",
    "required_roles",
    "assigned_roles",
    "otel_endpoint",
    "trace_id",
    "span_id",
)


class JsonFormatter(logging.Formatter):

    def format(
        self,
        record: logging.LogRecord,
    ) -> str:

        payload = {
            "timestamp":
                datetime.now(
                    timezone.utc
                ).isoformat(),
            "level":
                record.levelname,
            "logger":
                record.name,
            "message":
                record.getMessage(),
        }

        # First attempt to obtain trace context
        # directly from OpenTelemetry.
        span = trace.get_current_span()
        context = span.get_span_context()

        if context.is_valid:
            payload["trace_id"] = format(
                context.trace_id,
                "032x",
            )

            payload["span_id"] = format(
                context.span_id,
                "016x",
            )

        # Explicit fields supplied by application
        # logging take precedence.
        for field in EXTRA_FIELDS:
            if hasattr(record, field):
                payload[field] = getattr(
                    record,
                    field,
                )

        if record.exc_info:
            payload["exception"] = (
                self.formatException(
                    record.exc_info
                )
            )

        return json.dumps(
            payload,
            separators=(",", ":"),
            default=str,
        )


def configure_logging() -> None:
    handler = logging.StreamHandler(
        sys.stdout
    )

    handler.setFormatter(
        JsonFormatter()
    )

    root_logger = logging.getLogger()

    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)

    logging.getLogger(
        "uvicorn.access"
    ).disabled = True
