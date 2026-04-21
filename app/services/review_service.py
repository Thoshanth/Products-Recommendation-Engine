"""
review_service.py — Product reviews with verified purchase check.

Key Schema:
  review:{id}                → Hash  (review data)
  reviews:product:{pid}      → List  (review IDs for a product)
  reviews:user:{uid}         → List  (review IDs by a user)
  review:helpful:{id}:{uid}  → String (voted flag, TTL 30d)
"""

import json
import uuid
from datetime import datetime
from typing import Optional
from app.core.database import get_valkey
from app.services.order_service import get_user_orders
from app.models.schemas import Review, ReviewCreate, ReviewImage


def _key(rid):       return f"review:{rid}"
def _prod_key(pid):  return f"reviews:product:{pid}"
def _user_key(uid):  return f"reviews:user:{uid}"


def _serialize(r: Review) -> dict:
    return {
        "id":                   r.id,
        "product_id":           r.product_id,
        "user_id":              r.user_id,
        "user_name":            r.user_name,
        "user_avatar":          r.user_avatar or "",
        "order_id":             r.order_id or "",
        "rating":               str(r.rating),
        "title":                r.title,
        "body":                 r.body,
        "pros":                 json.dumps(r.pros),
        "cons":                 json.dumps(r.cons),
        "images":               json.dumps([i.model_dump() for i in r.images]),
        "helpful_votes":        str(r.helpful_votes),
        "not_helpful_votes":    str(r.not_helpful_votes),
        "is_verified_purchase": str(r.is_verified_purchase),
        "is_featured":          str(r.is_featured),
        "seller_reply":         r.seller_reply or "",
        "created_at":           r.created_at,
        "updated_at":           r.updated_at,
    }


def _deserialize(raw: dict) -> Review:
    return Review(
        id=raw["id"], product_id=raw["product_id"],
        user_id=raw["user_id"], user_name=raw["user_name"],
        user_avatar=raw.get("user_avatar") or None,
        order_id=raw.get("order_id") or None,
        rating=int(raw.get("rating", 3)),
        title=raw.get("title", ""), body=raw.get("body", ""),
        pros=json.loads(raw.get("pros", "[]")),
        cons=json.loads(raw.get("cons", "[]")),
        images=[ReviewImage(**i) for i in json.loads(raw.get("images", "[]"))],
        helpful_votes=int(raw.get("helpful_votes", 0)),
        not_helpful_votes=int(raw.get("not_helpful_votes", 0)),
        is_verified_purchase=raw.get("is_verified_purchase", "False") == "True",
        is_featured=raw.get("is_featured", "False") == "True",
        seller_reply=raw.get("seller_reply") or None,
        created_at=raw.get("created_at", datetime.utcnow().isoformat()),
        updated_at=raw.get("updated_at", datetime.utcnow().isoformat()),
    )


def _is_verified_purchase(user_id: str, product_id: str) -> tuple[bool, Optional[str]]:
    """Check if user purchased this product. Returns (is_verified, order_id)."""
    orders, _ = get_user_orders(user_id, per_page=100)
    for order in orders:
        if order.status in ["delivered", "shipped", "out_for_delivery"]:
            for item in order.items:
                if item.product_id == product_id:
                    return True, order.id
    return False, None


def _update_product_rating(product_id: str):
    """Recompute and store product's average rating from all reviews."""
    db      = get_valkey()
    rev_ids = db.lrange(_prod_key(product_id), 0, -1)
    if not rev_ids:
        return

    ratings    = []
    breakdown  = {"5": 0, "4": 0, "3": 0, "2": 0, "1": 0}
    for rid in rev_ids:
        raw = db.hgetall(_key(rid))
        if raw:
            r = int(raw.get("rating", 0))
            if 1 <= r <= 5:
                ratings.append(r)
                breakdown[str(r)] += 1

    if not ratings:
        return

    avg = round(sum(ratings) / len(ratings), 1)
    db.hset(f"product:{product_id}", mapping={
        "rating":           str(avg),
        "rating_count":     str(len(ratings)),
        "rating_breakdown": json.dumps(breakdown),
        "updated_at":       datetime.utcnow().isoformat(),
    })


# ── CRUD ───────────────────────────────────────────────────────────────────────

def create_review(user_id: str, user_name: str, data: ReviewCreate) -> tuple[Optional[Review], str]:
    db = get_valkey()

    # One review per user per product
    existing_ids = db.lrange(_prod_key(data.product_id), 0, -1)
    for rid in existing_ids:
        raw = db.hgetall(_key(rid))
        if raw and raw.get("user_id") == user_id:
            return None, "You have already reviewed this product"

    # Verified purchase check
    is_verified, order_id = _is_verified_purchase(user_id, data.product_id)
    if data.order_id:
        order_id = data.order_id

    rid = f"rev-{str(uuid.uuid4())[:8]}"
    now = datetime.utcnow().isoformat()

    review = Review(
        id=rid,
        product_id=data.product_id,
        user_id=user_id,
        user_name=user_name,
        order_id=order_id,
        rating=data.rating,
        title=data.title,
        body=data.body,
        pros=data.pros,
        cons=data.cons,
        images=data.images,
        is_verified_purchase=is_verified,
        created_at=now,
        updated_at=now,
    )

    db.hset(_key(rid), mapping=_serialize(review))
    db.lpush(_prod_key(data.product_id), rid)
    db.lpush(_user_key(user_id), rid)

    # Mark order item as reviewed
    if order_id:
        db.hset(f"order:{order_id}", mapping={"updated_at": now})

    # Update product rating
    _update_product_rating(data.product_id)

    return review, ""


def get_product_reviews(product_id: str, page: int = 1, per_page: int = 10,
                         sort_by: str = "newest") -> tuple[list[Review], int]:
    db      = get_valkey()
    all_ids = db.lrange(_prod_key(product_id), 0, -1)
    reviews = []
    for rid in all_ids:
        raw = db.hgetall(_key(rid))
        if raw:
            try:
                reviews.append(_deserialize(raw))
            except Exception:
                continue

    if sort_by == "highest_rating":
        reviews.sort(key=lambda r: r.rating, reverse=True)
    elif sort_by == "lowest_rating":
        reviews.sort(key=lambda r: r.rating)
    elif sort_by == "most_helpful":
        reviews.sort(key=lambda r: r.helpful_votes, reverse=True)
    else:
        reviews.sort(key=lambda r: r.created_at, reverse=True)

    total = len(reviews)
    start = (page - 1) * per_page
    return reviews[start:start + per_page], total


def get_user_reviews(user_id: str) -> list[Review]:
    db      = get_valkey()
    all_ids = db.lrange(_user_key(user_id), 0, -1)
    reviews = []
    for rid in all_ids:
        raw = db.hgetall(_key(rid))
        if raw:
            try:
                reviews.append(_deserialize(raw))
            except Exception:
                continue
    return reviews


def vote_helpful(review_id: str, user_id: str, is_helpful: bool) -> tuple[bool, str]:
    db       = get_valkey()
    vote_key = f"review:helpful:{review_id}:{user_id}"

    if db.exists(vote_key):
        return False, "You have already voted on this review"

    raw = db.hgetall(_key(review_id))
    if not raw:
        return False, "Review not found"

    if is_helpful:
        db.hincrby(_key(review_id), "helpful_votes", 1)
    else:
        db.hincrby(_key(review_id), "not_helpful_votes", 1)

    db.setex(vote_key, 86400 * 30, "1")   # one vote per 30 days
    return True, "Vote recorded"


def delete_review(review_id: str, user_id: str) -> tuple[bool, str]:
    db  = get_valkey()
    raw = db.hgetall(_key(review_id))
    if not raw:
        return False, "Review not found"
    if raw.get("user_id") != user_id:
        return False, "Unauthorized"

    product_id = raw.get("product_id", "")
    db.delete(_key(review_id))

    # Remove from product + user lists
    all_prod = db.lrange(_prod_key(product_id), 0, -1)
    db.delete(_prod_key(product_id))
    for rid in all_prod:
        if rid != review_id:
            db.rpush(_prod_key(product_id), rid)

    all_user = db.lrange(_user_key(user_id), 0, -1)
    db.delete(_user_key(user_id))
    for rid in all_user:
        if rid != review_id:
            db.rpush(_user_key(user_id), rid)

    _update_product_rating(product_id)
    return True, "Review deleted"