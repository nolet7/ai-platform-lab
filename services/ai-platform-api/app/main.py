from fastapi import FastAPI

from app.config import settings
from app.routers import (
    health,
    identity,
    inference,
)


app = FastAPI(
    title=settings.app_name,
    version="2L",
    description=(
        "Secure API layer for the Self-Service "
        "AI/ML Deployment Control Plane."
    ),
)


app.include_router(health.router)
app.include_router(identity.router)
app.include_router(inference.router)


@app.get("/")
async def root():
    return {
        "service": settings.app_name,
        "phase": "2L",
        "authentication": "Keycloak OIDC",
        "authorization": "RBAC",
        "status": "running",
    }
