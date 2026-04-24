"""
Vercel entrypoint: the platform looks for a FastAPI instance named `app` at
`app/index.py` (among other paths). The real app lives in `app.main`.
"""
from .main import app

__all__ = ["app"]
