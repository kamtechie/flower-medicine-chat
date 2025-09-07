from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import structlog

class BindSessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        sid = request.headers.get("X-Session-ID")
        if sid:
            structlog.contextvars.bind_contextvars(session_id=sid)
        try:
            response = await call_next(request)
        finally:
            structlog.contextvars.clear_contextvars()
        return response
