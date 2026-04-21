import valkey
from app.core.config import get_settings

settings = get_settings()

_pool = valkey.ConnectionPool(
    host=settings.valkey_host,
    port=settings.valkey_port,
    password=settings.valkey_password if settings.valkey_password.strip() else None,  # ← fix
    db=settings.valkey_db,
    decode_responses=True,
    max_connections=20,
    socket_timeout=5,
    socket_connect_timeout=5,
    retry_on_timeout=True,
)


def get_valkey() -> valkey.Valkey:
    return valkey.Valkey(connection_pool=_pool)


def ping_valkey() -> bool:
    try:
        return get_valkey().ping()
    except valkey.ValkeyError:
        return False