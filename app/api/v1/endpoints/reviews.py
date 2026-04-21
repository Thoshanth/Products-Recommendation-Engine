"""reviews.py — Product review endpoints."""
from fastapi import APIRouter, HTTPException, Depends, Query
from app.models.schemas import ReviewCreate, MessageResponse
from app.services import review_service
from app.services.user_service import get_user
from app.core.dependencies import get_current_user_id
from pydantic import BaseModel

router = APIRouter(prefix="/reviews", tags=["Reviews"])


class HelpfulVoteRequest(BaseModel):
    is_helpful: bool


@router.post("", status_code=201)
def create_review(data: ReviewCreate, user_id: str = Depends(get_current_user_id)):
    """
    Submit a product review.
    Automatically checks for verified purchase badge.
    One review per user per product.
    """
    user = get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    review, error = review_service.create_review(user_id, user.name, data)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {"success": True, "review": review}


@router.get("/product/{product_id}")
def get_product_reviews(
    product_id: str,
    page:       int = Query(1, ge=1),
    per_page:   int = Query(10, ge=1, le=50),
    sort_by:    str = Query("newest", enum=["newest", "highest_rating", "lowest_rating", "most_helpful"]),
):
    """Get paginated reviews for a product."""
    reviews, total = review_service.get_product_reviews(product_id, page, per_page, sort_by)
    return {
        "product_id":  product_id,
        "reviews":     reviews,
        "total":       total,
        "page":        page,
        "per_page":    per_page,
        "total_pages": -(-total // per_page),
    }


@router.get("/me")
def get_my_reviews(user_id: str = Depends(get_current_user_id)):
    """All reviews submitted by the current user."""
    return {"reviews": review_service.get_user_reviews(user_id)}


@router.post("/{review_id}/helpful")
def vote_helpful(
    review_id: str,
    body:      HelpfulVoteRequest,
    user_id:   str = Depends(get_current_user_id),
):
    """Vote a review as helpful or not helpful. One vote per user per review per 30 days."""
    ok, msg = review_service.vote_helpful(review_id, user_id, body.is_helpful)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return MessageResponse(success=True, message=msg)


@router.delete("/{review_id}", response_model=MessageResponse)
def delete_review(review_id: str, user_id: str = Depends(get_current_user_id)):
    """Delete your own review."""
    ok, msg = review_service.delete_review(review_id, user_id)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return MessageResponse(success=True, message=msg)