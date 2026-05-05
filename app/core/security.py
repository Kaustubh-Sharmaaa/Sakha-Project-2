from datetime import datetime, timedelta
from typing import Optional
import os

ALGORITHM = "HS256"
SECRET_KEY = os.getenv("SECRET_KEY", "sakha-secret-key-change-in-production-2024")


def create_access_token(data: dict, expires_delta: timedelta = timedelta(hours=24)) -> str:
    to_encode = data.copy()
    to_encode["exp"] = datetime.utcnow() + expires_delta
    to_encode["type"] = "access"
    return _create_jwt(to_encode)


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    to_encode["exp"] = datetime.utcnow() + timedelta(days=7)
    to_encode["type"] = "refresh"
    return _create_jwt(to_encode)


def _create_jwt(data: dict) -> str:
    import jwt
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    import jwt
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None


def get_password_hash(password: str) -> str:
    import bcrypt
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    import bcrypt
    try:
        return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())
    except Exception:
        return False
