"""FastAPI Application Entry Point.

Minimal stub for Sprint 1 infrastructure validation.
No business logic - just health check endpoint.
"""

from fastapi import FastAPI

app = FastAPI(
    title="Dropshipping Platform",
    description="Meta Ads Intelligence Platform",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint for Docker and load balancers."""
    return {"status": "ok"}
