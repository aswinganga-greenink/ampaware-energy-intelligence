# =============================================================================
# AmpAware Backend — Production Dockerfile
# =============================================================================
#
# Multi-stage build:
# Stage 1 (builder): Install dependencies in a virtual env
# Stage 2 (runtime): Copy only the venv — no build tools in final image
#
# Security:
# - Runs as non-root user "ampaware" (uid 1001)
# - No dev dependencies in production image
# - Uses specific Python patch version for reproducibility
#
# Build:
#   docker build -t ampaware-backend:latest .
#
# Run:
#   docker run -p 8000:8000 --env-file .env ampaware-backend:latest

# ---- Stage 1: Builder -------------------------------------------------------
FROM python:3.12.7-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# Install system build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create and populate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# ---- Stage 2: Runtime -------------------------------------------------------
FROM python:3.12.7-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# Runtime PostgreSQL client library (needed by asyncpg/psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Non-root user
RUN groupadd -g 1001 ampaware && \
    useradd -u 1001 -g ampaware -s /bin/bash -m ampaware

# Copy venv from builder
COPY --from=builder /opt/venv /opt/venv

WORKDIR /app

# Copy application source
COPY --chown=ampaware:ampaware . .

# Create log directory
RUN mkdir -p /app/logs && chown -R ampaware:ampaware /app/logs

USER ampaware

EXPOSE 8000

# Health check (liveness probe)
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Start uvicorn with production settings
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "4", \
     "--loop", "uvloop", \
     "--http", "httptools", \
     "--no-access-log", \
     "--proxy-headers"]
