"""
behavior.py — Behavior tracking & analytics API endpoints.
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional
from app.models.schemas import BehaviorEventCreate, MessageResponse
from app.services import behavior_service
from app.core.dependencies import get_current_user_id, get_current_user_id_optional

router = APIRouter(prefix="/behavior", tags=["Behavior & Analytics"])


# ── Track Event ────────────────────────────────────────────────────────────────

@router.post("/track", status_code=201)
def track_event(
    data: BehaviorEventCreate,
    user_id: str = Depends(get_current_user_id),
):
    """
    Track a user behavior event (view, click, add-to-cart, purchase, etc.).
    Automatically updates category affinity, product interaction scores,
    and trending sorted sets in Valkey.
    """
    event = behavior_service.track_event(user_id, data)
    return {
        "success":  True,
        "event_id": event.id,
        "message":  f"Event '{event.event_type}' tracked",
    }


# ── User Behavior ──────────────────────────────────────────────────────────────

@router.get("/me/events")
def get_my_events(
    limit: int = Query(50, ge=1, le=200),
    user_id: str = Depends(get_current_user_id),
):
    """Last N behavior events for the current user, newest first."""
    events = behavior_service.get_user_events(user_id, limit)
    return {"events": events, "count": len(events)}


@router.get("/me/affinity")
def get_my_affinity(user_id: str = Depends(get_current_user_id)):
    """Category affinity scores — drives personalized recommendations."""
    affinity = behavior_service.get_user_category_affinity(user_id)
    return {
        "user_id":  user_id,
        "affinity": affinity,
        "top_categories": list(affinity.keys())[:5],
    }


@router.get("/me/interactions")
def get_my_interactions(user_id: str = Depends(get_current_user_id)):
    """Per-product interaction scores for the current user."""
    interactions = behavior_service.get_user_product_interactions(user_id)
    return {
        "user_id":      user_id,
        "interactions": interactions,
        "total_products_interacted": len(interactions),
    }


@router.get("/me/search-history")
def get_my_search_history(
    limit: int = Query(20, ge=1, le=50),
    user_id: str = Depends(get_current_user_id),
):
    searches = behavior_service.get_user_search_history(user_id, limit)
    return {"searches": searches, "count": len(searches)}


@router.get("/me/summary")
def get_my_analytics_summary(user_id: str = Depends(get_current_user_id)):
    """Full behavior analytics summary for the current user."""
    return behavior_service.get_user_analytics_summary(user_id)


# ── Trending ───────────────────────────────────────────────────────────────────

@router.get("/trending/products")
def get_trending_products(
    period: str = Query("daily", enum=["daily", "weekly"]),
    limit:  int = Query(20, ge=1, le=100),
):
    """
    Trending products by interaction score.
    Backed by Valkey Sorted Sets with automatic TTL (24h daily / 7d weekly).
    """
    raw = behavior_service.get_trending_products(period, limit)
    return {"period": period, "trending": raw, "count": len(raw)}


@router.get("/trending/categories")
def get_trending_categories(limit: int = Query(10, ge=1, le=20)):
    raw = behavior_service.get_trending_categories(limit)
    return {"trending_categories": raw}


@router.get("/trending/searches")
def get_trending_searches(limit: int = Query(10, ge=1, le=50)):
    raw = behavior_service.get_trending_searches(limit)
    return {"trending_searches": raw}


# ── Global Analytics ───────────────────────────────────────────────────────────

@router.get("/analytics/global")
def get_global_analytics():
    """Platform-wide analytics: total events, users, products, trending counts."""
    return behavior_service.get_global_analytics()


@router.get("/analytics/user/{user_id}")
def get_user_analytics(user_id: str):
    """Analytics summary for a specific user (admin use)."""
    return behavior_service.get_user_analytics_summary(user_id)