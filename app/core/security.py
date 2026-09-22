"""Security utilities: password hashing and JWT token management.

Uses Passlib with bcrypt for password hashing and PyJWT for
access-token creation and verification.
"""

from datetime import UTC
from datetime import datetime
from datetime import timedelta
from typing import Any

import jwt
from passlib.context import CryptContext

from .config import ACCESS_TOKEN_EXPIRE_MINUTES
from .config import ALGORITHM
from .config import SECRET_KEY

# Passlib password context — bcrypt is the default scheme.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt.

    Args:
        password: The plaintext password to hash.

    Returns:
        The bcrypt-hashed password string.
    """
    return str(pwd_context.hash(password))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a stored bcrypt hash.

    Args:
        plain_password: The plaintext password to check.
        hashed_password: The stored bcrypt hash to compare against.

    Returns:
        ``True`` if the password matches, ``False`` otherwise.
    """
    return bool(pwd_context.verify(plain_password, hashed_password))


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """Encode a JWT access token from the given payload.

    Args:
        data: The claims to include in the token payload.
        expires_delta: How long the token is valid. Defaults to
            ``ACCESS_TOKEN_EXPIRE_MINUTES``.

    Returns:
        The encoded JWT string.
    """
    to_encode = data.copy()
    expire = datetime.now(UTC) + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "iat": datetime.now(UTC)})
    return str(jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM))


def decode_access_token(token: str) -> dict[str, Any] | None:
    """Decode and validate a JWT access token.

    Args:
        token: The JWT string to decode.

    Returns:
        The decoded payload dict if the token is valid, ``None`` otherwise
        (expired, malformed, or invalid signature).
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None
