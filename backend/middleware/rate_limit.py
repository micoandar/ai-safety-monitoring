import logging
import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from config import get_settings

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    In-memory sliding-window rate limiter per IP.
    Untuk production multi-instance, ganti ke Redis-backed (mis. slowapi).
    """

    def __init__(self, app):
        super().__init__(app)
        self._settings = get_settings()
        self._buckets: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()
        self._window = 60.0

        self._rules: list[tuple[str, int]] = [
            ("/api/detection/frame", self._settings.RATE_LIMIT_FRAME_PER_MINUTE),
            ("/api/detection/image", self._settings.RATE_LIMIT_DETECTION_PER_MINUTE),
            ("/api/", self._settings.RATE_LIMIT_DEFAULT_PER_MINUTE),
        ]

    def _client_ip(self, request: Request) -> str:
        if self._settings.TRUST_PROXY_HEADERS:
            forwarded = request.headers.get("x-forwarded-for")
            if forwarded:
                return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _limit_for(self, path: str) -> int | None:
        for prefix, limit in self._rules:
            if path.startswith(prefix):
                return limit
        return None

    async def dispatch(self, request: Request, call_next):
        if not self._settings.RATE_LIMIT_ENABLED:
            return await call_next(request)

        path = request.url.path
        if path in ("/", "/health", "/docs", "/redoc", "/openapi.json"):
            return await call_next(request)

        limit = self._limit_for(path)
        if limit is None:
            return await call_next(request)

        ip = self._client_ip(request)
        parts = path.split("/")
        key = f"{ip}:{parts[2] if len(parts) > 2 else path}"
        now = time.monotonic()
        cutoff = now - self._window

        with self._lock:
            bucket = self._buckets[key]
            while bucket and bucket[0] < cutoff:
                bucket.popleft()
            if len(bucket) >= limit:
                retry_after = int(self._window - (now - bucket[0])) + 1
                logger.warning("Rate limit exceeded: ip=%s path=%s", ip, path)
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": "Terlalu banyak permintaan. Coba lagi sebentar.",
                    },
                    headers={"Retry-After": str(max(1, retry_after))},
                )
            bucket.append(now)

        return await call_next(request)