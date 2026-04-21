from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.core.database import ping_valkey
from app.models.schemas import HealthResponse
from app.api.v1.router import api_router
from app.services.cart_service import seed_coupons
from app.middleware.rate_limiter import RateLimitMiddleware
from app.middleware.cache_middleware import ResponseCacheMiddleware
from app.utils.performance import PerformanceMiddleware

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="""
## 🛒 ShopMind AI — Intelligent Product Recommendation Engine

- 🔐 **JWT Auth** — register, login, refresh, logout
- 👤 **User Management** — profile, addresses, wishlist, loyalty
- 🛍️ **Product Catalog** — search, filter, categories, brands
- 📊 **Behavior Tracking** — events, affinity scores, trending
- 🤖 **AI Recommendations** — Nemotron via OpenRouter (hybrid engine)
- 🛒 **Cart** — add/update, coupons, auto-totals
- 📦 **Orders** — place, track, cancel, timeline
- ⭐ **Reviews** — verified purchase, helpful votes
- ⚡ **Performance** — Valkey caching, rate limiting, slow query tracking
    """,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Middleware stack (order matters — outermost runs first) ────────────────────
app.add_middleware(PerformanceMiddleware)       # 1. Timing (outermost)
app.add_middleware(RateLimitMiddleware)         # 2. Rate limiting
app.add_middleware(ResponseCacheMiddleware)     # 3. Response cache
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.on_event("startup")
def on_startup():
    try:
        seed_coupons()
        print("✅ Coupons seeded")
    except Exception as e:
        print(f"⚠️  Startup warning: {e}")


@app.get("/", tags=["Root"])
def root():
    return {
        "app":     settings.app_name,
        "version": settings.app_version,
        "docs":    "/docs",
        "health":  "/health",
        "stage":   "6 — Caching + Rate Limiting + Performance",
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health():
    ok = ping_valkey()
    return HealthResponse(
        status="healthy" if ok else "degraded",
        valkey_connected=ok,
        app_name=settings.app_name,
        app_version=settings.app_version,
        environment=settings.environment,
    )