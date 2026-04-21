"""
test_behavior.py — Unit tests for behavior scoring logic (no live DB needed).
"""
from app.services.behavior_service import EVENT_WEIGHTS, TRENDING_WEIGHTS
from app.models.schemas import BehaviorEventType


def test_purchase_has_highest_affinity_weight():
    assert EVENT_WEIGHTS[BehaviorEventType.PURCHASE] == 10.0

def test_return_has_negative_weight():
    assert EVENT_WEIGHTS[BehaviorEventType.RETURN] < 0

def test_remove_cart_has_negative_weight():
    assert EVENT_WEIGHTS[BehaviorEventType.REMOVE_CART] < 0

def test_purchase_has_highest_trending_weight():
    assert TRENDING_WEIGHTS[BehaviorEventType.PURCHASE] == max(TRENDING_WEIGHTS.values())

def test_all_trending_weights_positive():
    assert all(v > 0 for v in TRENDING_WEIGHTS.values())

def test_event_weights_cover_all_types():
    tracked = set(EVENT_WEIGHTS.keys())
    all_types = set(BehaviorEventType)
    assert tracked == all_types