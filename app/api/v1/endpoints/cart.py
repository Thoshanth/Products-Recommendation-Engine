"""cart.py — Cart management endpoints."""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from app.models.schemas import AddToCart, MessageResponse
from app.services import cart_service
from app.core.dependencies import get_current_user_id
from pydantic import BaseModel

router = APIRouter(prefix="/cart", tags=["Cart"])


class UpdateQuantityRequest(BaseModel):
    quantity:       int
    selected_size:  Optional[str] = None
    selected_color: Optional[str] = None

class CouponRequest(BaseModel):
    code: str


@router.get("")
def get_cart(user_id: str = Depends(get_current_user_id)):
    """Get current user's cart with computed totals."""
    return cart_service.get_cart(user_id)


@router.post("/items", status_code=201)
def add_to_cart(data: AddToCart, user_id: str = Depends(get_current_user_id)):
    """Add a product to cart. If already present, increments quantity."""
    cart, error = cart_service.add_to_cart(user_id, data)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {"success": True, "cart": cart}


@router.patch("/items/{product_id}")
def update_quantity(
    product_id: str,
    body:       UpdateQuantityRequest,
    user_id:    str = Depends(get_current_user_id),
):
    """Update quantity of a cart item. Set quantity=0 to remove."""
    cart, error = cart_service.update_quantity(
        user_id, product_id, body.quantity, body.selected_size, body.selected_color
    )
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {"success": True, "cart": cart}


@router.delete("/items/{product_id}", )
def remove_from_cart(
    product_id:     str,
    selected_size:  Optional[str] = Query(None),
    selected_color: Optional[str] = Query(None),
    user_id:        str = Depends(get_current_user_id),
):
    """Remove a specific item from cart."""
    cart = cart_service.remove_from_cart(user_id, product_id, selected_size, selected_color)
    return {"success": True, "cart": cart}


@router.delete("", response_model=MessageResponse)
def clear_cart(user_id: str = Depends(get_current_user_id)):
    """Clear entire cart."""
    cart_service.clear_cart(user_id)
    return MessageResponse(success=True, message="Cart cleared")


@router.post("/coupon")
def apply_coupon(body: CouponRequest, user_id: str = Depends(get_current_user_id)):
    """Apply a coupon code to the cart."""
    cart, error = cart_service.apply_coupon(user_id, body.code)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {"success": True, "cart": cart, "message": f"Coupon '{body.code}' applied!"}


@router.delete("/coupon", )
def remove_coupon(user_id: str = Depends(get_current_user_id)):
    """Remove applied coupon."""
    cart = cart_service.remove_coupon(user_id)
    return {"success": True, "cart": cart, "message": "Coupon removed"}