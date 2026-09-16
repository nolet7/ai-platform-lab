import hashlib
import json

from ai_gateway.config import settings
from ai_gateway.models import AIRequest, AIResponse
from ai_gateway.services.redis_store import get_redis

CACHEABLE_CLASSIFICATIONS = {
    "public",
    "internal",
}


def is_cacheable(request: AIRequest) -> bool:
    return (
        settings.redis_enabled
        and request.data_classification in CACHEABLE_CLASSIFICATIONS
    )


def build_cache_key(request: AIRequest) -> str:
    payload = {
        "use_case": request.use_case,
        "prompt": request.prompt,
        "provider": request.provider,
        "model": request.model,
        "data_classification": request.data_classification,
        "max_output_tokens": request.max_output_tokens,
    }

    serialized = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    )

    digest = hashlib.sha256(
        serialized.encode("utf-8")
    ).hexdigest()

    return f"ai-gateway:cache:{digest}"


async def get_cached_response(
    request: AIRequest,
) -> AIResponse | None:

    if not is_cacheable(request):
        return None

    redis = await get_redis()

    cached = await redis.get(
        build_cache_key(request)
    )

    if cached is None:
        return None

    return AIResponse.model_validate_json(cached)


async def cache_response(
    request: AIRequest,
    response: AIResponse,
) -> None:

    if not is_cacheable(request):
        return

    redis = await get_redis()

    await redis.set(
        build_cache_key(request),
        response.model_dump_json(),
        ex=settings.cache_ttl_seconds,
    )
