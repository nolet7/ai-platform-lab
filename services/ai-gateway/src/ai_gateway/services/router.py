from dataclasses import dataclass

from ai_gateway.models import AIRequest


@dataclass(frozen=True)
class RouteCandidate:
    provider: str
    model: str


DEFAULT_MODELS = {
    "mock-primary": "mock-primary-v1",
    "mock-secondary": "mock-secondary-v1",
}


def route_request(
    request: AIRequest,
) -> tuple[RouteCandidate, ...]:

    if request.provider and request.provider != "auto":
        model = (
            request.model
            or DEFAULT_MODELS.get(
                request.provider,
                "mock-primary-v1",
            )
        )

        return (
            RouteCandidate(
                provider=request.provider,
                model=model,
            ),
        )

    return (
        RouteCandidate(
            provider="mock-primary",
            model="mock-primary-v1",
        ),
        RouteCandidate(
            provider="mock-secondary",
            model="mock-secondary-v1",
        ),
    )
