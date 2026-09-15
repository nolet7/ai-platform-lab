from typing import Any

from pydantic import BaseModel, Field


class TokenIdentity(BaseModel):
    subject: str | None = None
    username: str | None = None
    client_id: str | None = None
    audience: str | list[str] | None = None
    roles: list[str] = Field(default_factory=list)


class InferenceRequest(BaseModel):
    model_name: str
    input_data: dict[str, Any]


class InferenceResponse(BaseModel):
    status: str
    model_name: str
    requested_by: str | None
    result: dict[str, Any]
