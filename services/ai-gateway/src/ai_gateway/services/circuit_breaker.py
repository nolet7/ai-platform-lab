import time
from dataclasses import dataclass

from ai_gateway.config import settings
from ai_gateway.services.redis_store import get_redis


@dataclass(frozen=True)
class CircuitState:
    provider: str
    open: bool
    failure_count: int
    open_until: int | None


def _failure_key(provider: str) -> str:
    return f"ai-gateway:circuit:{provider}:failures"


def _open_key(provider: str) -> str:
    return f"ai-gateway:circuit:{provider}:open-until"


async def get_circuit_state(
    provider: str,
) -> CircuitState:

    if not settings.redis_enabled:
        return CircuitState(
            provider=provider,
            open=False,
            failure_count=0,
            open_until=None,
        )

    redis = await get_redis()

    failures_raw = await redis.get(
        _failure_key(provider)
    )

    open_until_raw = await redis.get(
        _open_key(provider)
    )

    failure_count = (
        int(failures_raw)
        if failures_raw is not None
        else 0
    )

    open_until = (
        int(open_until_raw)
        if open_until_raw is not None
        else None
    )

    now = int(time.time())

    if open_until is not None and open_until <= now:
        await redis.delete(
            _open_key(provider),
            _failure_key(provider),
        )

        return CircuitState(
            provider=provider,
            open=False,
            failure_count=0,
            open_until=None,
        )

    return CircuitState(
        provider=provider,
        open=open_until is not None,
        failure_count=failure_count,
        open_until=open_until,
    )


async def record_success(
    provider: str,
) -> None:

    if not settings.redis_enabled:
        return

    redis = await get_redis()

    await redis.delete(
        _failure_key(provider),
        _open_key(provider),
    )


async def record_failure(
    provider: str,
) -> CircuitState:

    if not settings.redis_enabled:
        return CircuitState(
            provider=provider,
            open=False,
            failure_count=1,
            open_until=None,
        )

    redis = await get_redis()

    failure_key = _failure_key(provider)

    count = int(
        await redis.incr(failure_key)
    )

    await redis.expire(
        failure_key,
        settings.circuit_breaker_open_seconds,
    )

    open_until = None

    if count >= settings.circuit_breaker_failure_threshold:
        open_until = (
            int(time.time())
            + settings.circuit_breaker_open_seconds
        )

        await redis.set(
            _open_key(provider),
            open_until,
            ex=settings.circuit_breaker_open_seconds,
        )

    return CircuitState(
        provider=provider,
        open=open_until is not None,
        failure_count=count,
        open_until=open_until,
    )
