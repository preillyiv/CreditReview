"""
Vercel serverless function entry point.

Imports the FastAPI app from the main application module so Vercel
can serve it as a Python serverless function.
"""

from src.api import app
