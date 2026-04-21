"""
rate_limiter.py — Token bucket rate limiting via Valkey.

Key Schema:
  ratelimit:{ip}:minute   → String counter (TTL 60s)
  ratelimit:{ip}:hour     → String counter (TTL 3600s)
  ratelimit:{uid}:minute  → String counter (TTL 60s)
  ratelimit:{uid}:hour    → String counter (TTL 3600s)
  blocked:{ip}            → String (TTL = block duration)
"""

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from app.core.database import get_valkey
from app.core.config import get_settings
import time

settings = get_settings()

# ── Endpoint-specific limits ───────────────────────────────────────────────────
ENDPOINT_LIMITS = {
    "/api/v1/auth/register":       {"minute": 5,   "hour": 20},
    "/api/v1/auth/login":          {"minute": 10,  "hour": 50},
    "/api/v1/auth/login/form":     {"minute": 10,  "hour": 50},
    "/api/v1/recommendations/me":  {"minute": 30,  "hour": 300},
    "/api/v1/behavior/track":      {"minute": 120, "hour": 2000},
    "/api/v1/orders":              {"minute": 10,  "hour": 100},
}

DEFAULT_LIMITS = {
    "minute": settings.rate_limit_per_minute,
    "hour":   settings.rate_limit_per_hour,
}

# IPs exempt from rate limiting
WHITELISTED_IPS = {"127.0.0.1", "::1"}


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _check_limit(key: str, limit: int, window_secs: int) -> tuple[bool, int, int]:
    """
    Increment counter. Returns (is_allowed, current_count, ttl_remaining).
    Uses Valkey pipeline for atomicity.
    """
    db   = get_valkey()
    pipe = db.pipeline()
    pipe.incr(key)
    pipe.ttl(key)
    results = pipe.execute()

    count = results[0]
    ttl   = results[1]

    if ttl == -1:
        db.expire(key, window_secs)
        ttl = window_secs

    return count <= limit, count, ttl


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip health checks and docs
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json", "/"]:
            return await call_next(request)

        ip  = _get_client_ip(request)
        uid = getattr(request.state, "user_id", None)

        # Whitelist check
        if ip in WHITELISTED_IPS:
            return await call_next(request)

        # Check if IP is blocked
        db = get_valkey()
        if db.exists(f"blocked:{ip}"):
            ttl = db.ttl(f"blocked:{ip}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error":   "Too Many Requests",
                    "detail":  "Your IP has been temporarily blocked due to excessive requests.",
                    "retry_after": ttl,
                },
                headers={"Retry-After": str(ttl)},
            )

        # Get limits for this endpoint
        path   = request.url.path
        limits = ENDPOINT_LIMITS.get(path, DEFAULT_LIMITS)

        identifier = f"uid:{uid}" if uid else f"ip:{ip}"

        # Per-minute check
        min_key    = f"ratelimit:{identifier}:minute:{path[:30]}"
        min_ok, min_count, min_ttl = _check_limit(min_key, limits["minute"], 60)

        if not min_ok:
            # Auto-block IP after 3x the limit in a minute
            if min_count > limits["minute"] * 3:
                db.setex(f"blocked:{ip}", 300, "rate_limit_abuse")  # 5 min block
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error":       "Rate limit exceeded",
                    "detail":      f"Too many requests. Limit: {limits['minute']}/minute.",
                    "retry_after": min_ttl,
                    "limit":       limits["minute"],
                    "window":      "1 minute",
                },
                headers={
                    "X-RateLimit-Limit":     str(limits["minute"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset":     str(int(time.time()) + min_ttl),
                    "Retry-After":           str(min_ttl),
                },
            )

        # Per-hour check
        hr_key    = f"ratelimit:{identifier}:hour:{path[:30]}"
        hr_ok, hr_count, hr_ttl = _check_limit(hr_key, limits["hour"], 3600)

        if not hr_ok:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error":       "Hourly rate limit exceeded",
                    "detail":      f"Too many requests. Limit: {limits['hour']}/hour.",
                    "retry_after": hr_ttl,
                    "limit":       limits["hour"],
                    "window":      "1 hour",
                },
                headers={
                    "X-RateLimit-Limit":     str(limits["hour"]),
                    "X-RateLimit-Remaining": "0",
                    "Retry-After":           str(hr_ttl),
                },
            )

        # Pass through with rate limit headers
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"]     = str(limits["minute"])
        response.headers["X-RateLimit-Remaining"] = str(max(0, limits["minute"] - min_count))
        response.headers["X-RateLimit-Reset"]     = str(int(time.time()) + min_ttl)
        return response