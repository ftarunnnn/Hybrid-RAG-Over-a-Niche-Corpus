"""API package."""
from app.api.routes_query import router as query_router
from app.api.routes_health import router as health_router
from app.api.routes_ingestion import router as ingestion_router

__all__ = ["query_router", "health_router", "ingestion_router"]
