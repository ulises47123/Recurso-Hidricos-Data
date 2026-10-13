import hashlib
import secrets
import base64
import hmac
from datetime import datetime, timezone

def hash_password(password: str) -> str:
    """
    Hashea una contraseña usando PBKDF2-HMAC-SHA256 con salt aleatorio de 16 bytes
    y 600,000 iteraciones en formato pbkdf2$<iter>$<salt_b64>$<hash_b64>.
    """
    salt = secrets.token_bytes(16)
    salt_b64 = base64.b64encode(salt).decode('ascii')
    hash_bytes = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 600_000)
    hash_b64 = base64.b64encode(hash_bytes).decode('ascii')
    return f"pbkdf2$600000${salt_b64}${hash_b64}"

def verify_password(password: str, stored_hash: str) -> bool:
    """
    Verifica una contraseña contra un hash almacenado.
    Soporta formato pbkdf2$ y fallback a comparación segura en texto plano para hashes antiguos.
    """
    if not stored_hash:
        return False

    if stored_hash.startswith("pbkdf2$"):
        parts = stored_hash.split("$")
        if len(parts) != 4:
            return False
        _, iter_str, salt_b64, hash_b64 = parts
        try:
            iterations = int(iter_str)
            salt = base64.b64decode(salt_b64.encode('ascii'))
            computed_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations)
            computed_b64 = base64.b64encode(computed_hash).decode('ascii')
            return hmac.compare_digest(hash_b64, computed_b64)
        except Exception:
            return False
    else:
        # Texto plano (antiguo)
        return hmac.compare_digest(stored_hash, password)

def generar_token_sesion() -> str:
    """Genera un token seguro de 256 bits (32 bytes urlsafe)."""
    return secrets.token_urlsafe(32)
