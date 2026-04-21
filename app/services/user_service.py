import json, uuid
from typing import Optional
from datetime import datetime
from app.core.database import get_valkey
from app.core.security import hash_password, verify_password
from app.core.config import get_settings
from app.models.schemas import User, UserCreate, UserUpdate, UserPreferences, Address, AddressCreate

settings = get_settings()

def _key(uid): return f"user:{uid}"

def _serialize(u: User) -> dict:
    return {
        "id": u.id, "name": u.name, "email": u.email,
        "phone": u.phone or "", "avatar_url": u.avatar_url or "",
        "gender": u.gender or "", "date_of_birth": u.date_of_birth or "",
        "age": str(u.age or ""),
        "preferences": u.preferences.model_dump_json(),
        "loyalty_points": str(u.loyalty_points), "loyalty_tier": u.loyalty_tier,
        "total_orders": str(u.total_orders), "total_spent": str(u.total_spent),
        "avg_order_value": str(u.avg_order_value),
        "last_login": u.last_login or "",
        "is_active": str(u.is_active), "is_verified": str(u.is_verified),
        "is_premium": str(u.is_premium),
        "created_at": u.created_at, "updated_at": u.updated_at,
    }

def _deserialize(raw: dict) -> User:
    try:
        prefs = UserPreferences(**json.loads(raw.get("preferences", "{}")))
    except Exception:
        prefs = UserPreferences()
    return User(
        id=raw["id"], name=raw["name"], email=raw["email"],
        phone=raw.get("phone") or None, avatar_url=raw.get("avatar_url") or None,
        gender=raw.get("gender") or None, date_of_birth=raw.get("date_of_birth") or None,
        age=int(raw["age"]) if raw.get("age") else None,
        preferences=prefs,
        loyalty_points=int(raw.get("loyalty_points", 0)),
        loyalty_tier=raw.get("loyalty_tier", "Bronze"),
        total_orders=int(raw.get("total_orders", 0)),
        total_spent=float(raw.get("total_spent", 0)),
        avg_order_value=float(raw.get("avg_order_value", 0)),
        last_login=raw.get("last_login") or None,
        is_active=raw.get("is_active", "True") == "True",
        is_verified=raw.get("is_verified", "False") == "True",
        is_premium=raw.get("is_premium", "False") == "True",
        created_at=raw.get("created_at", datetime.utcnow().isoformat()),
        updated_at=raw.get("updated_at", datetime.utcnow().isoformat()),
    )

def register_user(data: UserCreate) -> tuple[User, str]:
    db = get_valkey()
    if db.exists(f"user:email:{data.email}"):
        return None, "Email already registered"
    uid = f"user-{str(uuid.uuid4())[:8]}"
    now = datetime.utcnow().isoformat()
    user = User(id=uid, name=data.name, email=data.email,
                phone=data.phone, gender=data.gender, date_of_birth=data.date_of_birth,
                preferences=data.preferences, created_at=now, updated_at=now)
    mapping = _serialize(user)
    mapping["password_hash"] = hash_password(data.password)
    db.hset(_key(uid), mapping=mapping)
    db.set(f"user:email:{data.email}", uid)
    db.sadd("users:all", uid)
    return user, ""

def authenticate_user(email: str, password: str) -> tuple[Optional[User], str]:
    db  = get_valkey()
    uid = db.get(f"user:email:{email}")
    if not uid: return None, "No account found with that email"
    raw = db.hgetall(_key(uid))
    if not raw: return None, "User data not found"
    if not verify_password(password, raw.get("password_hash", "")):
        return None, "Incorrect password"
    now = datetime.utcnow().isoformat()
    db.hset(_key(uid), mapping={"last_login": now, "updated_at": now})
    raw["last_login"] = now
    return _deserialize(raw), ""

def save_refresh_token(user_id: str, token: str):
    db  = get_valkey()
    ttl = settings.refresh_token_expire_days * 86400
    db.setex(f"session:refresh:{token}", ttl, user_id)

def invalidate_refresh_token(token: str):
    get_valkey().delete(f"session:refresh:{token}")

def verify_refresh_token(token: str) -> Optional[str]:
    return get_valkey().get(f"session:refresh:{token}")

def get_user(uid: str) -> Optional[User]:
    db  = get_valkey()
    raw = db.hgetall(_key(uid))
    return _deserialize(raw) if raw else None

def get_user_by_email(email: str) -> Optional[User]:
    db  = get_valkey()
    uid = db.get(f"user:email:{email}")
    return get_user(uid) if uid else None

def get_all_users(page=1, per_page=20):
    db  = get_valkey()
    ids = list(db.smembers("users:all"))
    users = [u for uid in ids if (u := get_user(uid))]
    total = len(users)
    start = (page - 1) * per_page
    return users[start:start + per_page], total

def update_user(uid: str, data: UserUpdate) -> Optional[User]:
    db = get_valkey()
    if not db.exists(_key(uid)): return None
    updates = {"updated_at": datetime.utcnow().isoformat()}
    if data.name:          updates["name"]          = data.name
    if data.phone:         updates["phone"]         = data.phone
    if data.avatar_url:    updates["avatar_url"]    = data.avatar_url
    if data.gender:        updates["gender"]        = data.gender
    if data.date_of_birth: updates["date_of_birth"] = data.date_of_birth
    if data.preferences:   updates["preferences"]   = data.preferences.model_dump_json()
    db.hset(_key(uid), mapping=updates)
    return get_user(uid)

def change_password(uid: str, old_pw: str, new_pw: str) -> tuple[bool, str]:
    db  = get_valkey()
    raw = db.hgetall(_key(uid))
    if not raw: return False, "User not found"
    if not verify_password(old_pw, raw.get("password_hash", "")):
        return False, "Current password is incorrect"
    db.hset(_key(uid), mapping={
        "password_hash": hash_password(new_pw),
        "updated_at": datetime.utcnow().isoformat(),
    })
    return True, "Password updated successfully"

def deactivate_user(uid: str) -> bool:
    db = get_valkey()
    if not db.exists(_key(uid)): return False
    db.hset(_key(uid), mapping={"is_active": "False", "updated_at": datetime.utcnow().isoformat()})
    return True

def _loyalty_tier(points: int) -> str:
    if points >= 10000: return "Platinum"
    if points >= 5000:  return "Gold"
    if points >= 1000:  return "Silver"
    return "Bronze"

def add_loyalty_points(uid: str, points: int) -> int:
    db  = get_valkey()
    raw = db.hgetall(_key(uid))
    if not raw: return 0
    new_total = int(raw.get("loyalty_points", 0)) + points
    db.hset(_key(uid), mapping={
        "loyalty_points": str(new_total),
        "loyalty_tier": _loyalty_tier(new_total),
        "updated_at": datetime.utcnow().isoformat(),
    })
    return new_total

def _addr_key(uid): return f"user:{uid}:addresses"

def get_addresses(uid: str) -> list[Address]:
    db = get_valkey()
    return [Address(**json.loads(r)) for r in db.lrange(_addr_key(uid), 0, -1)]

def add_address(uid: str, data: AddressCreate) -> Address:
    db   = get_valkey()
    addr = Address(id=f"addr-{str(uuid.uuid4())[:8]}", **data.model_dump())
    if addr.is_default:
        existing = get_addresses(uid)
        updated  = [a.model_copy(update={"is_default": False}).model_dump_json() for a in existing]
        if updated:
            db.delete(_addr_key(uid))
            for a in updated: db.rpush(_addr_key(uid), a)
    db.rpush(_addr_key(uid), addr.model_dump_json())
    return addr

def delete_address(uid: str, addr_id: str) -> bool:
    db       = get_valkey()
    existing = get_addresses(uid)
    new_list = [a for a in existing if a.id != addr_id]
    if len(new_list) == len(existing): return False
    db.delete(_addr_key(uid))
    for a in new_list: db.rpush(_addr_key(uid), a.model_dump_json())
    return True

def set_default_address(uid: str, addr_id: str) -> bool:
    db       = get_valkey()
    existing = get_addresses(uid)
    found    = any(a.id == addr_id for a in existing)
    if not found: return False
    db.delete(_addr_key(uid))
    for a in existing:
        a.is_default = (a.id == addr_id)
        db.rpush(_addr_key(uid), a.model_dump_json())
    return True