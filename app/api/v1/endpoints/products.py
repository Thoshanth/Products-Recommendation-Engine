from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.models.schemas import ProductCreate, MessageResponse
from app.services import product_service

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("")
def list_products(page: int = Query(1, ge=1), per_page: int = Query(20, ge=1, le=100),
                  in_stock_only: bool = Query(False)):
    products, total = product_service.get_all_products(page, per_page, in_stock_only)
    return {"products": products, "total": total, "page": page,
            "per_page": per_page, "total_pages": -(-total // per_page)}


@router.get("/featured")
def list_featured(limit: int = Query(10, ge=1, le=50)):
    return {"products": product_service.get_featured_products(limit)}


@router.get("/top-rated")
def list_top_rated(limit: int = Query(10, ge=1, le=50)):
    return {"products": product_service.get_top_rated_products(limit)}


@router.get("/search")
def search(
    q: str = Query(..., min_length=1),
    category: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    min_rating: Optional[float] = Query(None, ge=0, le=5),
    in_stock_only: bool = Query(False),
    sort_by: str = Query("relevance", enum=["relevance", "price_asc", "price_desc", "rating", "newest"]),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    products, total = product_service.search_products(
        q, category, min_price, max_price, min_rating, in_stock_only, sort_by, page, per_page)
    return {"query": q, "results": products, "total": total,
            "page": page, "per_page": per_page, "total_pages": -(-total // per_page)}


@router.get("/category/{category}")
def list_by_category(category: str, page: int = Query(1, ge=1), per_page: int = Query(20, ge=1, le=100)):
    products, total = product_service.get_products_by_category(category, page, per_page)
    return {"category": category, "products": products, "total": total,
            "page": page, "per_page": per_page, "total_pages": -(-total // per_page)}


@router.get("/brand/{brand_id}")
def list_by_brand(brand_id: str):
    return {"products": product_service.get_products_by_brand(brand_id)}


@router.get("/{product_id}")
def get_product(product_id: str):
    product = product_service.get_product(product_id)
    if not product: raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.post("", status_code=201)
def create_product(data: ProductCreate):
    return product_service.create_product(data)


@router.delete("/{product_id}", response_model=MessageResponse)
def delete_product(product_id: str):
    ok = product_service.delete_product(product_id)
    if not ok: raise HTTPException(status_code=404, detail="Product not found")
    return MessageResponse(success=True, message="Product deleted")