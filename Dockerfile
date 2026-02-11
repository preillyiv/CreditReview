# Stage 1: Build frontend
FROM node:20-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Python backend
FROM python:3.11-slim
WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install Python dependencies
COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev

# Copy backend source
COPY src/ ./src/

# Copy built frontend
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# Render sets PORT env var (default 10000)
EXPOSE 10000

CMD uv run uvicorn src.api:app --host 0.0.0.0 --port ${PORT:-10000}
