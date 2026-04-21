"""
cache.py — Reusable caching decorators and helpers for services.

Usage:
    from app.utils.cache import cached, invalidate_pattern

    @cached("product:{product_id}", ttl=300)
    def get_product(product_id: str): ...

    invalidate_pattern("reco:*")
"""

import json
import functools
from typing import Any, Callable, Optional
from app.core.database import get_valkey


# ── Low-level helpers ──────────────────────────────────────────────────────────

def cache_get(key: str) -> Optional[Any]:
    db  = get_valkey()
    raw = db.get(key)
    if raw:
        try:
            return json.loads(raw)
        except Exception:
            return raw
    return None


def cache_set(key: str, value: Any, ttl: int = 300):
    db = get_valkey()
    try:
        db.setex(key, ttl, json.dumps(value, default=str))
    except Exception as e:
        print(f"[Cache Set Error] {key}: {e}")


def cache_delete(key: str):
    get_valkey().delete(key)


def cache_delete_many(*keys: str):
    db = get_valkey()
    if keys:
        db.delete(*keys)


def invalidate_pattern(pattern: str) -> int:
    """Delete all keys matching a pattern. Returns count of deleted keys."""
    db   = get_valkey()
    keys = db.keys(pattern)
    if keys:
        db.delete(*keys)
    return len(keys)


def invalidate_user_caches(user_id: str):
    """Wipe all cached data related to a user."""
    invalidate_pattern(f"reco:{user_id}:*")
    invalidate_pattern(f"httpcache:*")   # broad reset on user action
    cache_delete(f"reco:popular")
    cache_delete(f"reco:trending:daily")


# ── Cache Stats ────────────────────────────────────────────────────────────────

def get_cache_stats() -> dict:
    """Return cache key counts by prefix."""
    db = get_valkey()
    return {
        "http_cache_keys":        len(db.keys("httpcache:*")),
        "reco_cache_keys":        len(db.keys("reco:*")),
        "rate_limit_keys":        len(db.keys("ratelimit:*")),
        "blocked_ips":            len(db.keys("blocked:*")),
        "session_keys":           len(db.keys("session:*")),
        "behavior_keys":          len(db.keys("behavior:*")),
        "trending_keys":          len(db.keys("trending:*")),
        "total_products":         db.scard("products:all"),
        "total_users":            db.scard("users:all"),
        "total_orders":           db.scard("orders:all"),
    }


def flush_cache_by_type(cache_type: str) -> dict:
    """
    Flush a specific type of cache.
    Types: http, recommendations, rate_limits, trending
    """
    patterns = {
        "http":            "httpcache:*",
        "recommendations": "reco:*",
        "rate_limits":     "ratelimit:*",
        "trending":        "trending:*",
        "all_cache":       "httpcache:*",
    }
    pattern = patterns.get(cache_type)
    if not pattern:
        return {"error": f"Unknown cache type: {cache_type}"}

    count = invalidate_pattern(pattern)
    return {"flushed": count, "type": cache_type}