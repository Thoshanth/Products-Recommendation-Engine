"""
users.py — User profile, addresses, wishlist, loyalty endpoints.
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional
from app.models.schemas import (
    UserUpdate, AddressCreate, MessageResponse,
    User, Wishlist, WishlistItem,
)
from app.services import user_service
from app.core.dependencies import get_current_user_id
from app.services.product_service import get_product
from app.core.database import get_valkey
import json
from datetime import datetime

router = APIRouter(prefix="/users", tags=["Users"])


# ── Profile ────────────────────────────────────────────────────────────────────

@router.get("/me")
def get_my_profile(user_id: str = Depends(get_current_user_id)):
    """Get current user's full profile."""
    user = user_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    addresses = user_service.get_addresses(user_id)
    return {"user": user, "addresses": addresses}


@router.patch("/me")
def update_my_profile(data: UserUpdate, user_id: str = Depends(get_current_user_id)):
    """Update profile fields."""
    user = user_service.update_user(user_id, data)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"success": True, "user": user}


@router.delete("/me", response_model=MessageResponse)
def deactivate_my_account(user_id: str = Depends(get_current_user_id)):
    """Soft-delete (deactivate) the current user account."""
    ok = user_service.deactivate_user(user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="User not found")
    return MessageResponse(success=True, message="Account deactivated")


# ── Addresses ──────────────────────────────────────────────────────────────────

@router.get("/me/addresses")
def get_my_addresses(user_id: str = Depends(get_current_user_id)):
    return {"addresses": user_service.get_addresses(user_id)}


@router.post("/me/addresses", status_code=status.HTTP_201_CREATED)
def add_address(data: AddressCreate, user_id: str = Depends(get_current_user_id)):
    addr = user_service.add_address(user_id, data)
    return {"success": True, "address": addr}


@router.delete("/me/addresses/{address_id}", response_model=MessageResponse)
def delete_address(address_id: str, user_id: str = Depends(get_current_user_id)):
    ok = user_service.delete_address(user_id, address_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Address not found")
    return MessageResponse(success=True, message="Address deleted")


@router.patch("/me/addresses/{address_id}/default", response_model=MessageResponse)
def set_default_address(address_id: str, user_id: str = Depends(get_current_user_id)):
    ok = user_service.set_default_address(user_id, address_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Address not found")
    return MessageResponse(success=True, message="Default address updated")


# ── Wishlist ───────────────────────────────────────────────────────────────────

def _wishlist_key(uid): return f"user:{uid}:wishlist"

@router.get("/me/wishlist")
def get_wishlist(user_id: str = Depends(get_current_user_id)):
    db = get_valkey()
    raw_list = db.lrange(_wishlist_key(user_id), 0, -1)
    items = [WishlistItem(**json.loads(r)) for r in raw_list]
    return Wishlist(user_id=user_id, items=items, count=len(items))


@router.post("/me/wishlist/{product_id}", response_model=MessageResponse)
def add_to_wishlist(product_id: str, user_id: str = Depends(get_current_user_id)):
    db = get_valkey()
    # Check if already in wishlist
    existing = db.lrange(_wishlist_key(user_id), 0, -1)
    for r in existing:
        item = json.loads(r)
        if item["product_id"] == product_id:
            return MessageResponse(success=False, message="Already in wishlist")

    product = get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    item = WishlistItem(
        product_id=product.id, product_name=product.name,
        thumbnail_url=product.thumbnail_url, selling_price=product.selling_price,
        mrp=product.mrp, in_stock=product.in_stock,
    )
    db.rpush(_wishlist_key(user_id), item.model_dump_json())
    return MessageResponse(success=True, message="Added to wishlist")


@router.delete("/me/wishlist/{product_id}", response_model=MessageResponse)
def remove_from_wishlist(product_id: str, user_id: str = Depends(get_current_user_id)):
    db = get_valkey()
    raw_list = db.lrange(_wishlist_key(user_id), 0, -1)
    new_list = [r for r in raw_list if json.loads(r)["product_id"] != product_id]
    if len(new_list) == len(raw_list):
        raise HTTPException(status_code=404, detail="Item not in wishlist")
    db.delete(_wishlist_key(user_id))
    for r in new_list:
        db.rpush(_wishlist_key(user_id), r)
    return MessageResponse(success=True, message="Removed from wishlist")


# ── Loyalty ────────────────────────────────────────────────────────────────────

@router.get("/me/loyalty")
def get_loyalty(user_id: str = Depends(get_current_user_id)):
    user = user_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    tier_thresholds = {"Bronze": 0, "Silver": 1000, "Gold": 5000, "Platinum": 10000}
    tier_order = ["Bronze", "Silver", "Gold", "Platinum"]
    current_idx = tier_order.index(user.loyalty_tier)
    next_tier = tier_order[current_idx + 1] if current_idx < 3 else None
    points_to_next = (tier_thresholds[next_tier] - user.loyalty_points) if next_tier else 0

    return {
        "loyalty_points": user.loyalty_points,
        "loyalty_tier": user.loyalty_tier,
        "next_tier": next_tier,
        "points_to_next_tier": max(0, points_to_next),
        "tier_benefits": {
            "Bronze":   ["Early sale access"],
            "Silver":   ["Early sale access", "Free shipping on orders > ₹499"],
            "Gold":     ["Early sale access", "Free shipping always", "5% extra discount"],
            "Platinum": ["Early sale access", "Free express shipping", "10% extra discount", "Dedicated support"],
        }.get(user.loyalty_tier, []),
    }


# ── Stats ──────────────────────────────────────────────────────────────────────

@router.get("/me/stats")
def get_my_stats(user_id: str = Depends(get_current_user_id)):
    """Dashboard stats for the current user."""
    user = user_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db = get_valkey()
    wishlist_count = db.llen(_wishlist_key(user_id))
    return {
        "total_orders":    user.total_orders,
        "total_spent":     user.total_spent,
        "avg_order_value": user.avg_order_value,
        "loyalty_points":  user.loyalty_points,
        "loyalty_tier":    user.loyalty_tier,
        "wishlist_count":  wishlist_count,
        "is_premium":      user.is_premium,
        "member_since":    user.created_at[:10],
    }