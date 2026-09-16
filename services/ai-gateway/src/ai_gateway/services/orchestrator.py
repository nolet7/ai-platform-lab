from dataclasses import dataclass
from uuid import uuid4

from ai_gateway.models import AIRequest, AIResponse
from ai_gateway.providers.base import ProviderError
from ai_gateway.services.cache import (
    cache_response,
    get_cached_response,
    is_cacheable,
)
from ai_gateway.services.circuit_breaker import (
    get_circuit_state,
    record_failure,
    record_success,
)
from ai_gateway.services.policy import evaluate_policy
from ai_gateway.services.provider_registry import get_provider
from ai_gateway.services.router import route_request


class ProviderUnavailableError(RuntimeError):
    """Raised when no authorized healthy provider is available."""


@dataclass(frozen=True)
class GenerationResult:
    response: AIResponse
    cache_status: str
    selected_provider: str
    attempted_providers: tuple[str, ...]
    skipped_open_circuits: tuple[str, ...]
    fallback_used: bool


class AIOrchestrator:

    async def generate(
        self,
        request: AIRequest,
        tenant_id: str,
    ) -> GenerationResult:

        cached = await get_cached_response(request)

        if cached is not None:
            return GenerationResult(
                response=cached,
                cache_status="HIT",
                selected_provider=cached.provider,
                attempted_providers=(),
                skipped_open_circuits=(),
                fallback_used=False,
            )

        candidates = route_request(request)

        attempted: list[str] = []
        skipped: list[str] = []
        errors: list[str] = []

        for index, candidate in enumerate(candidates):

            policy = await evaluate_policy(
                tenant_id=tenant_id,
                use_case=request.use_case,
                data_classification=request.data_classification,
                provider=candidate.provider,
                model=candidate.model,
            )

            if not policy.allowed:
                errors.append(
                    f"{candidate.provider}: policy denied"
                )
                continue

            circuit = await get_circuit_state(
                candidate.provider
            )

            if circuit.open:
                skipped.append(candidate.provider)
                continue

            provider = get_provider(
                candidate.provider
            )

            if provider is None:
                errors.append(
                    f"{candidate.provider}: provider not registered"
                )
                continue

            attempted.append(
                candidate.provider
            )

            try:
                result = await provider.generate(
                    request=request,
                    model=candidate.model,
                    max_output_tokens=(
                        request.max_output_tokens
                    ),
                )

            except ProviderError as exc:
                await record_failure(
                    candidate.provider
                )

                errors.append(
                    f"{candidate.provider}: {exc}"
                )
                continue

            await record_success(
                candidate.provider
            )

            response = AIResponse(
                request_id=str(uuid4()),
                provider=result.provider,
                model=result.model,
                output=result.output,
                input_tokens=result.input_tokens,
                output_tokens=result.output_tokens,
            )

            await cache_response(
                request=request,
                response=response,
            )

            cache_status = (
                "MISS"
                if is_cacheable(request)
                else "BYPASS"
            )

            return GenerationResult(
                response=response,
                cache_status=cache_status,
                selected_provider=result.provider,
                attempted_providers=tuple(attempted),
                skipped_open_circuits=tuple(skipped),
                fallback_used=(
                    index > 0
                    or bool(skipped)
                ),
            )

        detail = "; ".join(errors)

        if skipped:
            detail = (
                f"{detail}; open circuits: "
                f"{','.join(skipped)}"
            ).strip("; ")

        raise ProviderUnavailableError(
            detail or "No provider available"
        )
