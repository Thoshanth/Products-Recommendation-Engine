"""
cache_middleware.py — Response caching middleware for GET endpoints.

Automatically caches GET responses in Valkey.
Cache is bypassed when:
  - Authorization header present (personalized content)
  - Query param ?nocache=1
  - POST / PATCH / DELETE methods
"""

import json
import hashlib
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from app.core.database import get_valkey

# ── Cache TTLs per path prefix ─────────────────────────────────────────────────
CACHE_RULES: list[tuple[str, int]] = [
    ("/api/v1/products/featured",         300),   # 5 min
    ("/api/v1/products/top-rated",        300),   # 5 min
    ("/api/v1/recommendations/trending",  60),    # 1 min
    ("/api/v1/recommendations/popular",   120),   # 2 min
    ("/api/v1/recommendations/new",       300),   # 5 min
    ("/api/v1/behavior/trending",         60),    # 1 min
    ("/api/v1/behavior/analytics/global", 120),   # 2 min
    ("/api/v1/products/category/",        180),   # 3 min
    ("/api/v1/products/search",           60),    # 1 min
]

# Paths that must NEVER be cached
NEVER_CACHE = {"/api/v1/auth", "/api/v1/cart", "/api/v1/orders", "/api/v1/users/me"}


def _get_ttl(path: str) -> int:
    """Returns TTL in seconds, or 0 if path should not be cached."""
    for prefix, ttl in CACHE_RULES:
        if path.startswith(prefix):
            return ttl
    return 0


def _cache_key(request: Request) -> str:
    raw = f"{request.url.path}?{request.url.query}"
    return f"httpcache:{hashlib.md5(raw.encode()).hexdigest()}"


class ResponseCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Only cache GET requests
        if request.method != "GET":
            return await call_next(request)

        path = request.url.path

        # Never cache auth/personal/write endpoints
        if any(path.startswith(nc) for nc in NEVER_CACHE):
            return await call_next(request)

        # Skip if user authenticated (personalized content)
        if request.headers.get("Authorization"):
            return await call_next(request)

        # Skip if nocache param
        if request.query_params.get("nocache"):
            return await call_next(request)

        ttl = _get_ttl(path)
        if ttl == 0:
            return await call_next(request)

        db  = get_valkey()
        key = _cache_key(request)

        # Check cache hit
        cached = db.get(key)
        if cached:
            data = json.loads(cached)
            return JSONResponse(
                content=data["body"],
                status_code=data["status_code"],
                headers={
                    **data.get("headers", {}),
                    "X-Cache":     "HIT",
                    "X-Cache-TTL": str(db.ttl(key)),
                },
            )

        # Cache miss — call endpoint
        response    = await call_next(request)
        status_code = response.status_code

        if status_code == 200:
            body_bytes = b""
            async for chunk in response.body_iterator:
                body_bytes += chunk

            try:
                body = json.loads(body_bytes)
                db.setex(key, ttl, json.dumps({"body": body, "status_code": status_code, "headers": {}}))
            except Exception:
                pass

            return Response(
                content=body_bytes,
                status_code=status_code,
                media_type="application/json",
                headers={
                    "X-Cache":     "MISS",
                    "X-Cache-TTL": str(ttl),
                },
            )

        return response