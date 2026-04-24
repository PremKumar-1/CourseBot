"""
Vercel API entrypoint. Keep a stable `app` export under `api/` while
reusing the main FastAPI application defined in `app.main`.
"""

from app.main import app

__all__ = ["app"]
