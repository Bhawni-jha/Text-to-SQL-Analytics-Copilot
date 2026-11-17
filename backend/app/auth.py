"""Small dependency-free password and bearer-session implementation."""
import base64
import hashlib
import hmac
import json
import secrets
import time

from fastapi import Header, HTTPException

from .config import settings

_ITERATIONS = 310_000


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _ITERATIONS)
    enc = lambda value: base64.urlsafe_b64encode(value).decode().rstrip("=")
    return f"pbkdf2_sha256${_ITERATIONS}${enc(salt)}${enc(digest)}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, rounds, salt, expected = encoded.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        raw_salt = base64.urlsafe_b64decode(salt + "=" * (-len(salt) % 4))
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), raw_salt, int(rounds))
        return hmac.compare_digest(base64.urlsafe_b64encode(actual).decode().rstrip("="), expected)
    except (ValueError, TypeError):
        return False


def create_session(user_id: int) -> str:
    payload = {"sub": user_id, "exp": int(time.time()) + settings.session_ttl_seconds}
    body = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).decode().rstrip("=")
    signature = hmac.new(settings.auth_secret.encode(), body.encode(), hashlib.sha256).digest()
    return body + "." + base64.urlsafe_b64encode(signature).decode().rstrip("=")


def user_from_token(authorization: str | None) -> int | None:
    if not authorization:
        return None
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Bearer authentication required")
    try:
        body, signature = authorization[7:].split(".", 1)
        expected = hmac.new(settings.auth_secret.encode(), body.encode(), hashlib.sha256).digest()
        supplied = base64.urlsafe_b64decode(signature + "=" * (-len(signature) % 4))
        if not hmac.compare_digest(expected, supplied):
            raise ValueError
        payload = json.loads(base64.urlsafe_b64decode(body + "=" * (-len(body) % 4)))
        if int(payload["exp"]) < time.time():
            raise ValueError
        return int(payload["sub"])
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        raise HTTPException(401, "Invalid or expired session")


def current_user(authorization: str | None = Header(default=None)) -> int | None:
    return user_from_token(authorization)


def required_user(authorization: str | None = Header(default=None)) -> int:
    user_id = user_from_token(authorization)
    if user_id is None:
        raise HTTPException(401, "Authentication required")
    return user_id
