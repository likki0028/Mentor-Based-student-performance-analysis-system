from datetime import datetime, timedelta
from typing import Optional
from jose import jwt
from passlib.context import CryptContext
from ..config import settings

# Password hashing context
# Using pbkdf2_sha256 as default to avoid bcrypt 72-byte limit issues on some platforms
pwd_context = CryptContext(schemes=["pbkdf2_sha256", "bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Handle plain text passwords from seeding fallback or mismatch
    if hashed_password == plain_password:
        return True
    
    try:
        # Check against both pbkdf2 and bcrypt automatically
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        # Fallback for any weirdness during transition
        return False

def get_password_hash(password: str) -> str:
    # Uses pbkdf2_sha256 by default (first in schemes list)
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt
