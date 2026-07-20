"""Password hashing and JWT lifecycle helpers."""

import base64
import hashlib
import hmac
import os
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

ITERATIONS = 600_000


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERATIONS)
    salt_encoded = base64.b64encode(salt).decode()
    digest_encoded = base64.b64encode(digest).decode()
    return f"pbkdf2_sha256${ITERATIONS}${salt_encoded}${digest_encoded}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt_b64, digest_b64 = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), base64.b64decode(salt_b64), int(iterations)
        )
        return hmac.compare_digest(digest, base64.b64decode(digest_b64))
    except (ValueError, TypeError):
        return False


def validate_password(password: str) -> list[str]:
    errors = []
    checks = [
        (len(password) >= 12, "contain at least 12 characters"),
        (any(c.islower() for c in password), "contain a lowercase letter"),
        (any(c.isupper() for c in password), "contain an uppercase letter"),
        (any(c.isdigit() for c in password), "contain a number"),
        (any(not c.isalnum() for c in password), "contain a symbol"),
    ]
    errors.extend(message for passed, message in checks if not passed)
    return errors


def create_token(
    *,
    subject: str,
    role: str,
    secret: str,
    minutes: int,
    token_type: str,
    family_id: str | None = None,
) -> tuple[str, dict[str, Any]]:
    now = datetime.now(UTC)
    claims: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "type": token_type,
        "jti": str(uuid.uuid4()),
        "iat": now,
        "nbf": now,
        "exp": now + timedelta(minutes=minutes),
    }
    if family_id:
        claims["family_id"] = family_id
    return jwt.encode(claims, secret, algorithm="HS256"), claims


def decode_token(token: str, secret: str, *, verify_exp: bool = True) -> dict[str, Any]:
    return jwt.decode(token, secret, algorithms=["HS256"], options={"verify_exp": verify_exp})


def hash_jti(jti: str) -> str:
    return hashlib.sha256(jti.encode()).hexdigest()
