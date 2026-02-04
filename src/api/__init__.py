"""
FastAPI application for the Financial Reporting Tool.

This module sets up the FastAPI app with CORS middleware and includes
all route modules.
"""

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import extraction, export

# Create FastAPI app
app = FastAPI(
    title="Financial Reporting API",
    description="Generate financial reports from SEC EDGAR data with human-in-the-loop review",
    version="1.0.0",
)

# Configure CORS for frontend
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


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "Financial Reporting API"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}
