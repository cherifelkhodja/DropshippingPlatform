"""API Module.

FastAPI application layer with routers, schemas, and dependencies.
"""

from .dependencies import get_db_session, get_settings

__all__ = ["get_db_session", "get_settings"]
