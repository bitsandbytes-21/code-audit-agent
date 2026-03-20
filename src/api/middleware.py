"""
Middleware for rate limiting and authentication.
"""

import time
import secrets
from collections import defaultdict

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.config import settings


# ─── Rate Limiter ─────────────────────────────────────────────────────────────


class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window = window_seconds
        self.requests: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, ip: str) -> bool:
        now = time.time()
        self.requests[ip] = [t for t in self.requests[ip] if now - t < self.window]
        if len(self.requests[ip]) >= self.max_requests:
            return False
        self.requests[ip].append(now)
        return True


rate_limiter = RateLimiter(
    max_requests=settings.RATE_LIMIT_MAX,
    window_seconds=settings.RATE_LIMIT_WINDOW,
)


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/api/chat":
            ip = request.client.host if request.client else "unknown"
            if not rate_limiter.is_allowed(ip):
                return JSONResponse(
                    {"error": "Rate limited. Please wait before trying again."},
                    status_code=429,
                )
        return await call_next(request)


# ─── Session Auth ─────────────────────────────────────────────────────────────

SESSION_TTL = 86400  # 24 hours
active_sessions: dict[str, float] = {}


def create_session() -> str:
    token = secrets.token_urlsafe(32)
    active_sessions[token] = time.time()
    return token


def verify_session(request: Request) -> bool:
    if not settings.auth_enabled:
        return True
    token = request.cookies.get("session_token")
    if token and token in active_sessions:
        if time.time() - active_sessions[token] < SESSION_TTL:
            return True
        del active_sessions[token]
    return False
