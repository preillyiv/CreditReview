"""
FastAPI application for the Financial Reporting Tool.

This module sets up the FastAPI app with CORS middleware and includes
all route modules.
"""

# Load environment variables from .env file
import os

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import extraction, export

# Build allowed origins list for CORS
_origins = [
    "http://localhost:5173",  # Vite dev server
    "http://localhost:3000",  # Alternative React port
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]
# Allow the Vercel deployment URL when deployed
_vercel_url = os.environ.get("VERCEL_URL")
if _vercel_url:
    _origins.append(f"https://{_vercel_url}")

# Create FastAPI app
app = FastAPI(
    title="Financial Reporting API",
    description="Generate financial reports from SEC EDGAR data with human-in-the-loop review",
    version="1.0.0",
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include route modules
app.include_router(extraction.router, prefix="/api", tags=["extraction"])
app.include_router(export.router, prefix="/api", tags=["export"])


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "Financial Reporting API"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}
