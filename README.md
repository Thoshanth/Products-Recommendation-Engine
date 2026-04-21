# 🛒 ShopMind AI — Product Recommendation Engine

> Production-grade AI-powered recommendation engine with Valkey DB, FastAPI, and JWT auth.

---

## 🚀 Quick Start

```bash
# 1. Clone & install
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Edit .env — set ANTHROPIC_API_KEY, SECRET_KEY, etc.

# 3. Start Valkey DB
valkey-server          # or: redis-server (compatible)

# 4. Seed database
python scripts/seed_data.py

# 5. Run API
uvicorn app.main:app --reload

# 6. Open docs
open http://localhost:8000/docs
```

---

## 🗺️ API Endpoints (Stage 2)

### Auth  `/api/v1/auth`
| Method | Path | Description |
|--------|------|-------------|
| POST | `/register` | Create account, receive tokens |
| POST | `/login` | Login, receive tokens |
| POST | `/refresh` | Rotate access token |
| POST | `/logout` | Invalidate refresh token |
| POST | `/change-password` | Change password (auth required) |

### Users  `/api/v1/users`
| Method | Path | Description |
|--------|------|-------------|
| GET | `/me` | Get my profile + addresses |
| PATCH | `/me` | Update profile |
| DELETE | `/me` | Deactivate account |
| GET | `/me/addresses` | List addresses |
| POST | `/me/addresses` | Add new address |
| DELETE | `/me/addresses/{id}` | Remove address |
| PATCH | `/me/addresses/{id}/default` | Set default address |
| GET | `/me/wishlist` | Get wishlist |
| POST | `/me/wishlist/{product_id}` | Add to wishlist |
| DELETE | `/me/wishlist/{product_id}` | Remove from wishlist |
| GET | `/me/loyalty` | Loyalty points + tier info |
| GET | `/me/stats` | Dashboard stats |

### Products  `/api/v1/products`
| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | List all products (paginated) |
| GET | `/featured` | Featured products |
| GET | `/top-rated` | Top-rated products |
| GET | `/search?q=...` | Full-text search + filters |
| GET | `/category/{cat}` | Filter by category |
| GET | `/brand/{brand_id}` | Filter by brand |
| GET | `/{product_id}` | Single product detail |
| POST | `/` | Create product |
| DELETE | `/{product_id}` | Delete product |

---

## 🗃️ Valkey Key Schema

```
# Products
product:{id}               → Hash   (all product fields)
products:all               → Set    (all product IDs)
products:category:{cat}    → Set    (IDs by category)
products:brand:{brand_id}  → Set    (IDs by brand)
products:by_rating         → ZSet   (score = rating)
products:by_price          → ZSet   (score = price)
products:featured          → Set    (featured IDs)

# Users
user:{id}                  → Hash   (all user fields + password_hash)
user:email:{email}         → String (email → user ID lookup)
users:all                  → Set    (all user IDs)
user:{id}:addresses        → List   (JSON address objects)
user:{id}:wishlist         → List   (JSON wishlist items)

# Sessions
session:refresh:{token}    → String (→ user_id, TTL = 7 days)

# Brands
brand:{id}                 → Hash   (brand fields)
brands:all                 → Set    (all brand IDs)
```

---

## 📦 Stages

| Stage | Status | Description |
|-------|--------|-------------|
| 1 | ✅ Done | Project setup, rich models, Valkey connection, seed data |
| 2 | ✅ Done | JWT Auth, User management, Products API |
| 3 | 🔜 Next | Behavior tracking & analytics |
| 4 | 🔜 | AI recommendation engine (Claude embeddings) |
| 5 | 🔜 | Recommendation API endpoints |
| 6 | 🔜 | Cart, Orders, Reviews API |
| 7 | 🔜 | Caching, rate limiting, performance |
| 8 | 🔜 | Testing & documentation |
| 9 | 🔜 | React frontend |
| 10 | 🔜 | Docker + deployment |

---

## 🛠️ Tech Stack
- **FastAPI** — REST API framework
- **Valkey DB** — Primary data store + cache
- **JWT** — Stateless auth (access + refresh tokens)
- **Pydantic v2** — Data validation
- **Anthropic Claude** — AI embeddings (Stage 4)
- **Python 3.11+**
