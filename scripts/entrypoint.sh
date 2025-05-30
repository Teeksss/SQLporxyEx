#!/bin/bash
# Enterprise SQL Proxy System - Production Entrypoint
# Created: 2025-05-29 14:45:01 UTC by Teeksss

set -e

echo "🚀 Starting Enterprise SQL Proxy System v2.0.0"
echo "📅 Build Date: 2025-05-29 14:45:01 UTC"
echo "👤 Created by: Teeksss"
echo "🌍 Environment: ${ENVIRONMENT:-production}"

# Wait for database
echo "⏳ Waiting for database..."
python -c "
import time
import psycopg2
import os
from urllib.parse import urlparse

max_retries = 30
retry_count = 0

db_url = os.getenv('DATABASE_URL')
if not db_url:
    print('❌ DATABASE_URL not set')
    exit(1)

parsed = urlparse(db_url)

while retry_count < max_retries:
    try:
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port,
            user=parsed.username,
            password=parsed.password,
            database=parsed.path[1:]
        )
        conn.close()
        print('✅ Database connection successful')
        break
    except psycopg2.OperationalError:
        retry_count += 1
        print(f'⏳ Database not ready, retrying... ({retry_count}/{max_retries})')
        time.sleep(2)

if retry_count >= max_retries:
    print('❌ Database connection failed after maximum retries')
    exit(1)
"

# Wait for Redis (if enabled)
if [ "${CACHE_ENABLED:-true}" = "true" ]; then
    echo "⏳ Waiting for Redis..."
    python -c "
import time
import redis
import os
from urllib.parse import urlparse

max_retries = 30
retry_count = 0

redis_url = os.getenv('REDIS_URL')
if not redis_url:
    print('❌ REDIS_URL not set')
    exit(1)

while retry_count < max_retries:
    try:
        r = redis.from_url(redis_url)
        r.ping()
        print('✅ Redis connection successful')
        break
    except (redis.ConnectionError, redis.TimeoutError):
        retry_count += 1
        print(f'⏳ Redis not ready, retrying... ({retry_count}/{max_retries})')
        time.sleep(2)

if retry_count >= max_retries:
    print('❌ Redis connection failed after maximum retries')
    exit(1)
    "
fi

# Run database migrations
echo "🔄 Running database migrations..."
python -c "
from app.core.database import create_all_tables
try:
    create_all_tables()
    print('✅ Database migrations completed')
except Exception as e:
    print(f'❌ Database migrations failed: {e}')
    exit(1)
"

# Create necessary directories
mkdir -p /app/logs /app/uploads /app/backups

# Set proper permissions
chown -R appuser:appuser /app/logs /app/uploads /app/backups

echo "✅ Pre-startup checks completed"

# Start the application
if [ "${ENVIRONMENT}" = "production" ]; then
    echo "🏭 Starting production server with Gunicorn..."
    exec gunicorn app.main:app \
        --bind 0.0.0.0:8000 \
        --workers ${WORKERS:-4} \
        --worker-class ${WORKER_CLASS:-gevent} \
        --worker-connections ${WORKER_CONNECTIONS:-1000} \
        --max-requests ${MAX_REQUESTS:-1000} \
        --max-requests-jitter ${MAX_REQUESTS_JITTER:-100} \
        --timeout ${TIMEOUT:-30} \
        --keepalive ${KEEPALIVE:-2} \
        --preload \
        --access-logfile - \
        --error-logfile - \
        --log-level info \
        --capture-output \
        --enable-stdio-inheritance
else
    echo "🛠️ Starting development server with Uvicorn..."
    exec uvicorn app.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --reload \
        --log-level info
fi