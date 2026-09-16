import time
from dataclasses import dataclass

from ai_gateway.config import settings
from ai_gateway.services.redis_store import get_redis

RATE_LIMIT_SCRIPT = """
local current = redis.call("INCR", KEYS[1])

if current == 1 then
    redis.call("EXPIRE", KEYS[1], ARGV[1])
end

return current
"""


@dataclass
class RateLimitDecision:
    allowed: bool
    limit: int
    remaining: int
    retry_after: int


async def check_rate_limit(tenant_id: str) -> RateLimitDecision:
    if not settings.redis_enabled:
        return RateLimitDecision(
            allowed=True,
            limit=settings.rate_limit_per_minute,
            remaining=settings.rate_limit_per_minute,
            retry_after=0,
        )

    redis = await get_redis()

    current_window = int(time.time() // 60)

    key = f"ai-gateway:ratelimit:{tenant_id}:{current_window}"

    count = await redis.eval(
        RATE_LIMIT_SCRIPT,
        1,
        key,
        70,
    )

    count = int(count)

    remaining = max(
        settings.rate_limit_per_minute - count,
        0,
    )

    return RateLimitDecision(
        allowed=count <= settings.rate_limit_per_minute,
        limit=settings.rate_limit_per_minute,
        remaining=remaining,
        retry_after=60,
    )
