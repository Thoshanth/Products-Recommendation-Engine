"""
recommendation_service.py — Core AI Recommendation Engine.

Strategies:
  1. Content-Based     — match product tags/category to user affinity
  2. Collaborative     — users-who-interacted-similarly
  3. Trending          — real-time trending from Valkey Sorted Sets
  4. AI-Powered        — Nemotron scores & explains recommendations
  5. Hybrid            — weighted blend of all strategies

Valkey Keys:
  reco:{user_id}:personalized   → String JSON (cached, TTL 30min)
  reco:{user_id}:last_updated   → String (timestamp)
  reco:similar:{product_id}     → String JSON (cached, TTL 1hr)
  reco:popular                  → String JSON (cached, TTL 15min)
"""

import json
import time
from typing import Optional
from datetime import datetime

from app.core.database import get_valkey
from app.core.ai_client import chat_completion
from app.services.product_service import (
    get_product, get_all_products, get_products_by_category,
    get_top_rated_products, get_featured_products,
)
from app.services.behavior_service import (
    get_user_category_affinity, get_user_product_interactions,
    get_trending_products, get_top_categories, get_top_interacted_products,
)
from app.services.user_service import get_user
from app.models.schemas import Product, RecommendedProduct, RecommendationResponse

# ── Cache TTLs ─────────────────────────────────────────────────────────────────
TTL_PERSONALIZED = 60 * 30       # 30 minutes
TTL_SIMILAR      = 60 * 60       # 1 hour
TTL_POPULAR      = 60 * 15       # 15 minutes
TTL_AI_SCORED    = 60 * 45       # 45 minutes

MAX_CANDIDATES   = 50            # products fed into AI scorer
MAX_RESULTS      = 20            # max products returned


# ══════════════════════════════════════════════════════════════════════════════
# STRATEGY 1 — Content-Based Filtering
# ══════════════════════════════════════════════════════════════════════════════

def _content_based(user_id: str, limit: int = 20) -> list[RecommendedProduct]:
    """
    Score products by matching user's category affinity + tag overlap
    with products they haven't interacted with much.
    """
    affinity     = get_user_category_affinity(user_id)
    interactions = get_user_product_interactions(user_id)

    if not affinity:
        # Cold start — return top rated
        products = get_top_rated_products(limit)
        return [
            RecommendedProduct(
                product=p, score=p.rating / 5.0,
                reason="Top rated product on ShopMind",
                strategy="content_based",
            )
            for p in products
        ]

    scored: list[tuple[float, Product, str]] = []

    for category, cat_score in list(affinity.items())[:5]:
        products, _ = get_products_by_category(category, per_page=30)
        for p in products:
            if not p.in_stock or not p.is_active:
                continue

            # Base score from category affinity
            score = min(cat_score / 20.0, 1.0)

            # Boost for rating
            score += (p.rating / 5.0) * 0.3

            # Boost for discount
            score += min(p.discount_pct / 100.0, 0.2)

            # Penalty if already heavily interacted
            interaction = interactions.get(p.id, 0)
            if interaction > 10:
                continue   # already seen a lot
            if interaction > 0:
                score *= 0.7   # slight penalty

            reason = f"Based on your interest in {category.replace('_', ' ').title()}"
            scored.append((score, p, reason))

    scored.sort(key=lambda x: x[0], reverse=True)

    seen = set()
    results = []
    for score, product, reason in scored:
        if product.id in seen:
            continue
        seen.add(product.id)
        results.append(RecommendedProduct(
            product=product,
            score=round(score, 4),
            reason=reason,
            strategy="content_based",
        ))
        if len(results) >= limit:
            break

    return results


# ══════════════════════════════════════════════════════════════════════════════
# STRATEGY 2 — Trending Based
# ══════════════════════════════════════════════════════════════════════════════

def _trending_based(limit: int = 20) -> list[RecommendedProduct]:
    """Products trending right now based on Valkey Sorted Set scores."""
    trending_raw = get_trending_products("daily", limit * 2)

    if not trending_raw:
        # Fallback to featured
        products = get_featured_products(limit)
        return [
            RecommendedProduct(
                product=p, score=0.8,
                reason="Featured on ShopMind AI",
                strategy="trending",
            )
            for p in products
        ]

    max_score = trending_raw[0]["score"] if trending_raw else 1
    results   = []

    for item in trending_raw:
        product = get_product(item["product_id"])
        if not product or not product.in_stock or not product.is_active:
            continue

        normalized = item["score"] / max_score if max_score > 0 else 0
        results.append(RecommendedProduct(
            product=product,
            score=round(normalized, 4),
            reason=f"Trending now — {int(item['score'])} interactions today",
            strategy="trending",
        ))
        if len(results) >= limit:
            break

    return results


# ══════════════════════════════════════════════════════════════════════════════
# STRATEGY 3 — Similar Products (Content Similarity)
# ══════════════════════════════════════════════════════════════════════════════

def _similar_products(product_id: str, limit: int = 10) -> list[RecommendedProduct]:
    """
    Find products similar to a given product by:
    - Same category (high weight)
    - Overlapping tags (medium weight)
    - Similar price range (low weight)
    - Same brand (bonus)
    """
    db          = get_valkey()
    cache_key   = f"reco:similar:{product_id}"
    cached      = db.get(cache_key)

    if cached:
        items = json.loads(cached)
        return [RecommendedProduct(**i) for i in items]

    source = get_product(product_id)
    if not source:
        return []

    all_products, _ = get_all_products(per_page=200)
    scored: list[tuple[float, Product]] = []

    source_tags = set(source.tags)
    source_cat  = source.category if isinstance(source.category, str) else source.category.value

    for p in all_products:
        if p.id == product_id or not p.in_stock or not p.is_active:
            continue

        score = 0.0
        p_cat = p.category if isinstance(p.category, str) else p.category.value

        # Category match
        if p_cat == source_cat:
            score += 0.5

        # Tag overlap
        p_tags   = set(p.tags)
        overlap  = len(source_tags & p_tags)
        if overlap:
            score += min(overlap * 0.1, 0.3)

        # Same brand bonus
        if p.brand_id == source.brand_id:
            score += 0.15

        # Price proximity (within 30%)
        price_diff = abs(p.selling_price - source.selling_price)
        if source.selling_price > 0:
            price_ratio = price_diff / source.selling_price
            if price_ratio < 0.3:
                score += 0.1

        # Rating boost
        score += (p.rating / 5.0) * 0.1

        if score > 0.2:
            scored.append((score, p))

    scored.sort(key=lambda x: x[0], reverse=True)
    results = [
        RecommendedProduct(
            product=p,
            score=round(score, 4),
            reason=f"Similar to {source.name}",
            strategy="similar",
        )
        for score, p in scored[:limit]
    ]

    # Cache it
    db.setex(cache_key, TTL_SIMILAR, json.dumps([r.model_dump() for r in results]))
    return results


# ══════════════════════════════════════════════════════════════════════════════
# STRATEGY 4 — AI-Powered Scoring with Nemotron
# ══════════════════════════════════════════════════════════════════════════════

def _build_user_context(user_id: str) -> str:
    """Build a rich text summary of the user for the AI prompt."""
    user         = get_user(user_id)
    affinity     = get_user_category_affinity(user_id)
    interactions = get_user_product_interactions(user_id)

    top_cats  = list(affinity.items())[:5]
    top_prods = list(interactions.items())[:5]

    lines = []
    if user:
        lines.append(f"User: {user.name}, Age: {user.age or 'unknown'}, Tier: {user.loyalty_tier}")
        lines.append(f"Total orders: {user.total_orders}, Total spent: ₹{user.total_spent:,.0f}")
        if user.preferences.preferred_categories:
            lines.append(f"Stated preferences: {', '.join(user.preferences.preferred_categories[:5])}")
        lines.append(f"Price range: ₹{user.preferences.price_range_min:,.0f} – ₹{user.preferences.price_range_max:,.0f}")

    if top_cats:
        cat_str = ", ".join(f"{c} ({s:.1f})" for c, s in top_cats)
        lines.append(f"Behavioral category affinity: {cat_str}")

    if top_prods:
        lines.append(f"Recently interacted with {len(interactions)} products")

    return "\n".join(lines)


def _build_product_summary(products: list[Product]) -> str:
    """Compact product list for the AI prompt."""
    lines = []
    for i, p in enumerate(products):
        lines.append(
            f"{i+1}. [{p.id}] {p.name} | {p.category} | ₹{p.selling_price:,.0f} "
            f"| Rating: {p.rating}/5 ({p.rating_count} reviews) "
            f"| Tags: {', '.join(p.tags[:5])}"
        )
    return "\n".join(lines)


def _ai_score_products(
    user_id: str,
    candidates: list[Product],
    limit: int = 10,
) -> list[RecommendedProduct]:
    """
    Send candidate products + user context to Nemotron.
    Ask it to rank, score (0.0–1.0) and explain each recommendation.
    Returns parsed RecommendedProduct list.
    """
    if not candidates:
        return []

    user_context    = _build_user_context(user_id)
    product_summary = _build_product_summary(candidates[:MAX_CANDIDATES])

    system_prompt = """You are ShopMind AI, an expert e-commerce recommendation engine.
Your job is to rank products for a specific user based on their behavior and preferences.
You must respond ONLY with valid JSON — no markdown, no explanation outside JSON.

Response format:
{
  "recommendations": [
    {
      "product_id": "prod-xxx",
      "score": 0.95,
      "reason": "One sentence explaining why this suits the user"
    }
  ]
}

Rules:
- Score range: 0.0 to 1.0 (higher = better fit)
- Return at most """ + str(limit) + """ items
- Only include products that genuinely suit the user
- reason must be specific, mention the user's preference or behavior
- Do not include products with score below 0.3"""

    user_prompt = f"""USER PROFILE:
{user_context}

CANDIDATE PRODUCTS TO RANK:
{product_summary}

Rank these products for this user. Return only the JSON."""

    try:
        raw = chat_completion(system_prompt, user_prompt, temperature=0.2, max_tokens=2048)

        # Strip any markdown fences if model adds them
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        data = json.loads(raw)
        recs = data.get("recommendations", [])

        # Map back to Product objects
        product_map = {p.id: p for p in candidates}
        results     = []

        for rec in recs:
            pid     = rec.get("product_id", "")
            score   = float(rec.get("score", 0))
            reason  = rec.get("reason", "Recommended for you")
            product = product_map.get(pid)
            if product and score >= 0.3:
                results.append(RecommendedProduct(
                    product=product,
                    score=round(score, 4),
                    reason=reason,
                    strategy="ai_nemotron",
                ))

        return sorted(results, key=lambda x: x.score, reverse=True)

    except Exception as e:
        # AI failed — fallback to content-based scores
        print(f"[AI Scoring Error] {e}")
        return [
            RecommendedProduct(
                product=p,
                score=round(p.rating / 5.0, 4),
                reason="Highly rated product for you",
                strategy="ai_nemotron_fallback",
            )
            for p in candidates[:limit]
        ]


# ══════════════════════════════════════════════════════════════════════════════
# STRATEGY 5 — Hybrid (Blend All Strategies)
# ══════════════════════════════════════════════════════════════════════════════

def _hybrid(
    user_id: str,
    content_weight:  float = 0.35,
    trending_weight: float = 0.25,
    ai_weight:       float = 0.40,
    limit: int = 20,
) -> list[RecommendedProduct]:
    """
    Weighted blend:
      - Content-based  (35%)
      - Trending       (25%)
      - AI Nemotron    (40%)
    Deduplicates and merges scores.
    """
    content_recs  = _content_based(user_id, limit=30)
    trending_recs = _trending_based(limit=20)

    # Collect unique candidates from content + trending for AI scoring
    seen_ids   = set()
    candidates = []
    for r in content_recs + trending_recs:
        if r.product.id not in seen_ids:
            seen_ids.add(r.product.id)
            candidates.append(r.product)

    ai_recs = _ai_score_products(user_id, candidates[:MAX_CANDIDATES], limit=limit)

    # Build score map per product
    score_map: dict[str, dict] = {}

    for r in content_recs:
        score_map[r.product.id] = {
            "product": r.product,
            "content_score": r.score,
            "trending_score": 0.0,
            "ai_score": 0.0,
            "reasons": [r.reason],
        }

    for r in trending_recs:
        if r.product.id in score_map:
            score_map[r.product.id]["trending_score"] = r.score
            score_map[r.product.id]["reasons"].append(r.reason)
        else:
            score_map[r.product.id] = {
                "product": r.product,
                "content_score": 0.0,
                "trending_score": r.score,
                "ai_score": 0.0,
                "reasons": [r.reason],
            }

    for r in ai_recs:
        if r.product.id in score_map:
            score_map[r.product.id]["ai_score"] = r.score
            score_map[r.product.id]["reasons"].append(r.reason)
        else:
            score_map[r.product.id] = {
                "product": r.product,
                "content_score": 0.0,
                "trending_score": 0.0,
                "ai_score": r.score,
                "reasons": [r.reason],
            }

    # Compute weighted final score
    results = []
    for pid, data in score_map.items():
        final_score = (
            data["content_score"]  * content_weight +
            data["trending_score"] * trending_weight +
            data["ai_score"]       * ai_weight
        )
        # Pick the best reason (from AI if available)
        reason = data["reasons"][-1] if data["reasons"] else "Recommended for you"
        results.append(RecommendedProduct(
            product=data["product"],
            score=round(final_score, 4),
            reason=reason,
            strategy="hybrid",
        ))

    results.sort(key=lambda x: x.score, reverse=True)
    return results[:limit]


# ══════════════════════════════════════════════════════════════════════════════
# PUBLIC API — called by endpoints
# ══════════════════════════════════════════════════════════════════════════════

def get_personalized_recommendations(
    user_id: str,
    limit: int = 20,
    use_ai: bool = True,
    force_refresh: bool = False,
) -> RecommendationResponse:
    """
    Main recommendation call. Checks cache first, then runs hybrid engine.
    """
    db        = get_valkey()
    cache_key = f"reco:{user_id}:personalized"

    if not force_refresh:
        cached = db.get(cache_key)
        if cached:
            data = json.loads(cached)
            return RecommendationResponse(**data, from_cache=True)

    if use_ai:
        recs = _hybrid(user_id, limit=limit)
        strategy = "hybrid (content + trending + AI Nemotron)"
    else:
        recs = _content_based(user_id, limit=limit)
        strategy = "content_based"

    response = RecommendationResponse(
        user_id=user_id,
        strategy=strategy,
        products=recs,
        total=len(recs),
        from_cache=False,
    )

    db.setex(cache_key, TTL_PERSONALIZED, response.model_dump_json())
    return response


def get_similar_recommendations(
    product_id: str,
    limit: int = 10,
) -> RecommendationResponse:
    """Products similar to a given product."""
    recs = _similar_products(product_id, limit=limit)
    return RecommendationResponse(
        strategy="content_similarity",
        products=recs,
        total=len(recs),
        from_cache=False,
    )


def get_trending_recommendations(
    period: str = "daily",
    limit: int = 20,
) -> RecommendationResponse:
    """Real-time trending products."""
    db        = get_valkey()
    cache_key = f"reco:trending:{period}"
    cached    = db.get(cache_key)

    if cached:
        data = json.loads(cached)
        return RecommendationResponse(**data, from_cache=True)

    recs = _trending_based(limit=limit)
    response = RecommendationResponse(
        strategy=f"trending_{period}",
        products=recs,
        total=len(recs),
        from_cache=False,
    )
    db.setex(cache_key, TTL_POPULAR, response.model_dump_json())
    return response


def get_popular_recommendations(limit: int = 20) -> RecommendationResponse:
    """Most popular products by rating × review count."""
    db        = get_valkey()
    cache_key = "reco:popular"
    cached    = db.get(cache_key)

    if cached:
        data = json.loads(cached)
        return RecommendationResponse(**data, from_cache=True)

    products = get_top_rated_products(limit * 2)
    # Score by weighted rating
    scored = sorted(
        products,
        key=lambda p: p.rating * min(p.rating_count / 1000, 1.0),
        reverse=True,
    )

    recs = [
        RecommendedProduct(
            product=p,
            score=round(p.rating * min(p.rating_count / 1000, 1.0) / 5.0, 4),
            reason=f"Loved by {p.rating_count:,} shoppers with {p.rating}★ rating",
            strategy="popular",
        )
        for p in scored[:limit]
    ]

    response = RecommendationResponse(
        strategy="popular",
        products=recs,
        total=len(recs),
        from_cache=False,
    )
    db.setex(cache_key, TTL_POPULAR, response.model_dump_json())
    return response


def get_category_recommendations(
    category: str,
    user_id: Optional[str] = None,
    limit: int = 20,
) -> RecommendationResponse:
    """Best products in a category, optionally personalized."""
    products, _ = get_products_by_category(category, per_page=50)

    if user_id:
        interactions = get_user_product_interactions(user_id)
        scored = sorted(
            products,
            key=lambda p: (
                p.rating * 0.5 +
                min(p.discount_pct / 100, 0.3) -
                min(interactions.get(p.id, 0) / 20.0, 0.3)
            ),
            reverse=True,
        )
        reason_suffix = "matching your taste"
    else:
        scored  = sorted(products, key=lambda p: p.rating, reverse=True)
        reason_suffix = "in this category"

    recs = [
        RecommendedProduct(
            product=p,
            score=round(p.rating / 5.0, 4),
            reason=f"Top pick {reason_suffix}",
            strategy="category",
        )
        for p in scored[:limit]
        if p.in_stock and p.is_active
    ]

    return RecommendationResponse(
        user_id=user_id,
        strategy=f"category:{category}",
        products=recs,
        total=len(recs),
        from_cache=False,
    )


def get_new_arrivals(limit: int = 20) -> RecommendationResponse:
    """Newest products sorted by created_at."""
    products, _ = get_all_products(per_page=100)
    sorted_by_date = sorted(
        [p for p in products if p.in_stock and p.is_active],
        key=lambda p: p.created_at,
        reverse=True,
    )

    recs = [
        RecommendedProduct(
            product=p,
            score=round(p.rating / 5.0, 4),
            reason="Newly arrived on ShopMind AI",
            strategy="new_arrivals",
        )
        for p in sorted_by_date[:limit]
    ]

    return RecommendationResponse(
        strategy="new_arrivals",
        products=recs,
        total=len(recs),
        from_cache=False,
    )


def invalidate_user_cache(user_id: str):
    """Call this whenever user behavior changes significantly."""
    db = get_valkey()
    db.delete(f"reco:{user_id}:personalized")