from typing import Literal

from pydantic import BaseModel, Field


class DeploymentRequest(BaseModel):
    tenant_id: str = Field(
        min_length=1,
        pattern=r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$",
    )

    model_name: Literal["tax-document-classifier"]

    model_version: str = Field(
        pattern=r"^[1-9][0-9]*$",
    )

    environment: Literal[
        "dev",
        "staging",
    ]


class DeploymentAccepted(BaseModel):
    request_id: str
    status: str
    execution_status: str
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
    execution_status: str
    execution_message: str | None = None
    tenant_id: str
    model_name: str
    model_version: str
    environment: str
    requested_by: str
    decision_by: str | None = None
    decision_reason: str | None = None
    orchestration: dict | None = None


class AuditEventView(BaseModel):
    event_type: str
    actor: str
    tenant_id: str
    event_data: dict
    created_at: str
