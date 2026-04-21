"""
order_service.py — Order creation, management, timeline tracking.

Key Schema:
  order:{id}              → Hash  (order fields)
  orders:all              → Set   (all order IDs)
  orders:user:{user_id}   → List  (user's order IDs, newest first)
  orders:status:{status}  → Set   (order IDs by status)
  order_counter           → String (auto-increment for order numbers)
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Optional
from app.core.database import get_valkey
from app.services.cart_service import get_cart, clear_cart
from app.services.user_service import get_user, get_addresses, add_loyalty_points
from app.services.product_service import get_product, update_stock
from app.models.schemas import (
    Order, OrderItem, OrderCreate, OrderTimeline,
    Address, Cart,
)

LOYALTY_POINTS_RATE = 1   # 1 point per ₹100 spent


def _key(oid):      return f"order:{oid}"
def _user_key(uid): return f"orders:user:{uid}"


def _next_order_number() -> str:
    db  = get_valkey()
    num = db.incr("order_counter")
    return f"ORD-{datetime.utcnow().year}-{str(num).zfill(6)}"


def _serialize_order(o: Order) -> dict:
    return {
        "id":                   o.id,
        "order_number":         o.order_number,
        "user_id":              o.user_id,
        "items":                json.dumps([i.model_dump() for i in o.items]),
        "total_mrp":            str(o.total_mrp),
        "total_discount":       str(o.total_discount),
        "delivery_charge":      str(o.delivery_charge),
        "coupon_discount":      str(o.coupon_discount),
        "tax_amount":           str(o.tax_amount),
        "total_amount":         str(o.total_amount),
        "currency":             o.currency,
        "shipping_address":     o.shipping_address.model_dump_json(),
        "shipping_method":      o.shipping_method,
        "estimated_delivery":   o.estimated_delivery or "",
        "tracking_id":          o.tracking_id or "",
        "tracking_url":         o.tracking_url or "",
        "payment_method":       o.payment_method,
        "payment_status":       o.payment_status,
        "transaction_id":       o.transaction_id or "",
        "status":               o.status,
        "timeline":             json.dumps([t.model_dump() for t in o.timeline]),
        "notes":                o.notes or "",
        "cancellation_reason":  o.cancellation_reason or "",
        "created_at":           o.created_at,
        "updated_at":           o.updated_at,
        "delivered_at":         o.delivered_at or "",
    }


def _deserialize_order(raw: dict) -> Order:
    return Order(
        id=raw["id"],
        order_number=raw["order_number"],
        user_id=raw["user_id"],
        items=[OrderItem(**i) for i in json.loads(raw.get("items", "[]"))],
        total_mrp=float(raw.get("total_mrp", 0)),
        total_discount=float(raw.get("total_discount", 0)),
        delivery_charge=float(raw.get("delivery_charge", 0)),
        coupon_discount=float(raw.get("coupon_discount", 0)),
        tax_amount=float(raw.get("tax_amount", 0)),
        total_amount=float(raw.get("total_amount", 0)),
        currency=raw.get("currency", "INR"),
        shipping_address=Address(**json.loads(raw["shipping_address"])),
        shipping_method=raw.get("shipping_method", "standard"),
        estimated_delivery=raw.get("estimated_delivery") or None,
        tracking_id=raw.get("tracking_id") or None,
        tracking_url=raw.get("tracking_url") or None,
        payment_method=raw.get("payment_method", ""),
        payment_status=raw.get("payment_status", "pending"),
        transaction_id=raw.get("transaction_id") or None,
        status=raw.get("status", "pending"),
        timeline=[OrderTimeline(**t) for t in json.loads(raw.get("timeline", "[]"))],
        notes=raw.get("notes") or None,
        cancellation_reason=raw.get("cancellation_reason") or None,
        created_at=raw.get("created_at", datetime.utcnow().isoformat()),
        updated_at=raw.get("updated_at", datetime.utcnow().isoformat()),
        delivered_at=raw.get("delivered_at") or None,
    )


# ── Create Order ───────────────────────────────────────────────────────────────

def create_order(user_id: str, data: OrderCreate) -> tuple[Optional[Order], str]:
    """
    Convert cart → order.
    Validates stock, deducts inventory, awards loyalty points.
    """
    db   = get_valkey()
    cart = get_cart(user_id)

    if not cart.items:
        return None, "Cart is empty"

    # Validate shipping address
    addresses = get_addresses(user_id)
    address   = next((a for a in addresses if a.id == data.shipping_address_id), None)
    if not address:
        return None, "Shipping address not found"

    # Validate stock for all items
    for item in cart.items:
        product = get_product(item.product_id)
        if not product:
            return None, f"Product '{item.product_name}' no longer available"
        if not product.in_stock or product.stock_quantity < item.quantity:
            return None, f"Insufficient stock for '{item.product_name}'"

    # Build order items
    order_items = [
        OrderItem(
            product_id=item.product_id,
            product_name=item.product_name,
            brand_name=get_product(item.product_id).brand_name,
            thumbnail_url=item.thumbnail_url,
            sku=get_product(item.product_id).sku,
            quantity=item.quantity,
            mrp=item.mrp,
            selling_price=item.selling_price,
            subtotal=item.subtotal,
            selected_size=item.selected_size,
            selected_color=item.selected_color,
        )
        for item in cart.items
    ]

    # Estimated delivery
    delivery_days = {"standard": 5, "express": 2, "overnight": 1, "pickup": 0}
    days          = delivery_days.get(data.shipping_method, 5)
    est_delivery  = (datetime.utcnow() + timedelta(days=days)).strftime("%Y-%m-%d")

    now = datetime.utcnow().isoformat()
    oid = f"ord-{str(uuid.uuid4())[:8]}"

    initial_timeline = [
        OrderTimeline(
            status="pending",
            timestamp=now,
            description="Order placed successfully. Awaiting confirmation.",
        )
    ]

    order = Order(
        id=oid,
        order_number=_next_order_number(),
        user_id=user_id,
        items=order_items,
        total_mrp=cart.total_mrp,
        total_discount=cart.total_discount,
        delivery_charge=cart.delivery_charge,
        coupon_discount=cart.coupon_discount,
        total_amount=cart.total_amount,
        shipping_address=address,
        shipping_method=data.shipping_method,
        estimated_delivery=est_delivery,
        payment_method=data.payment_method,
        payment_status="paid" if data.payment_method != "cash_on_delivery" else "pending",
        status="confirmed",
        timeline=initial_timeline,
        notes=data.notes,
        created_at=now,
        updated_at=now,
    )

    # Persist
    db.hset(_key(oid), mapping=_serialize_order(order))
    db.sadd("orders:all", oid)
    db.lpush(_user_key(user_id), oid)
    db.sadd(f"orders:status:confirmed", oid)

    # Deduct stock
    for item in cart.items:
        product = get_product(item.product_id)
        if product:
            update_stock(item.product_id, max(0, product.stock_quantity - item.quantity))

    # Award loyalty points (1 per ₹100)
    points = int(cart.total_amount / 100) * LOYALTY_POINTS_RATE
    if points > 0:
        add_loyalty_points(user_id, points)

    # Update user stats
    _update_user_order_stats(user_id, cart.total_amount)

    # Clear cart
    clear_cart(user_id)

    return order, ""


def _update_user_order_stats(user_id: str, amount: float):
    db  = get_valkey()
    raw = db.hgetall(f"user:{user_id}")
    if not raw:
        return
    total_orders = int(raw.get("total_orders", 0)) + 1
    total_spent  = float(raw.get("total_spent", 0)) + amount
    avg          = round(total_spent / total_orders, 2)
    db.hset(f"user:{user_id}", mapping={
        "total_orders":    str(total_orders),
        "total_spent":     str(total_spent),
        "avg_order_value": str(avg),
        "updated_at":      datetime.utcnow().isoformat(),
    })


# ── Read ───────────────────────────────────────────────────────────────────────

def get_order(order_id: str) -> Optional[Order]:
    db  = get_valkey()
    raw = db.hgetall(_key(order_id))
    return _deserialize_order(raw) if raw else None


def get_user_orders(user_id: str, page: int = 1, per_page: int = 10) -> tuple[list[Order], int]:
    db      = get_valkey()
    all_ids = db.lrange(_user_key(user_id), 0, -1)
    total   = len(all_ids)
    start   = (page - 1) * per_page
    page_ids = all_ids[start:start + per_page]
    orders  = [o for oid in page_ids if (o := get_order(oid))]
    return orders, total


# ── Status Updates ─────────────────────────────────────────────────────────────

def update_order_status(order_id: str, new_status: str, description: str = "",
                         location: str = "") -> tuple[Optional[Order], str]:
    db    = get_valkey()
    order = get_order(order_id)
    if not order:
        return None, "Order not found"

    valid_transitions = {
        "pending":          ["confirmed", "cancelled"],
        "confirmed":        ["processing", "cancelled"],
        "processing":       ["shipped",    "cancelled"],
        "shipped":          ["out_for_delivery"],
        "out_for_delivery": ["delivered",  "returned"],
        "delivered":        ["returned"],
        "cancelled":        [],
        "returned":         ["refunded"],
        "refunded":         [],
    }

    allowed = valid_transitions.get(order.status, [])
    if new_status not in allowed:
        return None, f"Cannot transition from '{order.status}' to '{new_status}'"

    now = datetime.utcnow().isoformat()
    default_descriptions = {
        "confirmed":        "Order confirmed. Payment received.",
        "processing":       "Order is being packed at our warehouse.",
        "shipped":          "Order has been handed to courier partner.",
        "out_for_delivery": "Out for delivery. Expect it today!",
        "delivered":        "Order delivered successfully.",
        "cancelled":        "Order has been cancelled.",
        "returned":         "Return request initiated.",
        "refunded":         "Refund processed to original payment method.",
    }

    timeline_entry = OrderTimeline(
        status=new_status,
        timestamp=now,
        description=description or default_descriptions.get(new_status, ""),
        location=location or None,
    )

    order.timeline.append(timeline_entry)
    order.status     = new_status
    order.updated_at = now

    if new_status == "delivered":
        order.delivered_at    = now
        order.payment_status  = "paid"

    # Update Valkey
    db.srem(f"orders:status:{order.status}", order_id)
    db.hset(_key(order_id), mapping=_serialize_order(order))
    db.sadd(f"orders:status:{new_status}", order_id)

    return order, ""


def cancel_order(order_id: str, user_id: str, reason: str = "") -> tuple[Optional[Order], str]:
    order = get_order(order_id)
    if not order:
        return None, "Order not found"
    if order.user_id != user_id:
        return None, "Unauthorized"
    if order.status not in ["pending", "confirmed"]:
        return None, f"Cannot cancel order in '{order.status}' status"

    # Restore stock
    for item in order.items:
        product = get_product(item.product_id)
        if product:
            update_stock(item.product_id, product.stock_quantity + item.quantity)

    order, err = update_order_status(order_id, "cancelled", reason or "Cancelled by customer")
    if err:
        return None, err

    db = get_valkey()
    db.hset(_key(order_id), mapping={"cancellation_reason": reason, "updated_at": datetime.utcnow().isoformat()})
    return get_order(order_id), ""