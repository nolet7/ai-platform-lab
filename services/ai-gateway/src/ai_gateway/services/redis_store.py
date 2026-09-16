from redis.asyncio import Redis
from redis.exceptions import RedisError

from ai_gateway.config import settings

_redis: Redis | None = None


async def get_redis() -> Redis:
    global _redis

    if _redis is None:
        _redis = Redis.from_url(
            settings.redis_url,
            decode_responses=True,
        )

    return _redis


async def redis_health() -> bool:
    if not settings.redis_enabled:
        return False

    try:
        redis = await get_redis()
        return bool(await redis.ping())
    except RedisError:
        return False


async def close_redis() -> None:
    global _redis

    if _redis is not None:
        await _redis.aclose()
        _redis = None
