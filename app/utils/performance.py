"""
performance.py — Request timing, slow query detection, performance monitoring.
"""

import time
import json
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from app.core.database import get_valkey

# Log requests slower than this (ms)
SLOW_REQUEST_THRESHOLD_MS = 500

# Keep last N slow requests
MAX_SLOW_REQUESTS = 100


class PerformanceMiddleware(BaseHTTPMiddleware):
    """Adds X-Process-Time header and logs slow requests to Valkey."""

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)

        response.headers["X-Process-Time-Ms"] = str(elapsed_ms)

        # Log slow requests
        if elapsed_ms > SLOW_REQUEST_THRESHOLD_MS:
            _log_slow_request(request, elapsed_ms)

        # Track endpoint hit count
        _track_endpoint(request.url.path, request.method)

        return response


def _log_slow_request(request: Request, elapsed_ms: float):
    db = get_valkey()
    entry = json.dumps({
        "path":       request.url.path,
        "method":     request.method,
        "query":      str(request.url.query),
        "elapsed_ms": elapsed_ms,
        "timestamp":  time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    })
    db.lpush("perf:slow_requests", entry)
    db.ltrim("perf:slow_requests", 0, MAX_SLOW_REQUESTS - 1)
    db.incr("perf:slow_request_count")


def _track_endpoint(path: str, method: str):
    db = get_valkey()
    db.zincrby("perf:endpoint_hits", 1, f"{method}:{path}")


def get_performance_stats() -> dict:
    db = get_valkey()

    slow_raw  = db.lrange("perf:slow_requests", 0, 9)
    slow_reqs = []
    for r in slow_raw:
        try:
            slow_reqs.append(json.loads(r))
        except Exception:
            continue

    # Top 10 most hit endpoints
    top_endpoints_raw = db.zrevrange("perf:endpoint_hits", 0, 9, withscores=True)
    top_endpoints = [
        {"endpoint": ep, "hits": int(hits)}
        for ep, hits in top_endpoints_raw
    ]

    return {
        "slow_request_count":  int(db.get("perf:slow_request_count") or 0),
        "recent_slow_requests": slow_reqs,
        "top_endpoints":        top_endpoints,
        "slow_threshold_ms":   SLOW_REQUEST_THRESHOLD_MS,
    }