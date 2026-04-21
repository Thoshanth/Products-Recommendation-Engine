"""orders.py — Order placement and management endpoints."""
from fastapi import APIRouter, HTTPException, Depends, Query
from app.models.schemas import OrderCreate, MessageResponse
from app.services import order_service
from app.core.dependencies import get_current_user_id
from pydantic import BaseModel

router = APIRouter(prefix="/orders", tags=["Orders"])


class StatusUpdateRequest(BaseModel):
    status:      str
    description: str = ""
    location:    str = ""

class CancelRequest(BaseModel):
    reason: str = ""


@router.post("", status_code=201)
def place_order(data: OrderCreate, user_id: str = Depends(get_current_user_id)):
    """
    Place order from current cart.
    - Validates stock for all items
    - Deducts inventory
    - Awards loyalty points
    - Clears cart on success
    """
    order, error = order_service.create_order(user_id, data)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {
        "success":      True,
        "message":      "Order placed successfully! 🎉",
        "order_number": order.order_number,
        "order":        order,
    }


@router.get("")
def get_my_orders(
    page:     int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    user_id:  str = Depends(get_current_user_id),
):
    """Get paginated order history for current user."""
    orders, total = order_service.get_user_orders(user_id, page, per_page)
    return {
        "orders":      orders,
        "total":       total,
        "page":        page,
        "per_page":    per_page,
        "total_pages": -(-total // per_page),
    }


@router.get("/{order_id}")
def get_order(order_id: str, user_id: str = Depends(get_current_user_id)):
    """Get a specific order with full timeline."""
    order = order_service.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return order


@router.post("/{order_id}/cancel")
def cancel_order(
    order_id: str,
    body:     CancelRequest,
    user_id:  str = Depends(get_current_user_id),
):
    """Cancel an order (only allowed in pending/confirmed status)."""
    order, error = order_service.cancel_order(order_id, user_id, body.reason)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {"success": True, "message": "Order cancelled", "order": order}


@router.patch("/{order_id}/status")
def update_status(order_id: str, body: StatusUpdateRequest):
    """Update order status (admin/internal use). Validates state transitions."""
    order, error = order_service.update_order_status(
        order_id, body.status, body.description, body.location
    )
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {"success": True, "order": order}