"""
FastAPI application for the Financial Reporting Tool.

This module sets up the FastAPI app with CORS middleware and includes
all route modules.
"""

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from src.api.routes import extraction, export

# Create FastAPI app
app = FastAPI(
    title="Financial Reporting API",
    description="Generate financial reports from SEC EDGAR data with human-in-the-loop review",
    version="1.0.0",
)

# Configure CORS for frontend (needed for local dev; production serves same-origin)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative React port
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include route modules
app.include_router(extraction.router, prefix="/api", tags=["extraction"])
app.include_router(export.router, prefix="/api", tags=["export"])


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


# Serve frontend static files in production
FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"

if FRONTEND_DIR.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="static-assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """Serve frontend SPA — returns index.html for all non-API routes."""
        file_path = FRONTEND_DIR / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(FRONTEND_DIR / "index.html")
else:
    @app.get("/")
    async def root():
        """Health check endpoint (no frontend build present)."""
        return {"status": "ok", "message": "Financial Reporting API"}
