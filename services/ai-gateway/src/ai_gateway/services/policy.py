from dataclasses import dataclass

import httpx

from ai_gateway.config import settings


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str


async def opa_health() -> bool:
    if not settings.opa_enabled:
        return False

    try:
        async with httpx.AsyncClient(
            timeout=settings.opa_timeout_seconds
        ) as client:
            response = await client.get(
                f"{settings.opa_url.rstrip('/')}/health"
            )
            response.raise_for_status()
            return True

    except httpx.HTTPError:
        return False


async def evaluate_policy(
    *,
    tenant_id: str,
    use_case: str,
    data_classification: str,
    provider: str,
    model: str,
) -> PolicyDecision:

    if not settings.opa_enabled:
        return PolicyDecision(
            allowed=True,
            reason="OPA policy enforcement disabled",
        )

    payload = {
        "input": {
            "tenant_id": tenant_id,
            "use_case": use_case,
            "data_classification": data_classification,
            "provider": provider,
            "model": model,
        }
    }

    try:
        async with httpx.AsyncClient(
            timeout=settings.opa_timeout_seconds
        ) as client:

            response = await client.post(
                (
                    f"{settings.opa_url.rstrip('/')}"
                    "/v1/data/ai/gateway/decision"
                ),
                json=payload,
            )

            response.raise_for_status()
            body = response.json()

    except (httpx.HTTPError, ValueError):
        return PolicyDecision(
            allowed=False,
            reason="OPA unavailable or returned an invalid response",
        )

    result = body.get("result")

    if not isinstance(result, dict):
        return PolicyDecision(
            allowed=False,
            reason="OPA returned no valid policy decision",
        )

    return PolicyDecision(
        allowed=bool(result.get("allow", False)),
        reason=str(
            result.get(
                "reason",
                "No policy reason returned",
            )
        ),
    )
