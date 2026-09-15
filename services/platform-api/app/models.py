from typing import Literal

from pydantic import BaseModel, Field


class DeploymentRequest(BaseModel):
    tenant_id: str = Field(
        min_length=1,
        description="Tenant that owns the requested deployment",
    )

    model_name: str = Field(
        min_length=1,
        description="Logical model name",
    )

    model_version: str = Field(
        min_length=1,
        description="Model version or release identifier",
    )

    environment: Literal[
        "dev",
        "staging",
        "prod",
    ]


class DeploymentAccepted(BaseModel):
    request_id: str
    status: str
    tenant_id: str
    model_name: str
    model_version: str
    environment: str
    requested_by: str


class ApprovalDecision(BaseModel):
    decision: Literal[
        "approved",
        "rejected",
    ]

    reason: str = Field(
        min_length=3,
        max_length=1000,
    )


class DeploymentStatus(BaseModel):
    request_id: str
    status: str
    tenant_id: str
    model_name: str
    model_version: str
    environment: str
    requested_by: str
    decision_by: str | None = None
    decision_reason: str | None = None
