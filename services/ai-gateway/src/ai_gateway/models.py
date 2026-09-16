from typing import Literal

from pydantic import BaseModel, Field


class AIRequest(BaseModel):
    use_case: str = Field(min_length=1, max_length=100)
    prompt: str = Field(min_length=1, max_length=12000)

    provider: str | None = None
    model: str | None = None

    data_classification: Literal[
        "public",
        "internal",
        "confidential",
        "restricted",
    ] = "internal"

    max_output_tokens: int = Field(default=256, ge=1, le=2048)


class AIResponse(BaseModel):
    request_id: str
    provider: str
    model: str
    output: str
    input_tokens: int
    output_tokens: int
