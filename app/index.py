"""
Vercel entrypoint: the platform looks for a FastAPI instance named `app` at
`app/index.py` (among other paths). The real app lives in `app.main`.
"""
try:
    # Works when imported as a package module (most local runs).
    from .main import app
except ImportError:
    # Works when loaded by path in some serverless loaders.
    from app.main import app

__all__ = ["app"]
