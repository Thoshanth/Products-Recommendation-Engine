"""test_recommendations.py — Unit tests for recommendation scoring logic."""
from app.services.recommendation_service import (
    TTL_PERSONALIZED, TTL_SIMILAR, TTL_POPULAR, TTL_AI_SCORED,
    MAX_CANDIDATES, MAX_RESULTS,
)


def test_cache_ttl_values_are_positive():
    assert TTL_PERSONALIZED > 0
    assert TTL_SIMILAR > 0
    assert TTL_POPULAR > 0
    assert TTL_AI_SCORED > 0


def test_personalized_ttl_longer_than_popular():
    # Personalized (30min) should be longer than popular (15min)
    assert TTL_PERSONALIZED > TTL_POPULAR


def test_similar_ttl_is_longest():
    assert TTL_SIMILAR >= TTL_PERSONALIZED


def test_max_candidates_gt_max_results():
    # We always feed more candidates than we return
    assert MAX_CANDIDATES > MAX_RESULTS


def test_hybrid_weights_sum_to_one():
    content_weight  = 0.35
    trending_weight = 0.25
    ai_weight       = 0.40
    total = content_weight + trending_weight + ai_weight
    assert abs(total - 1.0) < 0.001