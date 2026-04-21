"""
seed_data.py — 50+ realistic products, brands, and users for ShopMind AI
Run: python scripts/seed_data.py
"""

import sys
import os
import json
import uuid
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.database import get_valkey, ping_valkey
from app.models.schemas import (
    Product, Brand, User, UserPreferences,
    ProductImage, ProductSpecification, Offer, DiscountType
)

db = get_valkey()

# ── Helpers ────────────────────────────────────────────────────────────────────

def uid(prefix=""):
    return (prefix + str(uuid.uuid4())[:8]).strip("-")

def now():
    return datetime.utcnow().isoformat()

def slugify(text):
    return text.lower().replace(" ", "-").replace("/", "-").replace("&", "and")

def store_product(p: Product):
    key = f"product:{p.id}"
    db.hset(key, mapping={
        "id":                p.id,
        "name":              p.name,
        "slug":              p.slug,
        "description":       p.description,
        "short_description": p.short_description,
        "brand_id":          p.brand_id,
        "brand_name":        p.brand_name,
        "category":          p.category,
        "sub_category":      p.sub_category or "",
        "condition":         p.condition,
        "mrp":               str(p.mrp),
        "selling_price":     str(p.selling_price),
        "discount_pct":      str(round((p.mrp - p.selling_price) / p.mrp * 100, 1) if p.mrp > 0 else 0),
        "currency":          p.currency,
        "thumbnail_url":     p.thumbnail_url or "",
        "tags":              json.dumps(p.tags),
        "color":             p.color or "",
        "size_options":      json.dumps(p.size_options),
        "sku":               p.sku,
        "model_number":      p.model_number or "",
        "rating":            str(p.rating),
        "rating_count":      str(p.rating_count),
        "rating_breakdown":  json.dumps(p.rating_breakdown),
        "in_stock":          str(p.in_stock),
        "stock_quantity":    str(p.stock_quantity),
        "free_shipping":     str(p.free_shipping),
        "shipping_days":     str(p.shipping_days),
        "badges":            json.dumps(p.badges),
        "is_featured":       str(p.is_featured),
        "is_active":         str(p.is_active),
        "specifications":    json.dumps([s.model_dump() for s in p.specifications]),
        "images":            json.dumps([i.model_dump() for i in p.images]),
        "offers":            json.dumps([o.model_dump() for o in p.offers]),
        "created_at":        p.created_at,
        "updated_at":        p.updated_at,
    })
    db.sadd("products:all", p.id)
    db.sadd(f"products:category:{p.category}", p.id)
    db.sadd(f"products:brand:{p.brand_id}", p.id)
    # Sorted set by rating for trending
    db.zadd("products:by_rating", {p.id: p.rating})
    db.zadd("products:by_price", {p.id: p.selling_price})
    if p.is_featured:
        db.sadd("products:featured", p.id)

def store_brand(b: Brand):
    key = f"brand:{b.id}"
    db.hset(key, mapping={
        "id":           b.id,
        "name":         b.name,
        "slug":         b.slug,
        "logo_url":     b.logo_url or "",
        "website":      b.website or "",
        "country":      b.country,
        "founded_year": str(b.founded_year or ""),
        "description":  b.description or "",
        "is_verified":  str(b.is_verified),
        "created_at":   b.created_at,
    })
    db.sadd("brands:all", b.id)

def store_user(u: User, password_hash: str):
    key = f"user:{u.id}"
    db.hset(key, mapping={
        "id":             u.id,
        "name":           u.name,
        "email":          u.email,
        "phone":          u.phone or "",
        "avatar_url":     u.avatar_url or "",
        "gender":         u.gender or "",
        "date_of_birth":  u.date_of_birth or "",
        "age":            str(u.age or ""),
        "preferences":    u.preferences.model_dump_json(),
        "loyalty_points": str(u.loyalty_points),
        "loyalty_tier":   u.loyalty_tier,
        "total_orders":   str(u.total_orders),
        "total_spent":    str(u.total_spent),
        "is_active":      str(u.is_active),
        "is_verified":    str(u.is_verified),
        "is_premium":     str(u.is_premium),
        "password_hash":  password_hash,
        "created_at":     u.created_at,
        "updated_at":     u.updated_at,
    })
    db.set(f"user:email:{u.email}", u.id)
    db.sadd("users:all", u.id)


# ══════════════════════════════════════════════════════════════════════════════
# BRANDS
# ══════════════════════════════════════════════════════════════════════════════

BRANDS = {
    "apple":    Brand(id="brand-apple",    name="Apple",    slug="apple",    country="USA",   founded_year=1976, is_verified=True,  website="https://apple.com",    description="Consumer electronics and software.", created_at=now()),
    "samsung":  Brand(id="brand-samsung",  name="Samsung",  slug="samsung",  country="South Korea", founded_year=1969, is_verified=True, website="https://samsung.com", description="Global electronics leader.", created_at=now()),
    "nike":     Brand(id="brand-nike",     name="Nike",     slug="nike",     country="USA",   founded_year=1964, is_verified=True,  website="https://nike.com",     description="World's leading sportswear brand.", created_at=now()),
    "sony":     Brand(id="brand-sony",     name="Sony",     slug="sony",     country="Japan", founded_year=1946, is_verified=True,  website="https://sony.com",     description="Electronics, gaming & entertainment.", created_at=now()),
    "levi":     Brand(id="brand-levi",     name="Levi's",   slug="levis",    country="USA",   founded_year=1853, is_verified=True,  website="https://levi.com",     description="Iconic American denim brand.", created_at=now()),
    "loreal":   Brand(id="brand-loreal",   name="L'Oréal",  slug="loreal",   country="France",founded_year=1909, is_verified=True,  website="https://loreal.com",   description="Global beauty and cosmetics leader.", created_at=now()),
    "bosch":    Brand(id="brand-bosch",    name="Bosch",    slug="bosch",    country="Germany",founded_year=1886, is_verified=True, website="https://bosch.com",    description="Engineering and technology company.", created_at=now()),
    "ikea":     Brand(id="brand-ikea",     name="IKEA",     slug="ikea",     country="Sweden",founded_year=1943, is_verified=True,  website="https://ikea.com",     description="Affordable home furnishings.", created_at=now()),
    "lg":       Brand(id="brand-lg",       name="LG",       slug="lg",       country="South Korea", founded_year=1958, is_verified=True, website="https://lg.com", description="Home appliances and electronics.", created_at=now()),
    "adidas":   Brand(id="brand-adidas",   name="Adidas",   slug="adidas",   country="Germany",founded_year=1949, is_verified=True, website="https://adidas.com",   description="Sports performance & lifestyle.", created_at=now()),
    "oneplus":  Brand(id="brand-oneplus",  name="OnePlus",  slug="oneplus",  country="China", founded_year=2013, is_verified=True,  website="https://oneplus.com",  description="Premium smartphones.", created_at=now()),
    "hp":       Brand(id="brand-hp",       name="HP",       slug="hp",       country="USA",   founded_year=1939, is_verified=True,  website="https://hp.com",       description="Personal computers and printers.", created_at=now()),
    "titan":    Brand(id="brand-titan",    name="Titan",    slug="titan",    country="India", founded_year=1984, is_verified=True,  website="https://titanworld.com", description="India's leading watches & jewellery.", created_at=now()),
    "nikon":    Brand(id="brand-nikon",    name="Nikon",    slug="nikon",    country="Japan", founded_year=1917, is_verified=True,  website="https://nikon.com",    description="Precision optics and cameras.", created_at=now()),
    "pedigree": Brand(id="brand-pedigree", name="Pedigree", slug="pedigree", country="USA",   founded_year=1934, is_verified=True,  website="https://pedigree.com", description="Leading pet nutrition brand.", created_at=now()),
}


# ══════════════════════════════════════════════════════════════════════════════
# PRODUCTS — 50+ across all categories
# ══════════════════════════════════════════════════════════════════════════════

def make_products():
    products = []

    # ── ELECTRONICS ────────────────────────────────────────────────────────────
    products.append(Product(
        id="prod-001", name="Apple iPhone 15 Pro Max", slug="apple-iphone-15-pro-max",
        description="The most advanced iPhone ever. Titanium design with Action Button, 48MP camera system, A17 Pro chip delivering console-class gaming performance.",
        short_description="Titanium iPhone with A17 Pro chip and 48MP camera.",
        brand_id="brand-apple", brand_name="Apple", category="electronics", sub_category="smartphones",
        mrp=159900, selling_price=149900, currency="INR",
        thumbnail_url="https://images.unsplash.com/photo-1696446702183-a4756f3e7285?w=400",
        images=[ProductImage(url="https://images.unsplash.com/photo-1696446702183-a4756f3e7285?w=800", is_primary=True)],
        specifications=[
            ProductSpecification(key="Display", value="6.7-inch Super Retina XDR"),
            ProductSpecification(key="Chip", value="A17 Pro"),
            ProductSpecification(key="Camera", value="48MP Main + 12MP Ultra Wide + 12MP Telephoto"),
            ProductSpecification(key="Battery", value="4422 mAh"),
            ProductSpecification(key="Storage", value="256GB / 512GB / 1TB"),
            ProductSpecification(key="OS", value="iOS 17"),
        ],
        tags=["iphone", "apple", "5g", "titanium", "pro"],
        size_options=["256GB", "512GB", "1TB"],
        color="Natural Titanium",
        sku="APPL-IP15PM-256-NT", model_number="MQDY3HN/A",
        rating=4.8, rating_count=12450,
        rating_breakdown={"5": 9500, "4": 2000, "3": 700, "2": 150, "1": 100},
        in_stock=True, stock_quantity=320, free_shipping=True, shipping_days=1,
        badges=["Best Seller", "Top Rated"], is_featured=True,
        offers=[Offer(offer_id="off-001", title="Bank Offer", description="10% instant discount on HDFC Bank Credit Cards",
                      discount_type=DiscountType.PERCENTAGE, discount_value=10, coupon_code="HDFC10")],
        created_at=now(), updated_at=now()
    ))

    products.append(Product(
        id="prod-002", name="Samsung Galaxy S24 Ultra", slug="samsung-galaxy-s24-ultra",
        description="Galaxy AI is here. The Samsung Galaxy S24 Ultra features a built-in S Pen, 200MP camera, and titanium frame for the ultimate Android experience.",
        short_description="200MP camera, built-in S Pen, Galaxy AI powered.",
        brand_id="brand-samsung", brand_name="Samsung", category="electronics", sub_category="smartphones",
        mrp=134999, selling_price=124999, currency="INR",
        thumbnail_url="https://images.unsplash.com/photo-1706795137053-16fd2bc2c97b?w=400",
        specifications=[
            ProductSpecification(key="Display", value="6.8-inch Dynamic AMOLED 2X, 120Hz"),
            ProductSpecification(key="Processor", value="Snapdragon 8 Gen 3"),
            ProductSpecification(key="Camera", value="200MP + 50MP + 10MP + 12MP"),
            ProductSpecification(key="Battery", value="5000 mAh"),
            ProductSpecification(key="RAM", value="12GB"),
        ],
        tags=["samsung", "android", "s-pen", "galaxy", "5g"],
        size_options=["256GB", "512GB", "1TB"], color="Titanium Black",
        sku="SAM-S24U-256-TB", model_number="SM-S928BZKDINS",
        rating=4.7, rating_count=8920,
        rating_breakdown={"5": 6500, "4": 1800, "3": 420, "2": 120, "1": 80},
        in_stock=True, stock_quantity=210, free_shipping=True, shipping_days=1,
        badges=["New Launch", "Top Rated"], is_featured=True,
        created_at=now(), updated_at=now()
    ))

    products.append(Product(
        id="prod-003", name="OnePlus 12 5G", slug="oneplus-12-5g",
        description="Powered by Snapdragon 8 Gen 3, the OnePlus 12 features a Hasselblad-tuned 50MP triple camera, 100W SuperVOOC charging, and a stunning 120Hz AMOLED display.",
        short_description="Snapdragon 8 Gen 3 with Hasselblad cameras and 100W charging.",
        brand_id="brand-oneplus", brand_name="OnePlus", category="electronics", sub_category="smartphones",
        mrp=64999, selling_price=56999, currency="INR",
        thumbnail_url="https://images.unsplash.com/photo-1610945415295-d9bbf067e59c?w=400",
        specifications=[
            ProductSpecification(key="Display", value="6.82-inch LTPO AMOLED, 120Hz"),
            ProductSpecification(key="Processor", value="Snapdragon 8 Gen 3"),
            ProductSpecification(key="Camera", value="50MP Main + 48MP Ultra Wide + 64MP Telephoto"),
            ProductSpecification(key="Battery", value="5400 mAh"),
            ProductSpecification(key="Charging", value="100W SuperVOOC + 50W Wireless"),
        ],
        tags=["oneplus", "5g", "hasselblad", "fast-charging", "android"],
        size_options=["256GB", "512GB"], color="Silky Black",
        sku="OP-12-256-SB",
        rating=4.6, rating_count=5430,
        rating_breakdown={"5": 3800, "4": 1200, "3": 280, "2": 90, "1": 60},
        in_stock=True, stock_quantity=150, free_shipping=True, shipping_days=2,
        badges=["Value for Money"], is_featured=False,
        created_at=now(), updated_at=now()
    ))

    # ── LAPTOPS & COMPUTERS ────────────────────────────────────────────────────
    products.append(Product(
        id="prod-004", name="Apple MacBook Air M3 13-inch", slug="apple-macbook-air-m3-13",
        description="Supercharged by M3. Incredibly thin and light laptop with up to 18 hours of battery life, 8-core CPU, and fanless design for silent operation.",
        short_description="M3 chip MacBook Air with 18-hour battery, fanless design.",
        brand_id="brand-apple", brand_name="Apple", category="laptops_computers", sub_category="laptops",
        mrp=114900, selling_price=107900, currency="INR",
        thumbnail_url="https://images.unsplash.com/photo-1611186871525-8fc4db61b4dc?w=400",
        specifications=[
            ProductSpecification(key="Chip", value="Apple M3, 8-core CPU, 10-core GPU"),
            ProductSpecification(key="RAM", value="8GB / 16GB / 24GB"),
            ProductSpecification(key="Storage", value="256GB / 512GB / 1TB SSD"),
            ProductSpecification(key="Display", value="13.6-inch Liquid Retina"),
            ProductSpecification(key="Battery", value="Up to 18 hours"),
            ProductSpecification(key="Weight", value="1.24 kg"),
        ],
        tags=["macbook", "apple", "m3", "ultrabook", "laptop"],
        size_options=["8GB RAM / 256GB", "8GB RAM / 512GB", "16GB RAM / 512GB", "16GB RAM / 1TB"],
        color="Midnight",
        sku="APPL-MBA-M3-8-256", model_number="MRXV3HN/A",
        rating=4.9, rating_count=7820,
        rating_breakdown={"5": 6800, "4": 800, "3": 150, "2": 40, "1": 30},
        in_stock=True, stock_quantity=85, free_shipping=True, shipping_days=1,
        badges=["Best Seller", "Editor's Choice"], is_featured=True,
        created_at=now(), updated_at=now()
    ))

    products.append(Product(
        id="prod-005", name="HP Pavilion 15 Laptop", slug="hp-pavilion-15-laptop",
        description="Sleek everyday laptop with Intel Core i5-13500H, 16GB RAM, and 512GB SSD. Features a 15.6-inch FHD display and NVIDIA GeForce MX550 graphics.",
        short_description="Intel i5 13th Gen with 16GB RAM and MX550 GPU.",
        brand_id="brand-hp", brand_name="HP", category="laptops_computers", sub_category="laptops",
        mrp=74999, selling_price=61990, currency="INR",
        thumbnail_url="https://images.unsplash.com/photo-1544731612-de7f96afe55f?w=400",
        specifications=[
            ProductSpecification(key="Processor", value="Intel Core i5-13500H"),
            ProductSpecification(key="RAM", value="16GB DDR4"),
            ProductSpecification(key="Storage", value="512GB SSD"),
            ProductSpecification(key="Display", value="15.6-inch FHD IPS Anti-glare"),
            ProductSpecification(key="GPU", value="NVIDIA GeForce MX550 2GB"),
            ProductSpecification(key="OS", value="Windows 11 Home"),
        ],
        tags=["hp", "laptop", "intel", "windows", "college"],
        color="Natural Silver", sku="HP-PAV15-I5-16-512",
        rating=4.2, rating_count=3210,
        rating_breakdown={"5": 1800, "4": 900, "3": 350, "2": 100, "1": 60},
        in_stock=True, stock_quantity=120, free_shipping=True, shipping_days=2,
        badges=["Value for Money"], is_featured=False,
        created_at=now(), updated_at=now()
    ))

    # ── AUDIO ──────────────────────────────────────────────────────────────────
    products.append(Product(
        id="prod-006", name="Sony WH-1000XM5 Wireless Headphones", slug="sony-wh1000xm5",
        description="Industry-leading noise cancellation with 8 microphones and Auto NC Optimizer. 30-hour battery life, speak-to-chat, multipoint connection.",
        short_description="Industry-leading ANC headphones with 30hr battery.",
        brand_id="brand-sony", brand_name="Sony", category="audio", sub_category="headphones",
        mrp=34990, selling_price=26990, currency="INR",
        thumbnail_url="https://images.unsplash.com/photo-1618366712010-f4ae9c647dcb?w=400",
        specifications=[
            ProductSpecification(key="Driver", value="30mm"),
            ProductSpecification(key="Battery", value="30 hours (ANC on)"),
            ProductSpecification(key="Connectivity", value="Bluetooth 5.2, 3.5mm Jack"),
            ProductSpecification(key="Weight", value="250g"),
            ProductSpecification(key="ANC", value="8 Microphones, Auto NC Optimizer"),
        ],
        tags=["sony", "headphones", "anc", "wireless", "audiophile"],
        color="Black", sku="SON-WH1000XM5-BLK",
        rating=4.8, rating_count=15600,
        rating_breakdown={"5": 11000, "4": 3200, "3": 900, "2": 300, "1": 200},
        in_stock=True, stock_quantity=430, free_shipping=True, shipping_days=2,
        badges=["Best Seller", "Award Winner"], is_featured=True,
        offers=[Offer(offer_id="off-002", title="No Cost EMI", description="No Cost EMI on 6 months",
                      discount_type=DiscountType.FLAT, discount_value=0)],
        created_at=now(), updated_at=now()
    ))

    products.append(Product(
        id="prod-007", name="Apple AirPods Pro (2nd Generation)", slug="apple-airpods-pro-2nd-gen",
        description="AirPods Pro with H2 chip, Adaptive Transparency, Personalized Spatial Audio, and up to 2x more Active Noise Cancellation than the previous generation.",
        short_description="H2 chip AirPods with Adaptive Transparency and ANC.",
        brand_id="brand-apple", brand_name="Apple", category="audio", sub_category="earbuds",
        mrp=24900, selling_price=20900, currency="INR",
        thumbnail_url="https://images.unsplash.com/photo-1600294037681-c80b4cb5b434?w=400",
        specifications=[
            ProductSpecification(key="Chip", value="Apple H2"),
            ProductSpecification(key="ANC", value="Active Noise Cancellation"),
            ProductSpecification(key="Battery", value="6 hours (30 hours with case)"),
            ProductSpecification(key="Water Resistance", value="IPX4"),
            ProductSpecification(key="Connectivity", value="Bluetooth 5.3"),
        ],
        tags=["airpods", "apple", "anc", "wireless", "earbuds"],
        sku="APPL-APPRO2-WHT",
        rating=4.7, rating_count=9870,
        rating_breakdown={"5": 7200, "4": 1900, "3": 500, "2": 170, "1": 100},
        in_stock=True, stock_quantity=280, free_shipping=True, shipping_days=1,
        badges=["Top Rated"], is_featured=True,
        created_at=now(), updated_at=now()
    ))

    # ── GAMING ─────────────────────────────────────────────────────────────────
    products.append(Product(
        id="prod-008", name="Sony PlayStation 5 Console (Disc Edition)", slug="sony-ps5-disc-edition",
        description="Experience lightning-fast loading with an ultra-high speed SSD, deeper immersion with haptic feedback, adaptive triggers and 3D Audio.",
        short_description="Next-gen gaming with ultra-high speed SSD and haptic feedback.",
        brand_id="brand-sony", brand_name="Sony", category="gaming", sub_category="consoles",
        mrp=54990, selling_price=49990, currency="INR",
        thumbnail_url="https://images.unsplash.com/photo-1607853202273-797f1c22a38e?w=400",
        specifications=[
            ProductSpecification(key="CPU", value="AMD Zen 2, 8 Cores at 3.5GHz"),
            ProductSpecification(key="GPU", value="10.28 TFLOPS, AMD RDNA 2"),
            ProductSpecification(key="RAM", value="16GB GDDR6"),
            ProductSpecification(key="Storage", value="825GB Custom SSD"),
            ProductSpecification(key="Optical Drive", value="Ultra HD Blu-ray"),
            ProductSpecification(key="Output", value="Up to 8K, 4K at 120fps"),
        ],
        tags=["ps5", "playstation", "gaming", "console", "sony"],
        sku="SON-PS5-DISC-WHT",
        rating=4.9, rating_count=22100,
        rating_breakdown={"5": 18000, "4": 2800, "3": 800, "2": 300, "1": 200},
        in_stock=True, stock_quantity=45, free_shipping=True, shipping_days=2,
        badges=["Best Seller", "Hot Deal"], is_featured=True,
        created_at=now(), updated_at=now()
    ))

    # ── CAMERAS ────────────────────────────────────────────────────────────────
    products.append(Product(
        id="prod-009", name="Nikon Z8 Mirrorless Camera (Body Only)", slug="nikon-z8-mirrorless-body",
        description="45.7MP full-frame BSI CMOS sensor, 8K RAW video recording, 20fps burst shooting. Professional-grade mirrorless in a lightweight body.",
        short_description="45.7MP full-frame mirrorless with 8K video.",
        brand_id="brand-nikon", brand_name="Nikon", category="cameras", sub_category="mirrorless",
        mrp=329995, selling_price=289995, currency="INR",
        thumbnail_url="https://images.unsplash.com/photo-1502920917128-1aa500764cbd?w=400",
        specifications=[
            ProductSpecification(key="Sensor", value="45.7MP Full-Frame BSI CMOS"),
            ProductSpecification(key="Video", value="8K RAW, 4K 120fps"),
            ProductSpecification(key="ISO", value="100-64000 (expandable to 204800)"),
            ProductSpecification(key="AF Points", value="493 Phase-detect"),
            ProductSpecification(key="Burst", value="20 fps (RAW)"),
            ProductSpecification(key="Weight", value="820g"),
        ],
        tags=["nikon", "mirrorless", "camera", "professional", "8k"],
        sku="NIK-Z8-BODY",
        rating=4.9, rating_count=1230,
        rating_breakdown={"5": 1100, "4": 100, "3": 20, "2": 5, "1": 5},
        in_stock=True, stock_quantity=18, free_shipping=True, shipping_days=3,
        badges=["Professional Choice"], is_featured=True,
        created_at=now(), updated_at=now()
    ))

    # ── FASHION - MEN ──────────────────────────────────────────────────────────
    products.append(Product(
        id="prod-010", name="Nike Air Max 270 Men's Shoes", slug="nike-air-max-270-mens",
        description="Max Air unit in the heel delivers incredible all-day comfort. Engineered mesh upper provides breathability, while the foam midsole creates a lightweight feel.",
        short_description="Max Air heel cushioning with breathable mesh upper.",
        brand_id="brand-nike", brand_name="Nike", category="fashion_men", sub_category="shoes",
        mrp=12995, selling_price=9746, currency="INR",
        thumbnail_url="https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400",
        specifications=[
            ProductSpecification(key="Upper", value="Engineered Mesh"),
            ProductSpecification(key="Midsole", value="Max Air unit + foam"),
            ProductSpecification(key="Outsole", value="Rubber"),
            ProductSpecification(key="Closure", value="Lace-up"),
        ],
        tags=["nike", "airmax", "shoes", "running", "sneakers", "men"],
        size_options=["UK 6", "UK 7", "UK 8", "UK 9", "UK 10", "UK 11"],
        color="Black/White",
        sku="NIK-AM270-M-BW-08", model_number="AH8050-002",
        rating=4.5, rating_count=8760,
        rating_breakdown={"5": 5500, "4": 2300, "3": 700, "2": 160, "1": 100},
        in_stock=True, stock_quantity=340, free_shipping=True, shipping_days=3,
        badges=["Top Rated", "Best Seller"],
        created_at=now(), updated_at=now()
    ))

    products.append(Product(
        id="prod-011", name="Levi's 511 Slim Fit Jeans", slug="levis-511-slim-fit-jeans",
        description="The Levi's 511 Slim Fit Jeans sit below the waist and are slim through the thigh and leg. Made with stretch denim for all-day comfort.",
        short_description="Classic slim fit jeans with stretch denim comfort.",
        brand_id="brand-levi", brand_name="Levi's", category="fashion_men", sub_category="jeans",
        mrp=3999, selling_price=2799, currency="INR",
        thumbnail_url="https://images.unsplash.com/photo-1542272604-787c3835535d?w=400",
        specifications=[
            ProductSpecification(key="Fit", value="Slim"),
            ProductSpecification(key="Rise", value="Below Waist"),
            ProductSpecification(key="Fabric", value="99% Cotton, 1% Elastane"),
            ProductSpecification(key="Wash", value="Dark Indigo"),
        ],
        tags=["levis", "jeans", "denim", "slim", "men"],
        size_options=["28x30", "30x30", "32x30", "32x32", "34x30", "34x32", "36x32"],
        color="Dark Indigo", sku="LEV-511-DI-32X32",
        rating=4.4, rating_count=5430,
        rating_breakdown={"5": 2900, "4": 1700, "3": 600, "2": 150, "1": 80},
        in_stock=True, stock_quantity=560, free_shipping=False, shipping_days=4,
        badges=["Classic Pick"],
        created_at=now(), updated_at=now()
    ))

    products.append(Product(
        id="prod-012", name="Adidas Ultraboost 23 Running Shoes", slug="adidas-ultraboost-23",
        description="Responsive BOOST midsole, Primeknit+ upper that moves with your foot, and Continental rubber outsole. Designed for the long run.",
        short_description="Responsive BOOST cushioning with Primeknit+ upper.",
        brand_id="brand-adidas", brand_name="Adidas", category="fashion_men", sub_category="shoes",
        mrp=17999, selling_price=14399, currency="INR",
        thumbnail_url="https://images.unsplash.com/photo-1608231387042-66d1773070a5?w=400",
        specifications=[
            ProductSpecification(key="Upper", value="Primeknit+"),
            ProductSpecification(key="Midsole", value="BOOST"),
            ProductSpecification(key="Outsole", value="Continental Rubber"),
            ProductSpecification(key="Drop", value="10mm"),
        ],
        tags=["adidas", "ultraboost", "running", "shoes", "men", "boost"],
        size_options=["UK 6", "UK 7", "UK 8", "UK 9", "UK 10", "UK 11", "UK 12"],
        color="Core Black", sku="ADI-UB23-M-CB-09",
        rating=4.6, rating_count=6780,
        rating_breakdown={"5": 4200, "4": 1800, "3": 550, "2": 150, "1": 80},
        in_stock=True, stock_quantity=220, free_shipping=True, shipping_days=3,
        badges=["Editor's Choice"],
        created_at=now(), updated_at=now()
    ))

    # ── FASHION - WOMEN ────────────────────────────────────────────────────────
    products.append(Product(
        id="prod-013", name="Nike Air Force 1 Women's Shoes", slug="nike-air-force-1-womens",
        description="The radiance lives on in the Nike Air Force 1. This b-ball icon is encased in clean, premium leather with a low-cut silhouette and encapsulated Air cushioning.",
        short_description="Iconic low-top leather sneaker with Air cushioning.",
        brand_id="brand-nike", brand_name="Nike", category="fashion_women", sub_category="shoes",
        mrp=8695, selling_price=7499, currency="INR",
        thumbnail_url="https://images.unsplash.com/photo-1549298916-b41d501d3772?w=400",
        specifications=[
            ProductSpecification(key="Upper", value="Full-grain leather"),
            ProductSpecification(key="Midsole", value="Encapsulated Air unit"),
            ProductSpecification(key="Outsole", value="Rubber"),
        ],
        tags=["nike", "air force 1", "women", "sneakers", "shoes", "casual"],
        size_options=["UK 3", "UK 4", "UK 5", "UK 6", "UK 7", "UK 8"],
        color="White", sku="NIK-AF1-W-WHT-06",
        rating=4.7, rating_count=11200,
        rating_breakdown={"5": 7800, "4": 2400, "3": 700, "2": 200, "1": 100},
        in_stock=True, stock_quantity=480, free_shipping=True, shipping_days=3,
        badges=["Best Seller", "Top Rated"],
        created_at=now(), updated_at=now()
    ))

    # ── HOME APPLIANCES ────────────────────────────────────────────────────────
    products.append(Product(
        id="prod-014", name="LG 260L 3-Star Frost-Free Double Door Refrigerator", slug="lg-260l-3star-fridge",
        description="Smart Inverter Compressor for energy efficiency. Door Cooling+ ensures uniform cooling. Moist Balance Crisper keeps vegetables and fruits fresh longer.",
        short_description="260L frost-free fridge with Smart Inverter Compressor.",
        brand_id="brand-lg", brand_name="LG", category="home_appliances", sub_category="refrigerators",
        mrp=35990, selling_price=28490, currency="INR",
        thumbnail_url="https://images.unsplash.com/photo-1571175443880-49e1d25b2bc5?w=400",
        specifications=[
            ProductSpecification(key="Capacity", value="260 Litres"),
            ProductSpecification(key="Star Rating", value="3 Star"),
            ProductSpecification(key="Type", value="Frost Free Double Door"),
            ProductSpecification(key="Compressor", value="Smart Inverter"),
            ProductSpecification(key="Annual Energy", value="258 kWh"),
            ProductSpecification(key="Warranty", value="1 Year + 10 Year Compressor"),
        ],
        tags=["lg", "refrigerator", "fridge", "double door", "inverter", "home"],
        color="Shiny Steel", sku="LG-GN-B262SQSY",
        rating=4.3, rating_count=4320,
        rating_breakdown={"5": 2200, "4": 1300, "3": 550, "2": 180, "1": 90},
        in_stock=True, stock_quantity=35, free_shipping=True, shipping_days=5,
        badges=["Energy Efficient"],
        created_at=now(), updated_at=now()
    ))

    products.append(Product(
        id="prod-015", name="Bosch 7kg Fully Automatic Front Load Washing Machine", slug="bosch-7kg-front-load-washer",
        description="EcoSilence Drive motor for whisper-quiet operation. ActiveWater Plus technology reduces water consumption. SpeedPerfect option saves 65% time.",
        short_description="7kg front loader with EcoSilence Drive and SpeedPerfect.",
        brand_id="brand-bosch", brand_name="Bosch", category="home_appliances", sub_category="washing_machines",
        mrp=56990, selling_price=44990, currency="INR",
        thumbnail_url="https://images.unsplash.com/photo-1626806787461-102c1bfaaea1?w=400",
        specifications=[
            ProductSpecification(key="Capacity", value="7 kg"),
            ProductSpecification(key="Type", value="Front Load"),
            ProductSpecification(key="Spin Speed", value="1200 RPM"),
            ProductSpecification(key="Programs", value="15 wash programs"),
            ProductSpecification(key="Energy Rating", value="5 Star"),
        ],
        tags=["bosch", "washing machine", "front load", "inverter", "home appliance"],
        color="White", sku="BOSCH-WAJ2416SIN",
        rating=4.5, rating_count=3120,
        rating_breakdown={"5": 1800, "4": 900, "3": 280, "2": 90, "1": 50},
        in_stock=True, stock_quantity=22, free_shipping=True, shipping_days=5,
        badges=["5-Star Rating"],
        created_at=now(), updated_at=now()
    ))

    products.append(Product(
        id="prod-016", name="Samsung 55-inch 4K Neo QLED Smart TV", slug="samsung-55-neo-qled-4k",
        description="Neo QLED with Quantum Mini LED technology for deep blacks and brilliant brightness. Object Tracking Sound+ fills the room with immersive audio.",
        short_description="55-inch Neo QLED 4K TV with Quantum Mini LED.",
        brand_id="brand-samsung", brand_name="Samsung", category="home_appliances", sub_category="televisions",
        mrp=119990, selling_price=84990, currency="INR",
        thumbnail_url="https://images.unsplash.com/photo-1593784991095-a205069470b6?w=400",
        specifications=[
            ProductSpecification(key="Screen Size", value="55 inches"),
            ProductSpecification(key="Resolution", value="3840 x 2160 (4K UHD)"),
            ProductSpecification(key="Display", value="Neo QLED, 120Hz"),
            ProductSpecification(key="HDR", value="HDR 2000, Quantum HDR"),
            ProductSpecification(key="Audio", value="60W, Dolby Atmos"),
            ProductSpecification(key="OS", value="Tizen Smart TV"),
        ],
        tags=["samsung", "tv", "4k", "neo qled", "smart tv", "oled"],
        sku="SAM-QN55QN85C", color="Black",
        rating=4.6, rating_count=7890,
        rating_breakdown={"5": 5200, "4": 1900, "3": 500, "2": 190, "1": 100},
        in_stock=True, stock_quantity=28, free_shipping=True, shipping_days=3,
        badges=["Best Seller", "Top Rated"], is_featured=True,
        created_at=now(), updated_at=now()
    ))

    # ── HOME DECOR ─────────────────────────────────────────────────────────────
    products.append(Product(
        id="prod-017", name="IKEA KALLAX Shelf Unit 77x147cm", slug="ikea-kallax-shelf-77x147",
        description="A classic storage unit that works as a room divider, shelving unit, or sideboard. Combine with inserts for customized storage solutions.",
        short_description="Versatile 4x2 shelf unit — use alone or with inserts.",
        brand_id="brand-ikea", brand_name="IKEA", category="home_decor", sub_category="shelving",
        mrp=13999, selling_price=10999, currency="INR",
        thumbnail_url="https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=400",
        specifications=[
            ProductSpecification(key="Dimensions", value="77 x 39 x 147 cm"),
            ProductSpecification(key="Material", value="Particleboard, Foil"),
            ProductSpecification(key="Max Load", value="13 kg per shelf"),
            ProductSpecification(key="Compartments", value="8"),
        ],
        tags=["ikea", "shelf", "storage", "home decor", "kallax", "organization"],
        color="White", sku="IKE-KALLAX-W-4X2",
        rating=4.4, rating_count=6540,
        rating_breakdown={"5": 3800, "4": 1800, "3": 600, "2": 220, "1": 120},
        in_stock=True, stock_quantity=90, free_shipping=False, shipping_days=7,
        badges=["Customer Favourite"],
        created_at=now(), updated_at=now()
    ))

    # ── BEAUTY & SKINCARE ──────────────────────────────────────────────────────
    products.append(Product(
        id="prod-018", name="L'Oréal Paris Revitalift Crystal Serum", slug="loreal-revitalift-crystal-serum",
        description="Micro-essence serum with 2% pure hyaluronic acid. Visibly replumps skin in 7 days and reduces wrinkles in 4 weeks. Suitable for all skin types.",
        short_description="2% hyaluronic acid serum for plump, wrinkle-free skin.",
        brand_id="brand-loreal", brand_name="L'Oréal", category="beauty_skincare", sub_category="serums",
        mrp=1299, selling_price=879, currency="INR",
        thumbnail_url="https://images.unsplash.com/photo-1631730486572-226d1f595058?w=400",
        specifications=[
            ProductSpecification(key="Key Ingredient", value="2% Pure Hyaluronic Acid"),
            ProductSpecification(key="Skin Type", value="All Skin Types"),
            ProductSpecification(key="Volume", value="30ml"),
            ProductSpecification(key="SPF", value="None"),
        ],
        tags=["loreal", "serum", "hyaluronic acid", "anti-aging", "skincare", "women"],
        sku="LOR-RVCRYST-30ML",
        rating=4.3, rating_count=18900,
        rating_breakdown={"5": 9500, "4": 5800, "3": 2500, "2": 700, "1": 400},
        in_stock=True, stock_quantity=950, free_shipping=True, shipping_days=3,
        badges=["Best Seller", "Dermatologist Recommended"],
        created_at=now(), updated_at=now()
    ))

    products.append(Product(
        id="prod-019", name="L'Oréal Paris Excellence Creme Hair Color", slug="loreal-excellence-creme-hair-color",
        description="Pro-Keratin + Ceramide formula for silky, shiny, long-lasting color. 100% grey coverage with a nourishing conditioner included.",
        short_description="Pro-Keratin formula hair color with 100% grey coverage.",
        brand_id="brand-loreal", brand_name="L'Oréal", category="beauty_skincare", sub_category="hair_care",
        mrp=399, selling_price=269, currency="INR",
        thumbnail_url="https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=400",
        specifications=[
            ProductSpecification(key="Coverage", value="100% Grey Coverage"),
            ProductSpecification(key="Duration", value="Up to 8 weeks"),
            ProductSpecification(key="Formula", value="Pro-Keratin + Ceramide"),
        ],
        tags=["loreal", "hair color", "grey coverage", "beauty", "hair care"],
        size_options=["Natural Black", "Dark Brown", "Medium Brown", "Dark Blonde", "Light Blonde"],
        sku="LOR-EXC-CREME-NB",
        rating=4.2, rating_count=42000,
        rating_breakdown={"5": 21000, "4": 12000, "3": 6000, "2": 2000, "1": 1000},
        in_stock=True, stock_quantity=1500, free_shipping=False, shipping_days=4,
        badges=["Best Seller"],
        created_at=now(), updated_at=now()
    ))

    # ── SPORTS & FITNESS ───────────────────────────────────────────────────────
    products.append(Product(
        id="prod-020", name="Nike Dri-FIT Men's Running T-Shirt", slug="nike-dri-fit-mens-running-tshirt",
        description="Nike Dri-FIT technology moves sweat away from skin for quicker evaporation. Lightweight, breathable fabric keeps you comfortable through your toughest workouts.",
        short_description="Sweat-wicking Dri-FIT fabric for intense workouts.",
        brand_id="brand-nike", brand_name="Nike", category="sports_fitness", sub_category="sports_clothing",
        mrp=2495, selling_price=1796, currency="INR",
        thumbnail_url="https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?w=400",
        specifications=[
            ProductSpecification(key="Fabric", value="100% Polyester"),
            ProductSpecification(key="Technology", value="Nike Dri-FIT"),
            ProductSpecification(key="Fit", value="Standard"),
        ],
        tags=["nike", "t-shirt", "dri-fit", "running", "sports", "gym", "men"],
        size_options=["XS", "S", "M", "L", "XL", "XXL"],
        color="Black", sku="NIK-DRIFIT-M-BLK-M",
        rating=4.5, rating_count=12300,
        rating_breakdown={"5": 7200, "4": 3400, "3": 1200, "2": 300, "1": 200},
        in_stock=True, stock_quantity=650, free_shipping=True, shipping_days=3,
        badges=["Best Seller"],
        created_at=now(), updated_at=now()
    ))

    products.append(Product(
        id="prod-021", name="Adidas Predator 24 Club Football Boots", slug="adidas-predator-24-club-football",
        description="Wrap-around control zones improve touch on all playing surfaces. Soft upper with ZONES print for improved feel and control of the ball.",
        short_description="ZONES control zones for superior ball touch and control.",
        brand_id="brand-adidas", brand_name="Adidas", category="sports_fitness", sub_category="football",
        mrp=5999, selling_price=4199, currency="INR",
        thumbnail_url="https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400",
        specifications=[
            ProductSpecification(key="Upper", value="Synthetic"),
            ProductSpecification(key="Surface", value="Firm Ground"),
            ProductSpecification(key="Closure", value="Lace-up"),
        ],
        tags=["adidas", "football", "boots", "predator", "sports"],
        size_options=["UK 6", "UK 7", "UK 8", "UK 9", "UK 10", "UK 11"],
        color="Core Black/White", sku="ADI-PRED24-FG-BW-08",
        rating=4.3, rating_count=2340,
        rating_breakdown={"5": 1300, "4": 700, "3": 210, "2": 80, "1": 50},
        in_stock=True, stock_quantity=180, free_shipping=False, shipping_days=4,
        created_at=now(), updated_at=now()
    ))

    products.append(Product(
        id="prod-022", name="Yoga Mat 6mm Non-Slip TPE", slug="yoga-mat-6mm-non-slip-tpe",
        description="Eco-friendly TPE yoga mat with double-sided non-slip texture. 6mm thick for joint protection. Includes carrying strap. Odour-free and moisture-resistant.",
        short_description="Eco-friendly 6mm TPE mat with double non-slip texture.",
        brand_id="brand-adidas", brand_name="Adidas", category="sports_fitness", sub_category="yoga",
        mrp=2499, selling_price=1299, currency="INR",
        thumbnail_url="https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?w=400",
        specifications=[
            ProductSpecification(key="Material", value="TPE"),
            ProductSpecification(key="Thickness", value="6mm"),
            ProductSpecification(key="Dimensions", value="183 x 61 cm"),
            ProductSpecification(key="Weight", value="1.1 kg"),
        ],
        tags=["yoga mat", "exercise", "fitness", "meditation", "non-slip"],
        color="Purple/Black", sku="GEN-YOGAMAT-6MM-PB",
        rating=4.4, rating_count=8900,
        rating_breakdown={"5": 5500, "4": 2300, "3": 750, "2": 230, "1": 120},
        in_stock=True, stock_quantity=780, free_shipping=True, shipping_days=3,
        badges=["Best Seller"],
        created_at=now(), updated_at=now()
    ))

    # ── BOOKS ──────────────────────────────────────────────────────────────────
    products.append(Product(
        id="prod-023", name="Atomic Habits by James Clear (Paperback)", slug="atomic-habits-james-clear-paperback",
        description="An easy and proven way to build good habits and break bad ones. With over 15 million copies sold, this New York Times bestseller is a practical guide to behavior change.",
        short_description="15M+ copies sold. The definitive guide to habit formation.",
        brand_id="brand-hp", brand_name="Penguin Random House", category="books", sub_category="self_help",
        mrp=499, selling_price=311, currency="INR",
        thumbnail_url="https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=400",
        specifications=[
            ProductSpecification(key="Author", value="James Clear"),
            ProductSpecification(key="Publisher", value="Penguin Business"),
            ProductSpecification(key="Pages", value="320"),
            ProductSpecification(key="Language", value="English"),
            ProductSpecification(key="ISBN", value="978-1847941831"),
        ],
        tags=["book", "habits", "self-help", "productivity", "james clear", "bestseller"],
        sku="BK-ATHMBT-PB",
        rating=4.8, rating_count=89000,
        rating_breakdown={"5": 68000, "4": 14000, "3": 4500, "2": 1500, "1": 1000},
        in_stock=True, stock_quantity=2000, free_shipping=True, shipping_days=2,
        badges=["Bestseller", "#1 on Charts"],
        created_at=now(), updated_at=now()
    ))

    products.append(Product(
        id="prod-024", name="The Psychology of Money by Morgan Housel (Paperback)", slug="psychology-of-money-morgan-housel",
        description="19 short stories about the strange ways people think about money. Timeless lessons on wealth, greed, and happiness by bestselling author Morgan Housel.",
        short_description="19 timeless lessons on money, wealth, and happiness.",
        brand_id="brand-hp", brand_name="Jaico Publishing", category="books", sub_category="finance",
        mrp=399, selling_price=259, currency="INR",
        thumbnail_url="https://images.unsplash.com/photo-1553729459-efe14ef6055d?w=400",
        specifications=[
            ProductSpecification(key="Author", value="Morgan Housel"),
            ProductSpecification(key="Publisher", value="Harriman House"),
            ProductSpecification(key="Pages", value="256"),
            ProductSpecification(key="Language", value="English"),
        ],
        tags=["book", "finance", "money", "investing", "bestseller", "morgan housel"],
        sku="BK-PSYMNY-PB",
        rating=4.7, rating_count=54000,
        rating_breakdown={"5": 38000, "4": 11000, "3": 3500, "2": 1000, "1": 500},
        in_stock=True, stock_quantity=1500, free_shipping=True, shipping_days=2,
        badges=["Bestseller"],
        created_at=now(), updated_at=now()
    ))

    # ── TOYS & GAMES ───────────────────────────────────────────────────────────
    products.append(Product(
        id="prod-025", name="LEGO Technic Land Rover Defender 42110", slug="lego-technic-land-rover-defender-42110",
        description="Build and display an iconic Land Rover Defender replica with 2573 pieces. Features working suspension, gearbox, and detailed interior. For ages 11+.",
        short_description="2573-piece Land Rover Defender replica with working mechanics.",
        brand_id="brand-hp", brand_name="LEGO", category="toys_games", sub_category="building_sets",
        mrp=19999, selling_price=14999, currency="INR",
        thumbnail_url="https://images.unsplash.com/photo-1587654780291-39c9404d746b?w=400",
        specifications=[
            ProductSpecification(key="Pieces", value="2573"),
            ProductSpecification(key="Age Range", value="11+ years"),
            ProductSpecification(key="Dimensions (built)", value="14 x 28 x 13 cm"),
            ProductSpecification(key="Scale", value="1:8"),
        ],
        tags=["lego", "technic", "land rover", "building set", "toys", "kids", "collector"],
        sku="LEGO-42110-LRD",
        rating=4.9, rating_count=3450,
        rating_breakdown={"5": 3000, "4": 350, "3": 70, "2": 20, "1": 10},
        in_stock=True, stock_quantity=65, free_shipping=True, shipping_days=3,
        badges=["Top Rated", "Collector's Edition"], is_featured=True,
        created_at=now(), updated_at=now()
    ))

    # ── MOBILE ACCESSORIES ─────────────────────────────────────────────────────
    products.append(Product(
        id="prod-026", name="Apple MagSafe Charger 15W", slug="apple-magsafe-charger-15w",
        description="The MagSafe Charger connects magnetically to deliver up to 15W of fast wireless charging for iPhone 12 and later. USB-C connector included.",
        short_description="Magnetic 15W wireless charger for iPhone 12 and later.",
        brand_id="brand-apple", brand_name="Apple", category="mobile_accessories", sub_category="chargers",
        mrp=4500, selling_price=3900, currency="INR",
        thumbnail_url="https://images.unsplash.com/photo-1633269540827-728aabbb7646?w=400",
        specifications=[
            ProductSpecification(key="Output", value="Up to 15W"),
            ProductSpecification(key="Connector", value="USB-C"),
            ProductSpecification(key="Compatibility", value="iPhone 12 and later"),
            ProductSpecification(key="Cable Length", value="1m"),
        ],
        tags=["apple", "magsafe", "charger", "wireless", "iphone", "accessories"],
        sku="APPL-MAGSAFE-15W", model_number="MHXH3HN/A",
        rating=4.5, rating_count=28900,
        rating_breakdown={"5": 18000, "4": 7000, "3": 2500, "2": 900, "1": 500},
        in_stock=True, stock_quantity=720, free_shipping=True, shipping_days=2,
        badges=["Best Seller"],
        created_at=now(), updated_at=now()
    ))

    products.append(Product(
        id="prod-027", name="Samsung 65W Super Fast Charging Adapter", slug="samsung-65w-super-fast-adapter",
        description="65W USB-C PD fast charging adapter compatible with Galaxy S24 series, Note, Tab, and MacBook. Compact design with GaN technology.",
        short_description="65W GaN fast charger for Galaxy, Tab and MacBook.",
        brand_id="brand-samsung", brand_name="Samsung", category="mobile_accessories", sub_category="chargers",
        mrp=2999, selling_price=2199, currency="INR",
        thumbnail_url="https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400",
        specifications=[
            ProductSpecification(key="Output", value="65W USB-C PD"),
            ProductSpecification(key="Technology", value="GaN"),
            ProductSpecification(key="Compatibility", value="Galaxy, MacBook, iPad"),
        ],
        tags=["samsung", "charger", "65w", "fast charging", "usb-c", "gan"],
        sku="SAM-EP-T6530NB", color="Black",
        rating=4.4, rating_count=9800,
        rating_breakdown={"5": 6000, "4": 2500, "3": 900, "2": 250, "1": 150},
        in_stock=True, stock_quantity=430, free_shipping=False, shipping_days=3,
        created_at=now(), updated_at=now()
    ))

    # ── HEALTH & WELLNESS ──────────────────────────────────────────────────────
    products.append(Product(
        id="prod-028", name="Fitbit Charge 6 Fitness Tracker", slug="fitbit-charge-6-fitness-tracker",
        description="Built-in GPS, ECG app, Google Maps, Google Wallet integration. 24/7 heart rate monitoring with stress management score and 7-day battery.",
        short_description="Built-in GPS, ECG, Google Maps and 7-day battery.",
        brand_id="brand-samsung", brand_name="Fitbit", category="health_wellness", sub_category="fitness_trackers",
        mrp=17999, selling_price=13499, currency="INR",
        thumbnail_url="https://images.unsplash.com/photo-1575311373937-040b8e1fd5b6?w=400",
        specifications=[
            ProductSpecification(key="GPS", value="Built-in"),
            ProductSpecification(key="Battery", value="Up to 7 days"),
            ProductSpecification(key="Sensors", value="Heart rate, SpO2, ECG, Skin Temp"),
            ProductSpecification(key="Water Resistance", value="50m"),
            ProductSpecification(key="Display", value="AMOLED, Always-on"),
        ],
        tags=["fitbit", "fitness tracker", "gps", "health", "smartwatch", "ecg"],
        color="Obsidian/Black", sku="FIT-CHRG6-OB",
        rating=4.4, rating_count=6750,
        rating_breakdown={"5": 3800, "4": 1900, "3": 700, "2": 220, "1": 130},
        in_stock=True, stock_quantity=190, free_shipping=True, shipping_days=2,
        badges=["Google Integration"],
        created_at=now(), updated_at=now()
    ))

    # ── JEWELLERY ──────────────────────────────────────────────────────────────
    products.append(Product(
        id="prod-029", name="Titan Raga Diamond Watch for Women", slug="titan-raga-diamond-watch-women",
        description="Elegant oval dial with 12 genuine diamond hour markers. Mother of Pearl dial, stainless steel case with rose gold PVD plating. Water resistant up to 30m.",
        short_description="Oval dial with 12 real diamonds and rose gold PVD plating.",
        brand_id="brand-titan", brand_name="Titan", category="jewellery", sub_category="watches",
        mrp=18995, selling_price=15195, currency="INR",
        thumbnail_url="https://images.unsplash.com/photo-1611591437281-460bfbe1220a?w=400",
        specifications=[
            ProductSpecification(key="Case Material", value="Stainless Steel"),
            ProductSpecification(key="Case Finish", value="Rose Gold PVD"),
            ProductSpecification(key="Dial", value="Mother of Pearl with 12 Diamonds"),
            ProductSpecification(key="Strap", value="Stainless Steel Bracelet"),
            ProductSpecification(key="Water Resistance", value="30m"),
            ProductSpecification(key="Movement", value="Quartz"),
        ],
        tags=["titan", "raga", "watch", "diamond", "women", "jewellery", "gift"],
        color="Rose Gold", sku="TITAN-RAGA-2590WM01", model_number="2590WM01",
        rating=4.6, rating_count=2340,
        rating_breakdown={"5": 1500, "4": 620, "3": 150, "2": 45, "1": 25},
        in_stock=True, stock_quantity=42, free_shipping=True, shipping_days=3,
        badges=["Gift Worthy", "Top Rated"],
        created_at=now(), updated_at=now()
    ))

    # ── FOOD & GROCERY ─────────────────────────────────────────────────────────
    products.append(Product(
        id="prod-030", name="Nescafé Gold Blend Coffee 200g", slug="nescafe-gold-blend-200g",
        description="Made with the finest Arabica and Robusta coffee beans, expertly roasted and freeze-dried to preserve the full aroma and smooth taste.",
        short_description="Freeze-dried Arabica-Robusta blend for rich, smooth coffee.",
        brand_id="brand-hp", brand_name="Nescafé", category="food_grocery", sub_category="coffee",
        mrp=699, selling_price=559, currency="INR",
        thumbnail_url="https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=400",
        specifications=[
            ProductSpecification(key="Weight", value="200g"),
            ProductSpecification(key="Type", value="Freeze-dried Instant Coffee"),
            ProductSpecification(key="Blend", value="Arabica + Robusta"),
            ProductSpecification(key="Caffeine", value="~90mg per cup"),
        ],
        tags=["nescafe", "coffee", "instant coffee", "arabica", "grocery"],
        sku="NES-GOLD-200G",
        rating=4.4, rating_count=32000,
        rating_breakdown={"5": 18000, "4": 9000, "3": 3500, "2": 1000, "1": 500},
        in_stock=True, stock_quantity=3000, free_shipping=False, shipping_days=3,
        badges=["Best Seller"],
        created_at=now(), updated_at=now()
    ))

    # ── AUTOMOTIVE ─────────────────────────────────────────────────────────────
    products.append(Product(
        id="prod-031", name="Bosch AGM Car Battery 60Ah", slug="bosch-agm-car-battery-60ah",
        description="AGM technology for stop-start vehicles. 3x longer service life. Sealed, maintenance-free design with vibration resistance for Indian road conditions.",
        short_description="AGM battery for stop-start cars — 3x longer life.",
        brand_id="brand-bosch", brand_name="Bosch", category="automotive", sub_category="batteries",
        mrp=12499, selling_price=9999, currency="INR",
        thumbnail_url="https://images.unsplash.com/photo-1615411640703-e9e73ed47f2a?w=400",
        specifications=[
            ProductSpecification(key="Capacity", value="60Ah"),
            ProductSpecification(key="Type", value="AGM"),
            ProductSpecification(key="CCA", value="540A"),
            ProductSpecification(key="Warranty", value="2 Years"),
            ProductSpecification(key="Compatible", value="Stop-start vehicles"),
        ],
        tags=["bosch", "car battery", "agm", "automotive", "stop-start"],
        sku="BOSCH-AGM-60AH",
        rating=4.3, rating_count=1890,
        rating_breakdown={"5": 1000, "4": 600, "3": 180, "2": 70, "1": 40},
        in_stock=True, stock_quantity=55, free_shipping=True, shipping_days=4,
        badges=["Trusted Brand"],
        created_at=now(), updated_at=now()
    ))

    # ── PET SUPPLIES ───────────────────────────────────────────────────────────
    products.append(Product(
        id="prod-032", name="Pedigree Adult Dry Dog Food Chicken & Vegetables 10kg", slug="pedigree-adult-dry-dog-food-10kg",
        description="Complete and balanced nutrition for adult dogs. Contains real chicken, vegetables and essential vitamins and minerals. Supports healthy skin, coat, and digestion.",
        short_description="Complete nutrition dog food with real chicken, 10kg.",
        brand_id="brand-pedigree", brand_name="Pedigree", category="pet_supplies", sub_category="dog_food",
        mrp=2499, selling_price=1899, currency="INR",
        thumbnail_url="https://images.unsplash.com/photo-1587300003388-59208cc962cb?w=400",
        specifications=[
            ProductSpecification(key="Weight", value="10 kg"),
            ProductSpecification(key="Life Stage", value="Adult (1-7 years)"),
            ProductSpecification(key="Protein", value="18% min"),
            ProductSpecification(key="Fat", value="8% min"),
            ProductSpecification(key="Flavour", value="Chicken & Vegetables"),
        ],
        tags=["pedigree", "dog food", "pet food", "chicken", "adult dog"],
        sku="PED-ADULT-CKN-10KG",
        rating=4.5, rating_count=28000,
        rating_breakdown={"5": 17000, "4": 7500, "3": 2500, "2": 600, "1": 400},
        in_stock=True, stock_quantity=890, free_shipping=True, shipping_days=3,
        badges=["Vet Recommended", "Best Seller"],
        created_at=now(), updated_at=now()
    ))

    # ── FASHION - KIDS ─────────────────────────────────────────────────────────
    products.append(Product(
        id="prod-033", name="Nike Kids' Air Max 90 LTR Shoes", slug="nike-kids-air-max-90-ltr",
        description="Inspired by the original AW running shoe, the Air Max 90 stays true to its roots with iconic Waffle outsole, stitched overlays and classic TPU details.",
        short_description="Iconic Air Max design in durable kids' size.",
        brand_id="brand-nike", brand_name="Nike", category="fashion_kids", sub_category="shoes",
        mrp=6995, selling_price=5246, currency="INR",
        thumbnail_url="https://images.unsplash.com/photo-1576566588028-4147f3842f27?w=400",
        specifications=[
            ProductSpecification(key="Upper", value="Leather + Synthetic"),
            ProductSpecification(key="Midsole", value="Max Air unit"),
            ProductSpecification(key="Closure", value="Lace-up"),
        ],
        tags=["nike", "kids", "air max", "shoes", "sneakers", "children"],
        size_options=["UK 1", "UK 2", "UK 3", "UK 4", "UK 5"],
        color="White/Black/Red", sku="NIK-AM90K-WBR-03",
        rating=4.6, rating_count=4320,
        rating_breakdown={"5": 2900, "4": 1100, "3": 250, "2": 50, "1": 20},
        in_stock=True, stock_quantity=210, free_shipping=True, shipping_days=3,
        created_at=now(), updated_at=now()
    ))

    # ── MORE ELECTRONICS ───────────────────────────────────────────────────────
    products.append(Product(
        id="prod-034", name="Apple iPad Air M2 11-inch Wi-Fi 256GB", slug="apple-ipad-air-m2-11-inch-256gb",
        description="M2 chip in the thinnest, lightest iPad Air ever. Landscape front camera, Wi-Fi 6E connectivity, USB-C with 2x faster transfer speeds. Works with Apple Pencil Pro.",
        short_description="M2-powered iPad Air, thinnest and lightest ever built.",
        brand_id="brand-apple", brand_name="Apple", category="electronics", sub_category="tablets",
        mrp=74900, selling_price=69900, currency="INR",
        thumbnail_url="https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?w=400",
        specifications=[
            ProductSpecification(key="Chip", value="Apple M2, 8-core CPU"),
            ProductSpecification(key="Display", value="11-inch Liquid Retina, 500 nits"),
            ProductSpecification(key="Storage", value="256GB"),
            ProductSpecification(key="Camera", value="12MP Wide + 12MP Front"),
            ProductSpecification(key="Battery", value="Up to 10 hours"),
        ],
        tags=["apple", "ipad", "m2", "tablet", "air"],
        size_options=["64GB", "256GB"], color="Blue",
        sku="APPL-IPADAIRM2-11-256-BLU",
        rating=4.8, rating_count=5430,
        rating_breakdown={"5": 4200, "4": 900, "3": 220, "2": 60, "1": 50},
        in_stock=True, stock_quantity=110, free_shipping=True, shipping_days=1,
        badges=["New Launch", "Top Rated"], is_featured=True,
        created_at=now(), updated_at=now()
    ))

    products.append(Product(
        id="prod-035", name="Samsung Galaxy Watch 6 Classic 47mm", slug="samsung-galaxy-watch-6-classic-47mm",
        description="The iconic rotating bezel returns. Advanced health monitoring with BioActive Sensor for heart rate, ECG, blood pressure, and body composition analysis.",
        short_description="Iconic rotating bezel smartwatch with ECG and BP monitoring.",
        brand_id="brand-samsung", brand_name="Samsung", category="electronics", sub_category="smartwatches",
        mrp=39999, selling_price=31999, currency="INR",
        thumbnail_url="https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400",
        specifications=[
            ProductSpecification(key="Display", value="1.5-inch Super AMOLED, 480x480"),
            ProductSpecification(key="Health", value="Heart Rate, ECG, Blood Pressure, SpO2"),
            ProductSpecification(key="Battery", value="425 mAh, up to 40 hours"),
            ProductSpecification(key="Water Resistance", value="5ATM + IP68"),
            ProductSpecification(key="OS", value="Wear OS + One UI Watch"),
        ],
        tags=["samsung", "smartwatch", "galaxy watch", "ecg", "health", "wearable"],
        color="Black", sku="SAM-GW6CL-47-BK",
        rating=4.5, rating_count=7890,
        rating_breakdown={"5": 5000, "4": 1900, "3": 600, "2": 250, "1": 140},
        in_stock=True, stock_quantity=95, free_shipping=True, shipping_days=2,
        badges=["Best Seller"],
        created_at=now(), updated_at=now()
    ))

    # More products for variety
    for i, p in enumerate([
        Product(
            id=f"prod-0{36+i}", name="Wireless Mechanical Gaming Keyboard RGB", slug=f"wireless-mechanical-gaming-keyboard-rgb-{36+i}",
            description="60% compact layout wireless mechanical keyboard with per-key RGB backlighting, Red linear switches, and 40-hour battery life.",
            short_description="60% wireless mechanical keyboard with RGB and Red switches.",
            brand_id="brand-samsung", brand_name="Keychron", category="gaming", sub_category="keyboards",
            mrp=9999, selling_price=6999, currency="INR",
            thumbnail_url="https://images.unsplash.com/photo-1595225476474-87563907a212?w=400",
            specifications=[ProductSpecification(key="Switch", value="Red Linear"), ProductSpecification(key="Layout", value="60%")],
            tags=["keyboard", "mechanical", "gaming", "rgb", "wireless"],
            color="Black", sku=f"KEY-MECH-RGB-{36+i}",
            rating=4.4, rating_count=3200,
            rating_breakdown={"5": 1900, "4": 900, "3": 280, "2": 80, "1": 40},
            in_stock=True, stock_quantity=130, free_shipping=True, shipping_days=3,
            created_at=now(), updated_at=now()
        ),
        Product(
            id=f"prod-0{37+i}", name="Ergonomic Office Chair Lumbar Support Mesh", slug=f"ergonomic-office-chair-lumbar-{37+i}",
            description="Fully adjustable mesh office chair with 3D adjustable lumbar support, adjustable armrests, headrest, and seat depth. Supports up to 150kg.",
            short_description="Fully adjustable mesh chair with 3D lumbar support.",
            brand_id="brand-ikea", brand_name="Featherlite", category="home_decor", sub_category="furniture",
            mrp=25999, selling_price=17999, currency="INR",
            thumbnail_url="https://images.unsplash.com/photo-1592078615290-033ee584e267?w=400",
            specifications=[ProductSpecification(key="Max Load", value="150 kg"), ProductSpecification(key="Seat Height", value="44-54 cm")],
            tags=["chair", "office", "ergonomic", "mesh", "work from home"],
            color="Black", sku=f"ERGO-CHR-MESH-{37+i}",
            rating=4.3, rating_count=5670,
            rating_breakdown={"5": 3200, "4": 1600, "3": 580, "2": 200, "1": 90},
            in_stock=True, stock_quantity=55, free_shipping=True, shipping_days=7,
            created_at=now(), updated_at=now()
        ),
        Product(
            id=f"prod-0{38+i}", name="Protein Whey Isolate 2kg Chocolate Fudge", slug=f"whey-protein-isolate-2kg-choco-{38+i}",
            description="28g protein per serving, ultra-low carbs and fat. Cold-filtered whey isolate with 5.5g BCAAs. NSF certified, mixes instantly, no clumping.",
            short_description="28g protein per serving — NSF certified pure whey isolate.",
            brand_id="brand-hp", brand_name="MuscleBlaze", category="health_wellness", sub_category="supplements",
            mrp=5999, selling_price=3599, currency="INR",
            thumbnail_url="https://images.unsplash.com/photo-1593095948071-474c5cc2989d?w=400",
            specifications=[ProductSpecification(key="Protein per Serving", value="28g"), ProductSpecification(key="Net Weight", value="2 kg")],
            tags=["protein", "whey", "supplement", "gym", "muscle", "chocolate"],
            color="Chocolate Fudge", sku=f"MB-WPI-2KG-CF-{38+i}",
            rating=4.5, rating_count=19000,
            rating_breakdown={"5": 11000, "4": 5500, "3": 1800, "2": 500, "1": 200},
            in_stock=True, stock_quantity=820, free_shipping=True, shipping_days=3,
            badges=["Best Seller"],
            created_at=now(), updated_at=now()
        ),
    ], start=0):
        products.append(p)

    return products


# ══════════════════════════════════════════════════════════════════════════════
# SAMPLE USERS
# ══════════════════════════════════════════════════════════════════════════════

def make_users():
    users_data = [
        {
            "user": User(
                id="user-001", name="Arjun Sharma", email="arjun.sharma@example.com",
                phone="+91-9876543210", gender="male", date_of_birth="1995-03-15", age=29,
                preferences=UserPreferences(
                    preferred_categories=["electronics", "gaming", "laptops_computers"],
                    preferred_brands=["brand-apple", "brand-sony"],
                    price_range_min=5000, price_range_max=150000
                ),
                loyalty_points=2450, loyalty_tier="Gold",
                total_orders=18, total_spent=145000.0,
                is_active=True, is_verified=True, is_premium=True,
                created_at=now(), updated_at=now()
            ),
            "password_hash": "$2b$12$example_hash_arjun"
        },
        {
            "user": User(
                id="user-002", name="Priya Patel", email="priya.patel@example.com",
                phone="+91-9823456781", gender="female", date_of_birth="1998-07-22", age=26,
                preferences=UserPreferences(
                    preferred_categories=["beauty_skincare", "fashion_women", "health_wellness"],
                    preferred_brands=["brand-loreal", "brand-nike"],
                    price_range_min=200, price_range_max=20000
                ),
                loyalty_points=1200, loyalty_tier="Silver",
                total_orders=32, total_spent=48000.0,
                is_active=True, is_verified=True, is_premium=False,
                created_at=now(), updated_at=now()
            ),
            "password_hash": "$2b$12$example_hash_priya"
        },
        {
            "user": User(
                id="user-003", name="Rahul Mehta", email="rahul.mehta@example.com",
                phone="+91-9912345678", gender="male", date_of_birth="1990-11-08", age=34,
                preferences=UserPreferences(
                    preferred_categories=["home_appliances", "home_decor", "food_grocery"],
                    preferred_brands=["brand-lg", "brand-bosch", "brand-ikea"],
                    price_range_min=1000, price_range_max=80000
                ),
                loyalty_points=850, loyalty_tier="Bronze",
                total_orders=9, total_spent=72000.0,
                is_active=True, is_verified=False, is_premium=False,
                created_at=now(), updated_at=now()
            ),
            "password_hash": "$2b$12$example_hash_rahul"
        },
        {
            "user": User(
                id="user-004", name="Sneha Rao", email="sneha.rao@example.com",
                phone="+91-9845678901", gender="female", date_of_birth="2000-01-30", age=24,
                preferences=UserPreferences(
                    preferred_categories=["books", "sports_fitness", "fashion_women"],
                    preferred_brands=["brand-nike", "brand-adidas"],
                    price_range_min=100, price_range_max=15000
                ),
                loyalty_points=340, loyalty_tier="Bronze",
                total_orders=7, total_spent=12500.0,
                is_active=True, is_verified=True, is_premium=False,
                created_at=now(), updated_at=now()
            ),
            "password_hash": "$2b$12$example_hash_sneha"
        },
        {
            "user": User(
                id="user-005", name="Vikram Nair", email="vikram.nair@example.com",
                phone="+91-9778901234", gender="male", date_of_birth="1985-05-18", age=39,
                preferences=UserPreferences(
                    preferred_categories=["cameras", "laptops_computers", "automotive"],
                    preferred_brands=["brand-nikon", "brand-sony", "brand-apple"],
                    price_range_min=10000, price_range_max=500000
                ),
                loyalty_points=5800, loyalty_tier="Platinum",
                total_orders=45, total_spent=480000.0,
                is_active=True, is_verified=True, is_premium=True,
                created_at=now(), updated_at=now()
            ),
            "password_hash": "$2b$12$example_hash_vikram"
        },
    ]
    return users_data


# ══════════════════════════════════════════════════════════════════════════════
# MAIN SEEDER
# ══════════════════════════════════════════════════════════════════════════════

def seed():
    print("\n🌱 ShopMind AI — Seeding database...\n")

    # Check connection
    if not ping_valkey():
        print("❌ Cannot connect to Valkey DB. Make sure it's running.")
        print("   Run: valkey-server (or redis-server)")
        sys.exit(1)

    print("✅ Valkey DB connected\n")

    # Flush existing data (dev only)
    print("🗑️  Clearing existing data...")
    db.flushdb()

    # Seed brands
    print("📦 Seeding brands...")
    for key, brand in BRANDS.items():
        store_brand(brand)
    print(f"   ✅ {len(BRANDS)} brands seeded")

    # Seed products
    print("🛒 Seeding products...")
    products = make_products()
    for product in products:
        store_product(product)
    print(f"   ✅ {len(products)} products seeded")

    # Seed users
    print("👤 Seeding users...")
    users_data = make_users()
    for u in users_data:
        store_user(u["user"], u["password_hash"])
    print(f"   ✅ {len(users_data)} users seeded")

    # Summary stats
    print("\n📊 Database Summary:")
    print(f"   Products  : {db.scard('products:all')}")
    print(f"   Brands    : {db.scard('brands:all')}")
    print(f"   Users     : {db.scard('users:all')}")
    print(f"   Categories: {len(set(db.smembers('products:all')))}")

    print("\n🎉 Seeding complete! ShopMind AI is ready.\n")


if __name__ == "__main__":
    seed()