"""Security headers, CSRF tokens for the admin, and a simple rate limiter."""
import hmac
import secrets
import threading
import time
from collections import defaultdict, deque

from flask import abort, g, request, session


def csrf_token():
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_urlsafe(32)
    return session["_csrf"]


def check_csrf():
    sent = request.form.get("_csrf", "")
    expected = session.get("_csrf", "")
    if not expected or not hmac.compare_digest(sent, expected):
        abort(400, "Your session expired. Go back, refresh the page and try again.")


class RateLimiter:
    """Allows `limit` hits per `window` seconds for each key. In-memory, so it
    resets on restart and is per process; fine for a single small server."""

    def __init__(self, limit, window):
        self.limit = limit
        self.window = window
        self.hits = defaultdict(deque)
        self.lock = threading.Lock()

    def _recent(self, key, now):
        hits = self.hits[key]
        while hits and hits[0] <= now - self.window:
            hits.popleft()
        return hits

    def blocked(self, key):
        with self.lock:
            return len(self._recent(key, time.monotonic())) >= self.limit

    def record(self, key):
        with self.lock:
            self._recent(key, time.monotonic()).append(time.monotonic())

    def allow(self, key):
        """Check and count in one step."""
        with self.lock:
            now = time.monotonic()
            hits = self._recent(key, now)
            if len(hits) >= self.limit:
                return False
            hits.append(now)
            return True


def init_app(app):
    @app.before_request
    def make_nonce():
        g.csp_nonce = secrets.token_urlsafe(16)

    @app.after_request
    def security_headers(response):
        nonce = getattr(g, "csp_nonce", "")
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            f"script-src 'self' 'nonce-{nonce}'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: blob:; "
            "frame-src https://www.google.com; "
            "form-action 'self'; frame-ancestors 'none'; base-uri 'self'; object-src 'none'"
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        if app.config["PRODUCTION"]:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        if request.path.startswith("/admin"):
            response.headers["Cache-Control"] = "no-store"
        return response
