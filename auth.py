import os
import hmac
import hashlib
import time
import base64
import json
from typing import Optional
from fastapi import Request

AUTH_SECRET = os.environ.get("AUTH_SECRET", "marble_granite_erp_secret_key_2026_adom_secure_key")

# Authorized credentials requested by the user:
# Username: admin, Password: adom0985 (and alias adom0985 / adom0985)
AUTHORIZED_USERS = {
    "admin": "adom0985",
    "adom0985": "adom0985"
}

def authenticate_user(username: str, password: str) -> Optional[str]:
    """Returns canonical username if valid, else None."""
    username = (username or "").strip().lower()
    password = (password or "").strip()
    if username in AUTHORIZED_USERS and AUTHORIZED_USERS[username] == password:
        return "admin" if username in ("admin", "adom0985") else username
    return None

def create_auth_token(username: str, expires_in_days: int = 30) -> str:
    """Creates a cryptographically secure HMAC-SHA256 signed token."""
    payload = {
        "sub": username,
        "exp": int(time.time()) + (expires_in_days * 86400),
        "iat": int(time.time())
    }
    payload_bytes = json.dumps(payload, separators=(',', ':')).encode("utf-8")
    payload_b64 = base64.urlsafe_b64encode(payload_bytes).decode("utf-8").rstrip("=")
    sig = hmac.new(AUTH_SECRET.encode("utf-8"), payload_b64.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{payload_b64}.{sig}"

def verify_auth_token(token: str) -> Optional[dict]:
    """Verifies HMAC signature and expiration. Returns payload if valid, else None."""
    if not token or not isinstance(token, str) or "." not in token:
        return None
    try:
        payload_b64, sig = token.split(".", 1)
        expected_sig = hmac.new(AUTH_SECRET.encode("utf-8"), payload_b64.encode("utf-8"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected_sig):
            return None
        
        # Restore base64 padding
        pad = len(payload_b64) % 4
        if pad:
            payload_b64 += "=" * (4 - pad)
            
        payload_bytes = base64.urlsafe_b64decode(payload_b64)
        payload = json.loads(payload_bytes.decode("utf-8"))
        
        if payload.get("exp", 0) < time.time():
            return None # Expired
            
        return payload
    except Exception:
        return None

def extract_token_from_request(request: Request) -> Optional[str]:
    """Extracts token from Authorization header, Cookie, or Query parameter."""
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.split("Bearer ", 1)[1].strip()
        
    cookie_token = request.cookies.get("auth_token")
    if cookie_token:
        return cookie_token
        
    query_token = request.query_params.get("token")
    if query_token:
        return query_token
        
    return None
