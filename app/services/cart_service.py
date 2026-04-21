"""
cart_service.py — Full cart management in Valkey.

Key Schema:
  cart:{user_id}          → Hash  (cart metadata)
  cart:{user_id}:items    → List  (JSON CartItem objects)
  coupon:{code}           → Hash  (coupon details)
"""

import json
from datetime import datetime
from typing import Optional
from app.core.database import get_valkey
from app.services.product_service import get_product
from app.models.schemas import Cart, CartItem, AddToCart

# ── Shipping thresholds ────────────────────────────────────────────────────────
FREE_SHIPPING_THRESHOLD = 499.0
STANDARD_SHIPPING_FEE   = 49.0
EXPRESS_SHIPPING_FEE    = 99.0

# ── Tax rate ───────────────────────────────────────────────────────────────────
GST_RATE = 0.18   # 18% GST included in selling_price (display only)


def _cart_key(uid):       return f"cart:{uid}"
def _items_key(uid):      return f"cart:{uid}:items"
def _coupon_key(code):    return f"coupon:{code.upper()}"


# ── Helpers ────────────────────────────────────────────────────────────────────

def _load_items(uid: str) -> list[CartItem]:
    db = get_valkey()
    raw = db.lrange(_items_key(uid), 0, -1)
    items = []
    for r in raw:
        try:
            items.append(CartItem(**json.loads(r)))
        except Exception:
            continue
    return items


def _save_items(uid: str, items: list[CartItem]):
    db = get_valkey()
    db.delete(_items_key(uid))
    for item in items:
        db.rpush(_items_key(uid), item.model_dump_json())


def _compute_totals(items: list[CartItem], coupon_discount: float = 0.0, shipping_method: str = "standard") -> dict:
    total_mrp      = sum(i.mrp * i.quantity for i in items)
    total_selling  = sum(i.selling_price * i.quantity for i in items)
    total_discount = total_mrp - total_selling

    if shipping_method == "express":
        delivery_charge = EXPRESS_SHIPPING_FEE
    elif total_selling >= FREE_SHIPPING_THRESHOLD:
        delivery_charge = 0.0
    else:
        delivery_charge = STANDARD_SHIPPING_FEE

    total_amount = total_selling - coupon_discount + delivery_charge

    return {
        "total_mrp":       round(total_mrp, 2),
        "total_discount":  round(total_discount, 2),
        "delivery_charge": round(delivery_charge, 2),
        "coupon_discount": round(coupon_discount, 2),
        "total_amount":    round(max(total_amount, 0), 2),
        "item_count":      sum(i.quantity for i in items),
    }


def _get_coupon(code: str) -> Optional[dict]:
    db  = get_valkey()
    raw = db.hgetall(_coupon_key(code))
    return raw if raw else None


# ── Seed coupons (call once) ───────────────────────────────────────────────────

def seed_coupons():
    db = get_valkey()
    coupons = [
        {"code": "WELCOME10", "discount_type": "percentage", "discount_value": "10",
         "min_order": "0",    "description": "10% off your first order", "is_active": "True"},
        {"code": "FLAT200",   "discount_type": "flat",       "discount_value": "200",
         "min_order": "999",  "description": "₹200 off on orders above ₹999", "is_active": "True"},
        {"code": "SAVE500",   "discount_type": "flat",       "discount_value": "500",
         "min_order": "2999", "description": "₹500 off on orders above ₹2999", "is_active": "True"},
        {"code": "HDFC10",    "discount_type": "percentage", "discount_value": "10",
         "min_order": "0",    "description": "10% off with HDFC Bank Card", "is_active": "True"},
        {"code": "PREMIUM15", "discount_type": "percentage", "discount_value": "15",
         "min_order": "1999", "description": "15% off for Premium members", "is_active": "True"},
    ]
    for c in coupons:
        db.hset(_coupon_key(c["code"]), mapping=c)


# ── CRUD ───────────────────────────────────────────────────────────────────────

def get_cart(user_id: str) -> Cart:
    db    = get_valkey()
    items = _load_items(user_id)
    meta  = db.hgetall(_cart_key(user_id))

    coupon_code     = meta.get("coupon_code", "") or None
    coupon_discount = float(meta.get("coupon_discount", 0))
    shipping_method = meta.get("shipping_method", "standard")

    totals = _compute_totals(items, coupon_discount, shipping_method)

    return Cart(
        user_id=user_id,
        items=items,
        coupon_code=coupon_code,
        **totals,
        updated_at=meta.get("updated_at", datetime.utcnow().isoformat()),
    )


def add_to_cart(user_id: str, data: AddToCart) -> tuple[Cart, str]:
    """Add or increment item. Returns (cart, error)."""
    product = get_product(data.product_id)
    if not product:
        return None, "Product not found"
    if not product.in_stock:
        return None, "Product is out of stock"
    if product.stock_quantity < data.quantity:
        return None, f"Only {product.stock_quantity} units available"

    items = _load_items(user_id)

    # Check if same product+size+color already in cart
    existing_idx = None
    for i, item in enumerate(items):
        if (item.product_id    == data.product_id and
            item.selected_size  == data.selected_size and
            item.selected_color == data.selected_color):
            existing_idx = i
            break

    if existing_idx is not None:
        # Increment quantity
        items[existing_idx].quantity += data.quantity
        items[existing_idx].subtotal  = round(
            items[existing_idx].selling_price * items[existing_idx].quantity, 2
        )
    else:
        new_item = CartItem(
            product_id=product.id,
            product_name=product.name,
            thumbnail_url=product.thumbnail_url,
            selling_price=product.selling_price,
            mrp=product.mrp,
            quantity=data.quantity,
            selected_size=data.selected_size,
            selected_color=data.selected_color,
            subtotal=round(product.selling_price * data.quantity, 2),
        )
        items.append(new_item)

    _save_items(user_id, items)
    _update_meta(user_id)
    return get_cart(user_id), ""


def update_quantity(user_id: str, product_id: str, quantity: int,
                    size: Optional[str] = None, color: Optional[str] = None) -> tuple[Cart, str]:
    if quantity < 1:
        return remove_from_cart(user_id, product_id, size, color), ""

    items = _load_items(user_id)
    found = False
    for item in items:
        if (item.product_id == product_id and
            item.selected_size == size and item.selected_color == color):
            product = get_product(product_id)
            if product and quantity > product.stock_quantity:
                return None, f"Only {product.stock_quantity} units available"
            item.quantity = quantity
            item.subtotal = round(item.selling_price * quantity, 2)
            found = True
            break

    if not found:
        return None, "Item not found in cart"

    _save_items(user_id, items)
    _update_meta(user_id)
    return get_cart(user_id), ""


def remove_from_cart(user_id: str, product_id: str,
                     size: Optional[str] = None, color: Optional[str] = None) -> Cart:
    items    = _load_items(user_id)
    new_items = [
        i for i in items
        if not (i.product_id == product_id and
                i.selected_size == size and i.selected_color == color)
    ]
    _save_items(user_id, new_items)
    _update_meta(user_id)
    return get_cart(user_id)


def clear_cart(user_id: str):
    db = get_valkey()
    db.delete(_items_key(user_id))
    db.delete(_cart_key(user_id))


def apply_coupon(user_id: str, code: str) -> tuple[Cart, str]:
    coupon = _get_coupon(code)
    if not coupon:
        return None, "Invalid coupon code"
    if coupon.get("is_active") != "True":
        return None, "This coupon has expired"

    cart   = get_cart(user_id)
    min_order = float(coupon.get("min_order", 0))
    if cart.total_amount < min_order:
        return None, f"Minimum order value ₹{min_order:,.0f} required for this coupon"

    discount_type  = coupon.get("discount_type")
    discount_value = float(coupon.get("discount_value", 0))

    if discount_type == "percentage":
        coupon_discount = round(cart.total_amount * discount_value / 100, 2)
    else:
        coupon_discount = min(discount_value, cart.total_amount)

    db = get_valkey()
    db.hset(_cart_key(user_id), mapping={
        "coupon_code":     code.upper(),
        "coupon_discount": str(coupon_discount),
        "updated_at":      datetime.utcnow().isoformat(),
    })
    return get_cart(user_id), ""


def remove_coupon(user_id: str) -> Cart:
    db = get_valkey()
    db.hset(_cart_key(user_id), mapping={
        "coupon_code": "", "coupon_discount": "0",
        "updated_at": datetime.utcnow().isoformat(),
    })
    return get_cart(user_id)


def _update_meta(user_id: str):
    db = get_valkey()
    db.hset(_cart_key(user_id), mapping={"updated_at": datetime.utcnow().isoformat()})