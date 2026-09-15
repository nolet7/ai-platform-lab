import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_client import (
    start_http_server,
)

from app.config import settings
from app.logging_config import (
    configure_logging,
)
from app.observability import (
    request_observability_middleware,
)
from app.routers import (
    admin,
    health,
    identity,
    inference,
)


configure_logging()

logger = logging.getLogger(
    "ai-platform-api"
)


@asynccontextmanager
async def lifespan(
    app: FastAPI,
):
    metrics_server = None
    metrics_thread = None

    if settings.metrics_enabled:
        (
            metrics_server,
            metrics_thread,
        ) = start_http_server(
            port=settings.metrics_port,
            addr="0.0.0.0",
        )

        logger.info(
            "metrics_server_started",
            extra={
                "event":
                    "metrics_server_started",
            },
        )

    logger.info(
        "application_started",
        extra={
            "event":
                "application_started",
        },
    )

    yield

    if metrics_server:
        metrics_server.shutdown()
        metrics_server.server_close()

    if metrics_thread:
        metrics_thread.join(
            timeout=5
        )

    logger.info(
        "application_stopped",
        extra={
            "event":
                "application_stopped",
        },
    )


app = FastAPI(
    title=settings.app_name,
    version="2O",
    description=(
        "Observable secure API layer "
        "for the Self-Service AI/ML "
        "Deployment Control Plane."
    ),
    lifespan=lifespan,
)


app.middleware("http")(
    request_observability_middleware
)


app.include_router(
    health.router
)

app.include_router(
    identity.router
)

app.include_router(
    inference.router
)

app.include_router(
    admin.router
)


@app.get("/")
async def root():
    return {
        "service":
            settings.app_name,
        "phase": "2O",
        "authentication":
            "Keycloak OIDC",
        "authorization":
            "RBAC",
        "observability":
            "Prometheus + Grafana",
        "status":
            "running",
    }
