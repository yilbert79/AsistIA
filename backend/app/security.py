import hashlib
import hmac
import secrets
from datetime import timedelta
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app.models import AdminUser

bearer = HTTPBearer(auto_error=False)
_serializer = URLSafeTimedSerializer(settings.secret_key, salt="asistia-auth-v1")
_ITERATIONS = 310_000

def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _ITERATIONS)
    return f"{salt.hex()}${digest.hex()}"

def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, digest_hex = stored.split("$", 1)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), _ITERATIONS)
        return hmac.compare_digest(digest.hex(), digest_hex)
    except (ValueError, TypeError):
        return False

def create_access_token(user_id: int) -> str:
    return _serializer.dumps({"sub": user_id})

def get_current_admin(credentials: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)) -> AdminUser:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Inicia sesión para continuar.")
    try:
        payload = _serializer.loads(credentials.credentials, max_age=settings.token_ttl_minutes * 60)
        user_id = int(payload["sub"])
    except (BadSignature, SignatureExpired, KeyError, TypeError, ValueError):
        raise HTTPException(status_code=401, detail="La sesión no es válida o expiró.")
    user = db.get(AdminUser, user_id)
    if not user or not user.active:
        raise HTTPException(status_code=401, detail="La cuenta no está activa.")
    return user

def require_roles(*roles: str):
    def check(user: AdminUser = Depends(get_current_admin)) -> AdminUser:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="No tienes permiso para esta operación.")
        return user
    return check
