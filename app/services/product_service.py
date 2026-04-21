import json, uuid
from typing import List, Optional
from datetime import datetime
from app.core.database import get_valkey
from app.models.schemas import Product, ProductCreate, ProductSpecification, ProductImage, Offer

def _key(pid): return f"product:{pid}"

def _serialize(p: Product) -> dict:
    cat  = p.category  if isinstance(p.category,  str) else p.category.value
    cond = p.condition if isinstance(p.condition, str) else p.condition.value
    disc = round((p.mrp - p.selling_price) / p.mrp * 100, 1) if p.mrp > 0 else 0
    return {
        "id": p.id, "name": p.name, "slug": p.slug,
        "description": p.description, "short_description": p.short_description,
        "brand_id": p.brand_id, "brand_name": p.brand_name,
        "category": cat, "sub_category": p.sub_category or "",
        "condition": cond, "mrp": str(p.mrp), "selling_price": str(p.selling_price),
        "discount_pct": str(disc), "currency": p.currency,
        "thumbnail_url": p.thumbnail_url or "", "video_url": p.video_url or "",
        "tags": json.dumps(p.tags), "color": p.color or "",
        "size_options": json.dumps(p.size_options), "sku": p.sku,
        "model_number": p.model_number or "", "rating": str(p.rating),
        "rating_count": str(p.rating_count),
        "rating_breakdown": json.dumps(p.rating_breakdown),
        "in_stock": str(p.in_stock), "stock_quantity": str(p.stock_quantity),
        "free_shipping": str(p.free_shipping), "shipping_days": str(p.shipping_days),
        "shipping_methods": json.dumps(p.shipping_methods),
        "badges": json.dumps(p.badges), "is_featured": str(p.is_featured),
        "is_active": str(p.is_active),
        "specifications": json.dumps([s.model_dump() for s in p.specifications]),
        "images": json.dumps([i.model_dump() for i in p.images]),
        "offers": json.dumps([o.model_dump() for o in p.offers]),
        "embedding_id": p.embedding_id or "",
        "created_at": p.created_at, "updated_at": p.updated_at,
    }

def _deserialize(raw: dict) -> Product:
    return Product(
        id=raw["id"], name=raw["name"], slug=raw.get("slug", ""),
        description=raw.get("description", ""), short_description=raw.get("short_description", ""),
        brand_id=raw.get("brand_id", ""), brand_name=raw.get("brand_name", ""),
        category=raw.get("category", "electronics"), sub_category=raw.get("sub_category") or None,
        condition=raw.get("condition", "new"), mrp=float(raw.get("mrp", 0)),
        selling_price=float(raw.get("selling_price", 0)), discount_pct=float(raw.get("discount_pct", 0)),
        currency=raw.get("currency", "INR"), thumbnail_url=raw.get("thumbnail_url") or None,
        video_url=raw.get("video_url") or None, tags=json.loads(raw.get("tags", "[]")),
        color=raw.get("color") or None, size_options=json.loads(raw.get("size_options", "[]")),
        sku=raw.get("sku", ""), model_number=raw.get("model_number") or None,
        rating=float(raw.get("rating", 0)), rating_count=int(raw.get("rating_count", 0)),
        rating_breakdown=json.loads(raw.get("rating_breakdown", '{"5":0,"4":0,"3":0,"2":0,"1":0}')),
        in_stock=raw.get("in_stock", "True") == "True",
        stock_quantity=int(raw.get("stock_quantity", 0)),
        free_shipping=raw.get("free_shipping", "False") == "True",
        shipping_days=int(raw.get("shipping_days", 5)),
        shipping_methods=json.loads(raw.get("shipping_methods", '["standard"]')),
        badges=json.loads(raw.get("badges", "[]")),
        is_featured=raw.get("is_featured", "False") == "True",
        is_active=raw.get("is_active", "True") == "True",
        specifications=[ProductSpecification(**s) for s in json.loads(raw.get("specifications", "[]"))],
        images=[ProductImage(**i) for i in json.loads(raw.get("images", "[]"))],
        offers=[Offer(**o) for o in json.loads(raw.get("offers", "[]"))],
        embedding_id=raw.get("embedding_id") or None,
        created_at=raw.get("created_at", datetime.utcnow().isoformat()),
        updated_at=raw.get("updated_at", datetime.utcnow().isoformat()),
    )

def create_product(data: ProductCreate) -> Product:
    db = get_valkey()
    pid  = f"prod-{str(uuid.uuid4())[:8]}"
    slug = data.name.lower().replace(" ", "-").replace("/", "-")
    product = Product(id=pid, slug=slug, discount_pct=0, **data.model_dump())
    db.hset(_key(pid), mapping=_serialize(product))
    db.sadd("products:all", pid)
    db.sadd(f"products:category:{product.category}", pid)
    db.sadd(f"products:brand:{product.brand_id}", pid)
    db.zadd("products:by_rating", {pid: product.rating})
    db.zadd("products:by_price",  {pid: product.selling_price})
    if product.is_featured:
        db.sadd("products:featured", pid)
    return product

def get_product(pid: str) -> Optional[Product]:
    db  = get_valkey()
    raw = db.hgetall(_key(pid))
    return _deserialize(raw) if raw else None

def get_all_products(page=1, per_page=20, in_stock_only=False):
    db  = get_valkey()
    ids = list(db.smembers("products:all"))
    products = []
    for pid in ids:
        p = get_product(pid)
        if p and p.is_active:
            if in_stock_only and not p.in_stock: continue
            products.append(p)
    total = len(products)
    start = (page - 1) * per_page
    return products[start:start + per_page], total

def get_products_by_category(category: str, page=1, per_page=20):
    db  = get_valkey()
    ids = list(db.smembers(f"products:category:{category}"))
    products = [p for pid in ids if (p := get_product(pid)) and p.is_active]
    total = len(products)
    start = (page - 1) * per_page
    return products[start:start + per_page], total

def get_featured_products(limit=10):
    db  = get_valkey()
    ids = list(db.smembers("products:featured"))
    return [p for pid in ids if (p := get_product(pid)) and p.is_active][:limit]

def get_top_rated_products(limit=10):
    db  = get_valkey()
    ids = db.zrevrange("products:by_rating", 0, limit - 1)
    return [p for pid in ids if (p := get_product(pid)) and p.is_active]

def get_products_by_brand(brand_id: str):
    db  = get_valkey()
    ids = list(db.smembers(f"products:brand:{brand_id}"))
    return [p for pid in ids if (p := get_product(pid)) and p.is_active]

def search_products(query, category=None, min_price=None, max_price=None,
                    min_rating=None, in_stock_only=False, sort_by="relevance", page=1, per_page=20):
    db  = get_valkey()
    q   = query.lower()
    ids = list(db.smembers(f"products:category:{category}")) if category else list(db.smembers("products:all"))
    results = []
    for pid in ids:
        p = get_product(pid)
        if not p or not p.is_active: continue
        searchable = f"{p.name} {p.description} {' '.join(p.tags)} {p.brand_name}".lower()
        if q not in searchable: continue
        if min_price   and p.selling_price < min_price:  continue
        if max_price   and p.selling_price > max_price:  continue
        if min_rating  and p.rating        < min_rating: continue
        if in_stock_only and not p.in_stock:             continue
        results.append(p)
    if sort_by == "price_asc":  results.sort(key=lambda x: x.selling_price)
    elif sort_by == "price_desc": results.sort(key=lambda x: x.selling_price, reverse=True)
    elif sort_by == "rating":   results.sort(key=lambda x: x.rating, reverse=True)
    elif sort_by == "newest":   results.sort(key=lambda x: x.created_at, reverse=True)
    total = len(results)
    start = (page - 1) * per_page
    return results[start:start + per_page], total

def delete_product(pid: str) -> bool:
    db  = get_valkey()
    raw = db.hgetall(_key(pid))
    if not raw: return False
    db.delete(_key(pid))
    db.srem("products:all", pid)
    db.srem(f"products:category:{raw.get('category', '')}", pid)
    db.srem(f"products:brand:{raw.get('brand_id', '')}", pid)
    db.zrem("products:by_rating", pid)
    db.zrem("products:by_price",  pid)
    db.srem("products:featured",  pid)
    return True

def update_stock(pid: str, quantity: int) -> bool:
    db = get_valkey()
    raw = db.hgetall(_key(pid))
    if not raw:
        return False
    
    in_stock = "True" if quantity > 0 else "False"
    db.hset(_key(pid), mapping={
        "stock_quantity": str(quantity),
        "in_stock": in_stock,
        "updated_at": datetime.utcnow().isoformat()
    })
    return True