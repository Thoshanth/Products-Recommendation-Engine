"""test_cache.py — Unit tests for cache utilities."""
from app.middleware.cache_middleware import _get_ttl, CACHE_RULES
from app.middleware.rate_limiter import ENDPOINT_LIMITS, DEFAULT_LIMITS


def test_featured_products_cache_ttl():
    assert _get_ttl("/api/v1/products/featured") == 300


def test_trending_cache_ttl():
    assert _get_ttl("/api/v1/recommendations/trending") == 60


def test_unknown_path_returns_zero_ttl():
    assert _get_ttl("/api/v1/users/me") == 0


def test_auth_path_returns_zero_ttl():
    assert _get_ttl("/api/v1/auth/login") == 0


def test_all_cache_rules_have_positive_ttl():
    for path, ttl in CACHE_RULES:
        assert ttl > 0, f"TTL for {path} must be positive"


def test_rate_limit_auth_stricter_than_default():
    auth_limit = ENDPOINT_LIMITS["/api/v1/auth/login"]["minute"]
    assert auth_limit < DEFAULT_LIMITS["minute"]


def test_behavior_track_has_high_limit():
    track_limit = ENDPOINT_LIMITS["/api/v1/behavior/track"]["minute"]
    assert track_limit >= 60


def test_default_limits_are_set():
    assert DEFAULT_LIMITS["minute"] > 0
    assert DEFAULT_LIMITS["hour"] > 0
    assert DEFAULT_LIMITS["hour"] > DEFAULT_LIMITS["minute"]