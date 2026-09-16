import logging

from fastapi import FastAPI

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
    OTLPSpanExporter,
)
from opentelemetry.instrumentation.fastapi import (
    FastAPIInstrumentor,
)
from opentelemetry.instrumentation.httpx import (
    HTTPXClientInstrumentor,
)
from opentelemetry.instrumentation.urllib import (
    URLLibInstrumentor,
)
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
)
from opentelemetry.sdk.trace.sampling import (
    ParentBased,
    TraceIdRatioBased,
)

from app.config import settings


logger = logging.getLogger("ai-platform-api.tracing")


def configure_tracing(app: FastAPI) -> None:
    if not settings.otel_enabled:
        logger.info(
            "tracing_disabled",
            extra={"event": "tracing_disabled"},
        )
        return

    resource = Resource.create(
        {
            "service.name": settings.otel_service_name,
            "service.version": "phase-2p-v1",
            "deployment.environment": settings.app_env,
            "k8s.cluster.name": "ai-platform",
        }
    )

    provider = TracerProvider(
        resource=resource,
        sampler=ParentBased(
            TraceIdRatioBased(
                settings.otel_trace_sample_ratio
            )
        ),
    )

    exporter = OTLPSpanExporter(
        endpoint=settings.otel_exporter_otlp_endpoint,
        insecure=settings.otel_exporter_otlp_insecure,
    )

    provider.add_span_processor(
        BatchSpanProcessor(exporter)
    )

    trace.set_tracer_provider(provider)

    FastAPIInstrumentor.instrument_app(
        app,
        excluded_urls=(
            "/health/live,/health/ready"
        ),
    )

    HTTPXClientInstrumentor().instrument()
    URLLibInstrumentor().instrument()

    logger.info(
        "tracing_enabled",
        extra={
            "event": "tracing_enabled",
            "otel_endpoint":
                settings.otel_exporter_otlp_endpoint,
        },
    )
