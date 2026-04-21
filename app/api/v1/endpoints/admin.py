"""
admin.py — Cache management, performance stats, system health endpoints.
"""
from fastapi import APIRouter, HTTPException, Path
from app.utils.cache import get_cache_stats, flush_cache_by_type, invalidate_pattern
from app.utils.performance import get_performance_stats
from app.core.database import ping_valkey, get_valkey
from app.services.cart_service import seed_coupons

router = APIRouter(prefix="/admin", tags=["Admin & Performance"])


@router.get("/stats/cache")
def cache_stats():
    """
    Full Valkey cache statistics.
    Shows key counts by type: HTTP cache, reco cache, sessions, rate limits, etc.
    """
    return get_cache_stats()


@router.get("/stats/performance")
def performance_stats():
    """
    API performance stats: slow requests, top endpoints by hit count.
    """
    return get_performance_stats()


@router.get("/stats/valkey")
def valkey_stats():
    """Raw Valkey server info and memory usage."""
    db = get_valkey()
    try:
        info = db.info()
        return {
            "connected":          True,
            "valkey_version":     info.get("redis_version") or info.get("valkey_version", "unknown"),
            "used_memory_human":  info.get("used_memory_human", "N/A"),
            "total_commands_processed": info.get("total_commands_processed", 0),
            "connected_clients":  info.get("connected_clients", 0),
            "total_keys":         db.dbsize(),
            "uptime_in_seconds":  info.get("uptime_in_seconds", 0),
            "keyspace_hits":      info.get("keyspace_hits", 0),
            "keyspace_misses":    info.get("keyspace_misses", 0),
            "hit_rate_pct": round(
                info.get("keyspace_hits", 0) /
                max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 1), 1) * 100, 1
            ),
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Valkey error: {e}")


@router.delete("/cache/{cache_type}")
def flush_cache(
    cache_type: str = Path(..., description="Types: http, recommendations, rate_limits, trending"),
):
    """
    Flush a specific cache type.
    - http: HTTP response cache
    - recommendations: AI reco cache
    - rate_limits: Reset all rate limit counters
    - trending: Reset trending sorted sets
    """
    result = flush_cache_by_type(cache_type)
    return {"success": True, **result}


@router.delete("/cache/user/{user_id}")
def flush_user_cache(user_id: str):
    """Flush all cached data for a specific user."""
    from app.utils.cache import invalidate_user_caches
    invalidate_user_caches(user_id)
    return {"success": True, "message": f"Cache cleared for user {user_id}"}


@router.post("/coupons/seed")
def reseed_coupons():
    """Re-seed default coupons into Valkey."""
    seed_coupons()
    return {"success": True, "message": "Coupons re-seeded"}


@router.get("/health/detailed")
def detailed_health():
    """Deep health check with component status."""
    db        = get_valkey()
    valkey_ok = ping_valkey()

    checks = {
        "valkey":    {"status": "up" if valkey_ok else "down"},
        "products":  {"count": db.scard("products:all")   if valkey_ok else 0},
        "users":     {"count": db.scard("users:all")      if valkey_ok else 0},
        "orders":    {"count": db.scard("orders:all")     if valkey_ok else 0},
        "sessions":  {"count": len(db.keys("session:*"))  if valkey_ok else 0},
    }

    overall = "healthy" if valkey_ok else "degraded"
    return {"status": overall, "checks": checks}