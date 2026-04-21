from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth, users, products, behavior,
    recommendations, cart, orders, reviews, admin,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(products.router)
api_router.include_router(behavior.router)
api_router.include_router(recommendations.router)
api_router.include_router(cart.router)
api_router.include_router(orders.router)
api_router.include_router(reviews.router)
api_router.include_router(admin.router)