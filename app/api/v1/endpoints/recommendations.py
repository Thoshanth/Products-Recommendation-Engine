"""
recommendations.py — All recommendation API endpoints.
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional
from app.services import recommendation_service
from app.core.dependencies import get_current_user_id, get_current_user_id_optional

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.get("/me")
def get_my_recommendations(
    limit:         int  = Query(20, ge=1, le=50),
    use_ai:        bool = Query(True,  description="Use Nemotron AI scoring"),
    force_refresh: bool = Query(False, description="Bypass cache and recompute"),
    user_id: str = Depends(get_current_user_id),
):
    """
    🤖 Personalized AI recommendations using hybrid engine:
    Content-based (35%) + Trending (25%) + Nemotron AI (40%).
    Results cached in Valkey for 30 minutes.
    """
    return recommendation_service.get_personalized_recommendations(
        user_id, limit=limit, use_ai=use_ai, force_refresh=force_refresh
    )


@router.get("/similar/{product_id}")
def get_similar(
    product_id: str,
    limit:      int = Query(10, ge=1, le=30),
):
    """
    Products similar to a given product.
    Scored by: category match + tag overlap + brand + price proximity.
    Cached in Valkey for 1 hour.
    """
    return recommendation_service.get_similar_recommendations(product_id, limit=limit)


@router.get("/trending")
def get_trending(
    period: str = Query("daily", enum=["daily", "weekly"]),
    limit:  int = Query(20, ge=1, le=50),
):
    """
    Real-time trending products from Valkey Sorted Sets.
    Daily resets every 24h, weekly every 7 days.
    """
    return recommendation_service.get_trending_recommendations(period, limit=limit)


@router.get("/popular")
def get_popular(
    limit: int = Query(20, ge=1, le=50),
    user_id: Optional[str] = Depends(get_current_user_id_optional),
):
    """
    Most popular products by weighted rating × review count.
    Cached 15 minutes.
    """
    return recommendation_service.get_popular_recommendations(limit=limit)


@router.get("/category/{category}")
def get_by_category(
    category: str,
    limit:    int = Query(20, ge=1, le=50),
    user_id:  Optional[str] = Depends(get_current_user_id_optional),
):
    """
    Top products in a category.
    Personalized if user is authenticated (adjusts for interaction history).
    """
    return recommendation_service.get_category_recommendations(
        category, user_id=user_id, limit=limit
    )


@router.get("/new-arrivals")
def get_new_arrivals(
    limit: int = Query(20, ge=1, le=50),
):
    """Latest products sorted by arrival date."""
    return recommendation_service.get_new_arrivals(limit=limit)


@router.post("/me/invalidate-cache")
def invalidate_my_cache(user_id: str = Depends(get_current_user_id)):
    """
    Force-clear recommendation cache for current user.
    Useful after major preference changes.
    """
    recommendation_service.invalidate_user_cache(user_id)
    return {"success": True, "message": "Recommendation cache cleared. Next call will recompute."}