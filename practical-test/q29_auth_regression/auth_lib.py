import base64
import hashlib
import hmac
import json
import time

SECRET = b"dev-secret"
ROLE_LEVEL = {"user": 1, "manager": 2, "admin": 3}


class AuthError(Exception):
    pass


def _b64(raw):
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _unb64(text):
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def _sign(body, secret):
    return _b64(hmac.new(secret, body.encode(), hashlib.sha256).digest())


def issue_token(user_id, role="user", ttl=900, now=None, secret=SECRET):
    now = int(time.time() if now is None else now)
    payload = {"sub": user_id, "role": role, "iat": now, "exp": now + ttl}
    body = _b64(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode())
    return f"{body}.{_sign(body, secret)}"


def verify_token(token, now=None, secret=SECRET):
    now = int(time.time() if now is None else now)
    try:
        body, sig = token.split(".")
        payload = json.loads(_unb64(body))
    except (ValueError, AttributeError):
        raise AuthError("malformed")
    if not hmac.compare_digest(sig, _sign(body, secret)):
        raise AuthError("bad_signature")
    if payload["exp"] <= now:
        raise AuthError("expired")
    return payload


def require_role(payload, required):
    if ROLE_LEVEL.get(payload.get("role"), 0) < ROLE_LEVEL[required]:
        raise AuthError("forbidden")
