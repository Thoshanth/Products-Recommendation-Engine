from __future__ import annotations
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


class ProductCategory(str, Enum):
    ELECTRONICS        = "electronics"
    FASHION_MEN        = "fashion_men"
    FASHION_WOMEN      = "fashion_women"
    FASHION_KIDS       = "fashion_kids"
    BOOKS              = "books"
    HOME_APPLIANCES    = "home_appliances"
    HOME_DECOR         = "home_decor"
    SPORTS_FITNESS     = "sports_fitness"
    BEAUTY_SKINCARE    = "beauty_skincare"
    HEALTH_WELLNESS    = "health_wellness"
    FOOD_GROCERY       = "food_grocery"
    TOYS_GAMES         = "toys_games"
    AUTOMOTIVE         = "automotive"
    JEWELLERY          = "jewellery"
    MOBILE_ACCESSORIES = "mobile_accessories"
    LAPTOPS_COMPUTERS  = "laptops_computers"
    CAMERAS            = "cameras"
    AUDIO              = "audio"
    GAMING             = "gaming"
    PET_SUPPLIES       = "pet_supplies"


class ProductCondition(str, Enum):
    NEW           = "new"
    REFURBISHED   = "refurbished"
    USED_LIKE_NEW = "used_like_new"
    USED_GOOD     = "used_good"


class OrderStatus(str, Enum):
    PENDING          = "pending"
    CONFIRMED        = "confirmed"
    PROCESSING       = "processing"
    SHIPPED          = "shipped"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED        = "delivered"
    CANCELLED        = "cancelled"
    RETURNED         = "returned"
    REFUNDED         = "refunded"


class PaymentMethod(str, Enum):
    CREDIT_CARD = "credit_card"
    DEBIT_CARD  = "debit_card"
    UPI         = "upi"
    NET_BANKING = "net_banking"
    WALLET      = "wallet"
    COD         = "cash_on_delivery"
    EMI         = "emi"


class PaymentStatus(str, Enum):
    PENDING  = "pending"
    PAID     = "paid"
    FAILED   = "failed"
    REFUNDED = "refunded"


class UserGender(str, Enum):
    MALE       = "male"
    FEMALE     = "female"
    NON_BINARY = "non_binary"
    PREFER_NOT = "prefer_not_to_say"


class BehaviorEventType(str, Enum):
    VIEW            = "view"
    CLICK           = "click"
    SEARCH          = "search"
    ADD_TO_CART     = "add_to_cart"
    REMOVE_CART     = "remove_from_cart"
    ADD_WISHLIST    = "add_to_wishlist"
    REMOVE_WISHLIST = "remove_from_wishlist"
    PURCHASE        = "purchase"
    REVIEW          = "review"
    SHARE           = "share"
    RETURN          = "return"


class DiscountType(str, Enum):
    PERCENTAGE = "percentage"
    FLAT       = "flat"


class ShippingMethod(str, Enum):
    STANDARD  = "standard"
    EXPRESS   = "express"
    OVERNIGHT = "overnight"
    PICKUP    = "pickup"


class LoyaltyTier(str, Enum):
    BRONZE   = "Bronze"
    SILVER   = "Silver"
    GOLD     = "Gold"
    PLATINUM = "Platinum"


# ── Brand ──────────────────────────────────────────────────────────────────────

class Brand(BaseModel):
    id:           str
    name:         str
    slug:         str
    logo_url:     Optional[str] = None
    website:      Optional[str] = None
    country:      str
    founded_year: Optional[int] = None
    description:  Optional[str] = None
    is_verified:  bool = False
    created_at:   str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class BrandCreate(BaseModel):
    name:         str
    country:      str
    logo_url:     Optional[str] = None
    website:      Optional[str] = None
    founded_year: Optional[int] = None
    description:  Optional[str] = None
    is_verified:  bool = False


# ── Product ────────────────────────────────────────────────────────────────────

class ProductImage(BaseModel):
    url:        str
    alt_text:   Optional[str] = None
    is_primary: bool = False


class ProductSpecification(BaseModel):
    key:   str
    value: str
    unit:  Optional[str] = None


class ProductDimensions(BaseModel):
    length_cm: float
    width_cm:  float
    height_cm: float
    weight_kg: float


class Offer(BaseModel):
    offer_id:        str
    title:           str
    description:     str
    discount_type:   DiscountType
    discount_value:  float
    min_order_value: Optional[float] = None
    valid_until:     Optional[str] = None
    coupon_code:     Optional[str] = None


class Product(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    id:                str
    name:              str
    slug:              str
    description:       str
    short_description: str
    brand_id:          str
    brand_name:        str
    category:          ProductCategory
    sub_category:      Optional[str] = None
    condition:         ProductCondition = ProductCondition.NEW
    mrp:               float
    selling_price:     float
    discount_pct:      float = 0.0
    currency:          str = "INR"
    images:            List[ProductImage] = []
    thumbnail_url:     Optional[str] = None
    video_url:         Optional[str] = None
    specifications:    List[ProductSpecification] = []
    dimensions:        Optional[ProductDimensions] = None
    tags:              List[str] = []
    color:             Optional[str] = None
    size_options:      List[str] = []
    sku:               str = ""
    model_number:      Optional[str] = None
    rating:            float = Field(ge=0.0, le=5.0, default=0.0)
    rating_count:      int = 0
    rating_breakdown:  Dict[str, int] = Field(
        default_factory=lambda: {"5": 0, "4": 0, "3": 0, "2": 0, "1": 0}
    )
    in_stock:          bool = True
    stock_quantity:    int = 0
    shipping_methods:  List[str] = ["standard"]
    free_shipping:     bool = False
    shipping_days:     int = 5
    offers:            List[Offer] = []
    badges:            List[str] = []
    is_featured:       bool = False
    is_active:         bool = True
    embedding_id:      Optional[str] = None
    created_at:        str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at:        str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ProductCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    name:              str
    description:       str
    short_description: str
    brand_id:          str
    brand_name:        str
    category:          ProductCategory
    sub_category:      Optional[str] = None
    condition:         ProductCondition = ProductCondition.NEW
    mrp:               float = Field(gt=0)
    selling_price:     float = Field(gt=0)
    currency:          str = "INR"
    images:            List[ProductImage] = []
    thumbnail_url:     Optional[str] = None
    specifications:    List[ProductSpecification] = []
    dimensions:        Optional[ProductDimensions] = None
    tags:              List[str] = []
    color:             Optional[str] = None
    size_options:      List[str] = []
    sku:               str = ""
    model_number:      Optional[str] = None
    in_stock:          bool = True
    stock_quantity:    int = 0
    free_shipping:     bool = False
    shipping_days:     int = 5
    badges:            List[str] = []
    is_featured:       bool = False


# ── Inventory ──────────────────────────────────────────────────────────────────

class Inventory(BaseModel):
    product_id:         str
    sku:                str
    quantity:           int
    reserved:           int = 0
    available:          int = 0
    warehouse_location: Optional[str] = None
    reorder_threshold:  int = 10
    last_restocked:     Optional[str] = None
    updated_at:         str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class InventoryUpdate(BaseModel):
    quantity:           int = Field(ge=0)
    warehouse_location: Optional[str] = None
    reorder_threshold:  int = 10


# ── Address & User ─────────────────────────────────────────────────────────────

class Address(BaseModel):
    id:            str
    label:         str = "Home"
    full_name:     str
    phone:         str
    address_line1: str
    address_line2: Optional[str] = None
    city:          str
    state:         str
    pincode:       str
    country:       str = "India"
    is_default:    bool = False
    landmark:      Optional[str] = None
    latitude:      Optional[float] = None
    longitude:     Optional[float] = None


class AddressCreate(BaseModel):
    label:         str = "Home"
    full_name:     str
    phone:         str
    address_line1: str
    address_line2: Optional[str] = None
    city:          str
    state:         str
    pincode:       str
    country:       str = "India"
    is_default:    bool = False
    landmark:      Optional[str] = None


class UserPreferences(BaseModel):
    preferred_categories:  List[str] = []
    preferred_brands:      List[str] = []
    price_range_min:       float = 0.0
    price_range_max:       float = 100000.0
    preferred_language:    str = "en"
    currency:              str = "INR"
    notifications_enabled: bool = True
    email_marketing:       bool = True


class User(BaseModel):
    id:              str
    name:            str
    email:           str
    phone:           Optional[str] = None
    avatar_url:      Optional[str] = None
    gender:          Optional[UserGender] = None
    date_of_birth:   Optional[str] = None
    age:             Optional[int] = None
    preferences:     UserPreferences = Field(default_factory=UserPreferences)
    addresses:       List[Address] = []
    loyalty_points:  int = 0
    loyalty_tier:    str = "Bronze"
    total_orders:    int = 0
    total_spent:     float = 0.0
    avg_order_value: float = 0.0
    last_login:      Optional[str] = None
    is_active:       bool = True
    is_verified:     bool = False
    is_premium:      bool = False
    created_at:      str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at:      str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class UserCreate(BaseModel):
    name:          str
    email:         str
    password:      str = Field(min_length=8, max_length=72)
    phone:         Optional[str] = None
    gender:        Optional[UserGender] = None
    date_of_birth: Optional[str] = None
    preferences:   UserPreferences = Field(default_factory=UserPreferences)


class UserLogin(BaseModel):
    email:    str
    password: str = Field(max_length=72)


class UserUpdate(BaseModel):
    name:          Optional[str] = None
    phone:         Optional[str] = None
    avatar_url:    Optional[str] = None
    gender:        Optional[UserGender] = None
    date_of_birth: Optional[str] = None
    preferences:   Optional[UserPreferences] = None


class TokenPair(BaseModel):
    access_token:  str
    refresh_token: str
    token_type:    str = "bearer"
    expires_in:    int


# ── Review ─────────────────────────────────────────────────────────────────────

class ReviewImage(BaseModel):
    url:     str
    caption: Optional[str] = None


class Review(BaseModel):
    id:                   str
    product_id:           str
    user_id:              str
    user_name:            str
    user_avatar:          Optional[str] = None
    order_id:             Optional[str] = None
    rating:               int = Field(ge=1, le=5)
    title:                str
    body:                 str
    pros:                 List[str] = []
    cons:                 List[str] = []
    images:               List[ReviewImage] = []
    helpful_votes:        int = 0
    not_helpful_votes:    int = 0
    is_verified_purchase: bool = False
    is_featured:          bool = False
    seller_reply:         Optional[str] = None
    created_at:           str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at:           str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ReviewCreate(BaseModel):
    product_id: str
    order_id:   Optional[str] = None
    rating:     int = Field(ge=1, le=5)
    title:      str
    body:       str
    pros:       List[str] = []
    cons:       List[str] = []
    images:     List[ReviewImage] = []


# ── Cart ───────────────────────────────────────────────────────────────────────

class CartItem(BaseModel):
    product_id:     str
    product_name:   str
    thumbnail_url:  Optional[str] = None
    selling_price:  float
    mrp:            float
    quantity:       int = Field(ge=1)
    selected_size:  Optional[str] = None
    selected_color: Optional[str] = None
    subtotal:       float = 0.0


class Cart(BaseModel):
    user_id:         str
    items:           List[CartItem] = []
    total_mrp:       float = 0.0
    total_discount:  float = 0.0
    delivery_charge: float = 0.0
    total_amount:    float = 0.0
    coupon_code:     Optional[str] = None
    coupon_discount: float = 0.0
    item_count:      int = 0
    updated_at:      str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class AddToCart(BaseModel):
    product_id:     str
    quantity:       int = Field(ge=1, default=1)
    selected_size:  Optional[str] = None
    selected_color: Optional[str] = None


# ── Wishlist ───────────────────────────────────────────────────────────────────

class WishlistItem(BaseModel):
    product_id:    str
    product_name:  str
    thumbnail_url: Optional[str] = None
    selling_price: float
    mrp:           float
    in_stock:      bool = True
    added_at:      str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class Wishlist(BaseModel):
    user_id:    str
    items:      List[WishlistItem] = []
    count:      int = 0
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# ── Order ──────────────────────────────────────────────────────────────────────

class OrderItem(BaseModel):
    product_id:     str
    product_name:   str
    brand_name:     str
    thumbnail_url:  Optional[str] = None
    sku:            str
    quantity:       int
    mrp:            float
    selling_price:  float
    subtotal:       float
    selected_size:  Optional[str] = None
    selected_color: Optional[str] = None
    is_reviewed:    bool = False


class OrderTimeline(BaseModel):
    status:      str
    timestamp:   str
    description: str
    location:    Optional[str] = None


class Order(BaseModel):
    id:                  str
    order_number:        str
    user_id:             str
    items:               List[OrderItem]
    total_mrp:           float
    total_discount:      float
    delivery_charge:     float
    coupon_discount:     float = 0.0
    tax_amount:          float = 0.0
    total_amount:        float
    currency:            str = "INR"
    shipping_address:    Address
    shipping_method:     str
    estimated_delivery:  Optional[str] = None
    tracking_id:         Optional[str] = None
    tracking_url:        Optional[str] = None
    payment_method:      str
    payment_status:      str = "pending"
    transaction_id:      Optional[str] = None
    status:              str = "pending"
    timeline:            List[OrderTimeline] = []
    notes:               Optional[str] = None
    cancellation_reason: Optional[str] = None
    created_at:          str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at:          str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    delivered_at:        Optional[str] = None


class OrderCreate(BaseModel):
    shipping_address_id: str
    shipping_method:     str = "standard"
    payment_method:      str
    coupon_code:         Optional[str] = None
    notes:               Optional[str] = None


# ── Behavior ───────────────────────────────────────────────────────────────────

class BehaviorEvent(BaseModel):
    id:            str
    user_id:       str
    event_type:    BehaviorEventType
    product_id:    Optional[str] = None
    category:      Optional[str] = None
    search_query:  Optional[str] = None
    session_id:    str
    device_type:   str = "web"
    duration_secs: Optional[int] = None
    metadata:      Dict[str, Any] = {}
    timestamp:     str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class BehaviorEventCreate(BaseModel):
    event_type:    BehaviorEventType
    product_id:    Optional[str] = None
    category:      Optional[str] = None
    search_query:  Optional[str] = None
    session_id:    str
    device_type:   str = "web"
    duration_secs: Optional[int] = None
    metadata:      Dict[str, Any] = {}


# ── Recommendations ────────────────────────────────────────────────────────────

class RecommendedProduct(BaseModel):
    product:  Product
    score:    float
    reason:   str
    strategy: str


class RecommendationResponse(BaseModel):
    user_id:      Optional[str] = None
    strategy:     str
    products:     List[RecommendedProduct]
    total:        int
    generated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    from_cache:   bool = False


# ── Search ─────────────────────────────────────────────────────────────────────

class SearchFilters(BaseModel):
    category:      Optional[str] = None
    brand_ids:     Optional[List[str]] = None
    min_price:     Optional[float] = None
    max_price:     Optional[float] = None
    min_rating:    Optional[float] = None
    in_stock_only: bool = False
    free_shipping: bool = False
    sort_by:       str = "relevance"


class SearchRequest(BaseModel):
    query:    str
    filters:  SearchFilters = Field(default_factory=SearchFilters)
    page:     int = Field(ge=1, default=1)
    per_page: int = Field(ge=1, le=100, default=20)


class SearchResponse(BaseModel):
    query:           str
    results:         List[Product]
    total:           int
    page:            int
    per_page:        int
    total_pages:     int
    filters_applied: SearchFilters


# ── Generic Responses ──────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status:           str
    valkey_connected: bool
    app_name:         str
    app_version:      str
    environment:      str
    timestamp:        str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class MessageResponse(BaseModel):
    success: bool
    message: str
    data:    Optional[Dict[str, Any]] = None