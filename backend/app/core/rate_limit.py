import logging
import time
from dataclasses import dataclass

import redis
from fastapi import HTTPException, Request, status

from app.core.config import Settings

logger = logging.getLogger(__name__)


@dataclass
class RateLimitResult:
    allowed: bool
    retry_after: int | None = None


class RateLimiter:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._client: redis.Redis | None = None

    @property
    def client(self) -> redis.Redis:
        if self._client is None:
            self._client = redis.Redis.from_url(
                str(self.settings.redis_url),
                decode_responses=True,
            )
        return self._client

    def _client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "unknown"

    def check(self, request: Request, *, scope: str) -> RateLimitResult:
        ip = self._client_ip(request)
        key = f"rl:{scope}:{ip}"
        window = self.settings.auth_rate_limit_window_seconds
        limit = self.settings.auth_rate_limit_requests

        try:
            current = self.client.incr(key)
            if current == 1:
                self.client.expire(key, window)

            if current > limit:
                ttl = self.client.ttl(key)
                return RateLimitResult(allowed=False, retry_after=max(ttl, 1))
        except redis.RedisError:
            logger.warning("Rate limiter unavailable; allowing request")
            return RateLimitResult(allowed=True)

        return RateLimitResult(allowed=True)


def enforce_rate_limit(limiter: RateLimiter, request: Request, *, scope: str) -> None:
    result = limiter.check(request, scope=scope)
    if not result.allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please try again later.",
            headers={"Retry-After": str(result.retry_after or 60)},
        )
