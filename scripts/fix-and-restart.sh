#!/bin/bash

# Enterprise SQL Proxy System - Fix and Restart Script
# Created: 2025-05-30 08:05:44 UTC by Teeksss
# Purpose: Apply fixes and restart the system

set -euo pipefail

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $(date '+%H:%M:%S') $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $(date '+%H:%M:%S') $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $(date '+%H:%M:%S') $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $(date '+%H:%M:%S') $1"; }

echo "🚀 Enterprise SQL Proxy System - Fix and Restart"
echo "================================================="
echo "Created by: Teeksss"
echo "Date: 2025-05-30 08:05:44 UTC"
echo ""

# Step 1: Stop and clean existing containers
log_info "Stopping and cleaning existing containers..."
docker-compose down --remove-orphans
docker system prune -f
docker rmi $(docker images | grep esp_ | awk '{print $3}') 2>/dev/null || true

# Step 2: Remove problematic files
log_info "Cleaning frontend dependencies..."
cd frontend
rm -rf node_modules package-lock.json .next build
cd ..

# Step 3: Rebuild with no cache
log_info "Rebuilding services with no cache..."
docker-compose build --no-cache

# Step 4: Start services step by step
log_info "Starting database services first..."
docker-compose up -d postgres redis

log_info "Waiting for databases to be ready..."
sleep 30

# Check databases
if docker-compose exec -T postgres pg_isready -U postgres &>/dev/null; then
    log_success "PostgreSQL is ready"
else
    log_warning "PostgreSQL still starting..."
fi

if docker-compose exec -T redis redis-cli ping &>/dev/null; then
    log_success "Redis is ready"
else
    log_warning "Redis still starting..."
fi

# Step 5: Start backend
log_info "Starting backend service..."
docker-compose up -d backend

log_info "Waiting for backend to be ready..."
sleep 45

# Check backend
local attempt=1
while [[ $attempt -le 30 ]]; do
    if curl -f http://localhost:8000/health &>/dev/null; then
        log_success "Backend is ready"
        break
    fi
    if [[ $attempt -eq 30 ]]; then
        log_warning "Backend taking longer than expected"
    fi
    sleep 2
    ((attempt++))
done

# Step 6: Start frontend
log_info "Starting frontend service..."
docker-compose up -d frontend

log_info "Waiting for frontend to be ready..."
sleep 60

# Check frontend
attempt=1
while [[ $attempt -le 30 ]]; do
    if curl -f http://localhost:3000 &>/dev/null; then
        log_success "Frontend is ready"
        break
    fi
    if [[ $attempt -eq 30 ]]; then
        log_warning "Frontend taking longer than expected (normal for first start)"
    fi
    sleep 3
    ((attempt++))
done

# Step 7: Final status check
log_info "Final system status check..."
echo ""
echo "🔗 Access URLs:"
echo "  • Frontend:      http://localhost:3000"
echo "  • Backend API:   http://localhost:8000"
echo "  • API Docs:      http://localhost:8000/docs"
echo "  • Health Check:  http://localhost:8000/health"
echo ""

echo "📊 Service Status:"
docker-compose ps

echo ""
log_success "System restart completed!"
log_info "If you still have issues, check logs with: docker-compose logs -f"