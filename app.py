"""
Code Audit Agent — Entry Point
Run with: python app.py
"""

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.api.routes import router
from src.api.middleware import RateLimitMiddleware
from src.config import settings

# ─── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

# ─── App ──────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Code Audit Agent",
    version="2.0",
    description="AI-powered code security auditor",
)

app.add_middleware(RateLimitMiddleware)
app.include_router(router)

# Serve frontend
STATIC_DIR = Path(__file__).parent / "src" / "static"


@app.get("/")
async def root():
    return FileResponse(STATIC_DIR / "index.html")


# ─── Run ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=True,
    )
