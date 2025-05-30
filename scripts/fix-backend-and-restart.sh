#!/bin/bash

# Enterprise SQL Proxy System - Backend Fix and Restart Script
# Created: 2025-05-30 08:10:23 UTC by Teeksss
# Purpose: Fix ODBC driver issues and restart backend

set -euo pipefail

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
PURPLE='\033[0;35m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $(date '+%H:%M:%S') $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $(date '+%H:%M:%S') $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $(date '+%H:%M:%S') $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $(date '+%H:%M:%S') $1"; }
log_step() { echo -e "${PURPLE}[STEP]${NC} $(date '+%H:%M:%S') $1"; }

echo -e "${PURPLE}"
echo "================================================================"
echo "🚀 Enterprise SQL Proxy System - Backend ODBC Fix"
echo "================================================================"
echo -e "${NC}"
echo "Created by: Teeksss"
echo "Date: 2025-05-30 08:10:23 UTC"
echo "Purpose: Fix Microsoft ODBC Driver installation issues"
echo ""

# Step 1: Stop backend service
log_step "Step 1: Stopping backend service"
docker-compose stop backend || true

# Step 2: Remove backend container and image
log_step "Step 2: Removing old backend container and image"
docker-compose rm -f backend || true
docker rmi $(docker images | grep esp_backend | awk '{print $3}') 2>/dev/null || true

# Step 3: Clean Docker build cache
log_step "Step 3: Cleaning Docker build cache"
docker builder prune -f

# Step 4: Rebuild backend with no cache
log_step "Step 4: Rebuilding backend with ODBC driver fix"
log_info "This may take several minutes..."
docker-compose build --no-cache backend

if [ $? -eq 0 ]; then
    log_success "Backend rebuild completed successfully"
else
    log_error "Backend rebuild failed"
    exit 1
fi

# Step 5: Start backend service
log_step "Step 5: Starting backend service"
docker-compose up -d backend

log_info "Waiting for backend to start..."
sleep 30

# Step 6: Test backend health
log_step "Step 6: Testing backend health"
local max_attempts=30
local attempt=1

while [[ $attempt -le $max_attempts ]]; do
    if curl -f http://localhost:8000/health &>/dev/null; then
        log_success "✅ Backend is healthy and responding"
        break
    fi
    
    if [[ $attempt -eq $max_attempts ]]; then
        log_warning "⚠️ Backend taking longer than expected to start"
        log_info "Check logs with: docker-compose logs backend"
        break
    fi
    
    log_info "Attempt $attempt/$max_attempts - Waiting for backend..."
    sleep 3
    ((attempt++))
done

# Step 7: Test database drivers
log_step "Step 7: Testing database drivers"
if curl -f http://localhost:8000/drivers &>/dev/null; then
    log_success "✅ Database drivers endpoint is accessible"
    log_info "Check driver status at: http://localhost:8000/drivers"
else
    log_warning "⚠️ Database drivers endpoint not yet accessible"
fi

# Step 8: Show final status
log_step "Step 8: Final system status"
echo ""
echo "🔗 Backend Access URLs:"
echo "  • Health Check:     http://localhost:8000/health"
echo "  • API Documentation: http://localhost:8000/docs"
echo "  • Database Drivers:  http://localhost:8000/drivers"
echo "  • System Info:      http://localhost:8000/system"
echo ""

echo "📊 Backend Container Status:"
docker-compose ps backend

echo ""
echo "📋 Useful Commands:"
echo "  • View backend logs:    docker-compose logs -f backend"
echo "  • Restart backend:      docker-compose restart backend"
echo "  • Check all services:   docker-compose ps"
echo ""

# Test specific endpoints
log_info "Testing key endpoints..."

if curl -s http://localhost:8000/health | jq '.status' 2>/dev/null | grep -q "healthy"; then
    log_success "✅ Health endpoint: Working"
else
    log_warning "⚠️ Health endpoint: Not responding"
fi

if curl -s http://localhost:8000/drivers | jq '.drivers' &>/dev/null; then
    log_success "✅ Drivers endpoint: Working"
else
    log_warning "⚠️ Drivers endpoint: Not responding"
fi

if curl -s http://localhost:8000/system | jq '.system' &>/dev/null; then
    log_success "✅ System endpoint: Working"
else
    log_warning "⚠️ System endpoint: Not responding"
fi

echo ""
log_success "🎉 Backend ODBC driver fix completed!"
log_info "If you still have issues, check the logs: docker-compose logs backend"

# Show ODBC driver info if available
log_info "Checking ODBC driver installation..."
if docker-compose exec -T backend python -c "import pyodbc; print('ODBC Drivers:', pyodbc.drivers())" 2>/dev/null; then
    log_success "✅ ODBC drivers are properly installed"
else
    log_warning "⚠️ Unable to verify ODBC driver installation"
fi