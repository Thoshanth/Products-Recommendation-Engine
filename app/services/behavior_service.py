"""
behavior_service.py — Track all user events in Valkey.

Key Schema:
  behavior:{user_id}:events          → List  (last 500 raw events JSON)
  behavior:{user_id}:category_score  → Hash  (category → affinity float)
  behavior:{user_id}:product_counts  → Hash  (product_id → interaction count)
  behavior:{user_id}:search_history  → List  (last 50 search queries)
  trending:products:daily            → ZSet  (product_id → score, TTL 24h)
  trending:products:weekly           → ZSet  (product_id → score, TTL 7d)
  trending:categories:daily          → ZSet  (category → score)
  analytics:events:total             → String (global event counter)
"""

import json
import uuid
from datetime import datetime
from typing import Optional
from app.core.database import get_valkey
from app.models.schemas import BehaviorEvent, BehaviorEventCreate, BehaviorEventType

# ── Event weights for affinity scoring ────────────────────────────────────────
EVENT_WEIGHTS = {
    BehaviorEventType.VIEW:            1.0,
    BehaviorEventType.CLICK:           1.5,
    BehaviorEventType.SEARCH:          0.8,
    BehaviorEventType.ADD_WISHLIST:    3.0,
    BehaviorEventType.REMOVE_WISHLIST: -1.0,
    BehaviorEventType.ADD_TO_CART:     4.0,
    BehaviorEventType.REMOVE_CART:     -2.0,
    BehaviorEventType.PURCHASE:        10.0,
    BehaviorEventType.REVIEW:          5.0,
    BehaviorEventType.SHARE:           2.0,
    BehaviorEventType.RETURN:          -5.0,
}

# Trending score weights (separate from affinity)
TRENDING_WEIGHTS = {
    BehaviorEventType.VIEW:         1,
    BehaviorEventType.CLICK:        2,
    BehaviorEventType.ADD_TO_CART:  5,
    BehaviorEventType.PURCHASE:     10,
    BehaviorEventType.ADD_WISHLIST: 3,
    BehaviorEventType.REVIEW:       4,
}

MAX_EVENTS_PER_USER = 500
MAX_SEARCH_HISTORY  = 50


def track_event(user_id: str, data: BehaviorEventCreate) -> BehaviorEvent:
    db = get_valkey()

    event = BehaviorEvent(
        id=f"evt-{str(uuid.uuid4())[:8]}",
        user_id=user_id,
        **data.model_dump(),
        timestamp=datetime.utcnow().isoformat(),
    )

    raw = event.model_dump_json()

    # 1. Append to user event list (capped)
    events_key = f"behavior:{user_id}:events"
    db.rpush(events_key, raw)
    db.ltrim(events_key, -MAX_EVENTS_PER_USER, -1)

    # 2. Update category affinity score
    if data.category:
        weight = EVENT_WEIGHTS.get(data.event_type, 1.0)
        db.hincrbyfloat(f"behavior:{user_id}:category_score", data.category, weight)

    # 3. Update per-product interaction count
    if data.product_id:
        weight = EVENT_WEIGHTS.get(data.event_type, 1.0)
        db.hincrbyfloat(f"behavior:{user_id}:product_counts", data.product_id, weight)

        # 4. Update trending sorted sets
        trending_score = TRENDING_WEIGHTS.get(data.event_type, 0)
        if trending_score > 0:
            db.zincrby("trending:products:daily",  trending_score, data.product_id)
            db.zincrby("trending:products:weekly", trending_score, data.product_id)
            # Set TTL on first creation
            if db.ttl("trending:products:daily") == -1:
                db.expire("trending:products:daily",  86400)       # 24 hours
            if db.ttl("trending:products:weekly") == -1:
                db.expire("trending:products:weekly", 86400 * 7)   # 7 days

    # 5. Update trending categories
    if data.category:
        db.zincrby("trending:categories:daily", 1, data.category)
        if db.ttl("trending:categories:daily") == -1:
            db.expire("trending:categories:daily", 86400)

    # 6. Track search queries
    if data.event_type == BehaviorEventType.SEARCH and data.search_query:
        search_key = f"behavior:{user_id}:search_history"
        db.rpush(search_key, data.search_query)
        db.ltrim(search_key, -MAX_SEARCH_HISTORY, -1)
        # Global search popularity
        db.zincrby("trending:searches:daily", 1, data.search_query.lower())
        if db.ttl("trending:searches:daily") == -1:
            db.expire("trending:searches:daily", 86400)

    # 7. Global event counter
    db.incr("analytics:events:total")
    db.incr(f"analytics:events:{data.event_type.value}")

    return event


# ── Read: User Behavior ────────────────────────────────────────────────────────

def get_user_events(user_id: str, limit: int = 50) -> list[BehaviorEvent]:
    db       = get_valkey()
    raw_list = db.lrange(f"behavior:{user_id}:events", -limit, -1)
    events   = []
    for r in raw_list:
        try:
            events.append(BehaviorEvent(**json.loads(r)))
        except Exception:
            continue
    return list(reversed(events))  # newest first


def get_user_category_affinity(user_id: str) -> dict[str, float]:
    """Returns {category: affinity_score} sorted by score desc."""
    db  = get_valkey()
    raw = db.hgetall(f"behavior:{user_id}:category_score")
    scores = {cat: float(score) for cat, score in raw.items()}
    return dict(sorted(scores.items(), key=lambda x: x[1], reverse=True))


def get_user_product_interactions(user_id: str) -> dict[str, float]:
    """Returns {product_id: interaction_score} sorted by score desc."""
    db  = get_valkey()
    raw = db.hgetall(f"behavior:{user_id}:product_counts")
    scores = {pid: float(score) for pid, score in raw.items()}
    return dict(sorted(scores.items(), key=lambda x: x[1], reverse=True))


def get_user_search_history(user_id: str, limit: int = 20) -> list[str]:
    db = get_valkey()
    return list(reversed(db.lrange(f"behavior:{user_id}:search_history", -limit, -1)))


def get_top_interacted_products(user_id: str, limit: int = 20) -> list[str]:
    """Returns product_ids the user has interacted with most."""
    interactions = get_user_product_interactions(user_id)
    return list(interactions.keys())[:limit]


def get_top_categories(user_id: str, limit: int = 5) -> list[str]:
    """Returns user's top N preferred categories by affinity score."""
    affinity = get_user_category_affinity(user_id)
    return list(affinity.keys())[:limit]


# ── Read: Trending ─────────────────────────────────────────────────────────────

def get_trending_products(period: str = "daily", limit: int = 20) -> list[dict]:
    """
    Returns [{product_id, score}] for trending products.
    period: 'daily' | 'weekly'
    """
    db  = get_valkey()
    key = f"trending:products:{period}"
    raw = db.zrevrange(key, 0, limit - 1, withscores=True)
    return [{"product_id": pid, "score": score} for pid, score in raw]


def get_trending_categories(limit: int = 10) -> list[dict]:
    db  = get_valkey()
    raw = db.zrevrange("trending:categories:daily", 0, limit - 1, withscores=True)
    return [{"category": cat, "score": score} for cat, score in raw]


def get_trending_searches(limit: int = 10) -> list[dict]:
    db  = get_valkey()
    raw = db.zrevrange("trending:searches:daily", 0, limit - 1, withscores=True)
    return [{"query": q, "count": int(score)} for q, score in raw]


# ── Read: Analytics ────────────────────────────────────────────────────────────

def get_global_analytics() -> dict:
    db = get_valkey()
    event_types = [e.value for e in BehaviorEventType]
    per_type = {}
    for et in event_types:
        val = db.get(f"analytics:events:{et}")
        per_type[et] = int(val) if val else 0

    total_users    = db.scard("users:all")
    total_products = db.scard("products:all")
    total_events   = db.get("analytics:events:total")

    return {
        "total_users":    int(total_users),
        "total_products": int(total_products),
        "total_events":   int(total_events) if total_events else 0,
        "events_by_type": per_type,
        "trending_products_today": len(get_trending_products("daily")),
    }


def get_user_analytics_summary(user_id: str) -> dict:
    db = get_valkey()
    events       = get_user_events(user_id, limit=500)
    category_aff = get_user_category_affinity(user_id)
    product_ints = get_user_product_interactions(user_id)
    searches     = get_user_search_history(user_id, limit=50)

    # Count by event type
    type_counts: dict[str, int] = {}
    for evt in events:
        key = evt.event_type.value if hasattr(evt.event_type, "value") else str(evt.event_type)
        type_counts[key] = type_counts.get(key, 0) + 1

    return {
        "user_id":              user_id,
        "total_events":         len(events),
        "events_by_type":       type_counts,
        "top_categories":       list(category_aff.items())[:5],
        "top_products":         list(product_ints.items())[:5],
        "recent_searches":      searches[:10],
        "total_products_viewed": len(product_ints),
        "engagement_score":     round(sum(product_ints.values()), 2),
    }