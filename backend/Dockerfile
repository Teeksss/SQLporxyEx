# Enterprise SQL Proxy System - Backend Dockerfile (Version Fixed)
# Created: 2025-05-30 08:21:32 UTC by Teeksss
# Version: 2.0.0 Final - Compatible Dependencies

FROM python:3.11-slim

# Build arguments
ARG BUILD_DATE="2025-05-30 08:21:32"
ARG VERSION="2.0.0"
ARG CREATOR="Teeksss"

# Labels
LABEL maintainer="Teeksss"
LABEL version="${VERSION}"
LABEL description="Enterprise SQL Proxy System Backend - Version Fixed"
LABEL build-date="${BUILD_DATE}"
LABEL creator="${CREATOR}"

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV DEBIAN_FRONTEND=noninteractive

# Set work directory
WORKDIR /app

# Install system dependencies (Essential only)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    wget \
    git \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    postgresql-client \
    redis-tools \
    ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip first
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies with fallback strategy
RUN pip install --no-cache-dir -r requirements.txt || \
    (echo "Main requirements failed, trying minimal..." && \
     pip install --no-cache-dir \
     fastapi==0.104.1 \
     uvicorn[standard]==0.24.0 \
     sqlalchemy==2.0.23 \
     psycopg2-binary==2.9.9 \
     redis==5.0.1 \
     python-dotenv==1.0.0 \
     pydantic==2.5.0 \
     httpx==0.25.2 \
     requests==2.31.0)

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs uploads backups static temp

# Set permissions
RUN chmod +x /app

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]