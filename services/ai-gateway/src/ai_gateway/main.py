from contextlib import asynccontextmanager

from fastapi import (
    FastAPI,
    Header,
    HTTPException,
    Response,
)

from ai_gateway.config import settings
from ai_gateway.models import AIRequest, AIResponse
from ai_gateway.services.guardrails import scan_prompt
from ai_gateway.services.orchestrator import (
    AIOrchestrator,
    ProviderUnavailableError,
)
from ai_gateway.services.output_guardrail import protect_output
from ai_gateway.services.pii import redact_pii
from ai_gateway.services.policy import (
    evaluate_policy,
    opa_health,
)
from ai_gateway.services.rate_limit import check_rate_limit
from ai_gateway.services.redis_store import (
    close_redis,
    get_redis,
    redis_health,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.redis_enabled:
        redis = await get_redis()
        await redis.ping()

    yield

    await close_redis()


app = FastAPI(
    title=settings.app_name,
    version="0.5.0",
    description="Governed enterprise AI gateway",
    lifespan=lifespan,
)

orchestrator = AIOrchestrator()


@app.get("/health/live")
async def health_live():
    return {
        "status": "alive",
        "service": "ai-gateway",
    }


@app.get("/health/ready")
async def health_ready():
    redis_ok = await redis_health()
    opa_ok = await opa_health()

    redis_ready = (
        redis_ok if settings.redis_enabled else True
    )

    opa_ready = (
        opa_ok if settings.opa_enabled else True
    )

    if not (redis_ready and opa_ready):
        raise HTTPException(
            status_code=503,
            detail={
                "redis_ready": redis_ready,
                "opa_ready": opa_ready,
            },
        )

    return {
        "status": "ready",
        "environment": settings.app_env,
        "redis_connected": redis_ok,
        "opa_connected": opa_ok,
        "guardrails_enabled": True,
        "pii_redaction_enabled": True,
        "model_routing_enabled": True,
        "circuit_breaker_enabled": True,
    }


@app.get("/v1/models")
async def models():
    return {
        "models": [
            {
                "provider": "mock-primary",
                "model": "mock-primary-v1",
                "priority": 1,
            },
            {
                "provider": "mock-secondary",
                "model": "mock-secondary-v1",
                "priority": 2,
            },
        ]
    }


@app.post(
    "/v1/responses",
    response_model=AIResponse,
)
async def create_response(
    request: AIRequest,
    response: Response,
    x_tenant_id: str = Header(
        ...,
        alias="X-Tenant-ID",
        min_length=2,
        max_length=100,
    ),
):
    rate_decision = await check_rate_limit(
        tenant_id=x_tenant_id
    )

    if not rate_decision.allowed:
        raise HTTPException(
            status_code=429,
            detail="Tenant rate limit exceeded",
        )

    requested_provider = (
        request.provider or "auto"
    )

    requested_model = (
        request.model or "auto"
    )

    policy_decision = await evaluate_policy(
        tenant_id=x_tenant_id,
        use_case=request.use_case,
        data_classification=request.data_classification,
        provider=requested_provider,
        model=requested_model,
    )

    if not policy_decision.allowed:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "policy_denied",
                "reason": policy_decision.reason,
            },
            headers={
                "X-Policy-Decision": "DENY",
            },
        )

    prompt_guardrail = scan_prompt(
        request.prompt
    )

    if not prompt_guardrail.allowed:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "prompt_guardrail_blocked",
                "reason": prompt_guardrail.reason,
                "detections": list(
                    prompt_guardrail.detections
                ),
            },
            headers={
                "X-Policy-Decision": "ALLOW",
                "X-Prompt-Guardrail": "BLOCK",
            },
        )

    pii_result = redact_pii(
        request.prompt
    )

    sanitized_request = request.model_copy(
        update={
            "prompt": pii_result.text,
        }
    )

    try:
        generation = await orchestrator.generate(
            request=sanitized_request,
            tenant_id=x_tenant_id,
        )

    except ProviderUnavailableError as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "model_provider_unavailable",
                "reason": str(exc),
            },
        ) from exc

    ai_response = generation.response

    output_result = protect_output(
        ai_response.output
    )

    if output_result.modified:
        ai_response = ai_response.model_copy(
            update={
                "output": output_result.text,
            }
        )

    response.headers[
        "X-Tenant-ID"
    ] = x_tenant_id

    response.headers[
        "X-RateLimit-Limit"
    ] = str(rate_decision.limit)

    response.headers[
        "X-RateLimit-Remaining"
    ] = str(rate_decision.remaining)

    response.headers[
        "X-Policy-Decision"
    ] = "ALLOW"

    response.headers[
        "X-Prompt-Guardrail"
    ] = "ALLOW"

    response.headers[
        "X-PII-Detected"
    ] = str(
        pii_result.detected
    ).lower()

    response.headers[
        "X-PII-Redacted-Count"
    ] = str(pii_result.count)

    response.headers[
        "X-Output-Guardrail"
    ] = (
        "REDACTED"
        if output_result.modified
        else "PASS"
    )

    response.headers[
        "X-Cache"
    ] = generation.cache_status

    response.headers[
        "X-Model-Provider"
    ] = generation.selected_provider

    response.headers[
        "X-Model-Attempted"
    ] = (
        ",".join(
            generation.attempted_providers
        )
        or "cache"
    )

    response.headers[
        "X-Fallback-Used"
    ] = str(
        generation.fallback_used
    ).lower()

    response.headers[
        "X-Circuit-Skipped"
    ] = (
        ",".join(
            generation.skipped_open_circuits
        )
        or "none"
    )

    return ai_response
