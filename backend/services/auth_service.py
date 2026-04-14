"""Auth service: password hashing + JWT creation/verification."""
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

# ── Config ────────────────────────────────────────────────────
SECRET_KEY: str = os.getenv("JWT_SECRET", "changeme-in-production")
ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "10080"))  # 7 days

bearer_scheme = HTTPBearer()


# ── Password helpers ──────────────────────────────────────────

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


# ── JWT helpers ───────────────────────────────────────────────

def create_jwt(user_id: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "role": role,
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_jwt(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


# ── FastAPI dependency ────────────────────────────────────────

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """Returns {'user_id': ..., 'role': ...} or raises 401."""
    return decode_jwt(credentials.credentials)


def require_role(role: str):
    """Factory: dependency that enforces a specific role."""
    def _check(user: dict = Depends(get_current_user)) -> dict:
        if user.get("role") != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access restricted to {role}s",
            )
        return user
    return _check


require_student = require_role("student")
require_recruiter = require_role("recruiter")
