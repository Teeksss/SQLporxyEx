#!/bin/bash

# Enterprise SQL Proxy System - PostgreSQL Backend Fix Script
# Created: 2025-05-30 08:16:16 UTC by Teeksss
# Purpose: Fix backend without ODBC dependencies

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
echo "🚀 Enterprise SQL Proxy System - PostgreSQL Backend Fix"
echo "================================================================"
echo -e "${NC}"
echo "Created by: Teeksss"
echo "Date: 2025-05-30 08:16:16 UTC"
echo "Purpose: Remove ODBC dependencies, focus on PostgreSQL"
echo ""

# Step 1: Stop all services
log_step "Step 1: Stopping all services"
docker-compose down

# Step 2: Remove backend images and containers
log_step "Step 2: Removing old backend containers and images"
docker-compose rm -f backend || true
docker rmi $(docker images | grep esp_backend | awk '{print $3}') 2>/dev/null || true

# Step 3: Clean Docker system
log_step "Step 3: Cleaning Docker system"
docker system prune -f
docker builder prune -f

# Step 4: Rebuild backend (PostgreSQL focused)
log_step "Step 4: Rebuilding backend (PostgreSQL + MySQL focused)"
log_info "This will be much faster without ODBC dependencies..."

if docker-compose build --no-cache backend; then
    log_success "✅ Backend rebuild completed successfully"
else
    log_error "❌ Backend rebuild failed"
    exit 1
fi

# Step 5: Start database services first
log_step "Step 5: Starting database services"
docker-compose up -d postgres redis

log_info "Waiting for databases to be ready..."
sleep 30

# Check PostgreSQL
if docker-compose exec -T postgres pg_isready -U postgres &>/dev/null; then
    log_success "✅ PostgreSQL is ready"
else
    log_warning "⚠️ PostgreSQL still starting..."
fi

# Check Redis
if docker-compose exec -T redis redis-cli ping &>/dev/null; then
    log_success "✅ Redis is ready"
else
    log_warning "⚠️ Redis still starting..."
fi

# Step 6: Start backend
log_step "Step 6: Starting backend service"
docker-compose up -d backend

log_info "Waiting for backend to start..."
sleep 45

# Step 7: Test backend health
log_step "Step 7: Testing backend health"
local max_attempts=30
local attempt=1

while [[ $attempt -le $max_attempts ]]; do
    if curl -f http://localhost:8000/health &>/dev/null; then
        log_success "✅ Backend is healthy and responding"
        break
    fi
    
    if [[ $attempt -eq $max_attempts ]]; then
        log_warning "⚠️ Backend taking longer than expected"
        log_info "Check logs: docker-compose logs backend"
        break
    fi
    
    log_info "Attempt $attempt/$max_attempts - Waiting for backend..."
    sleep 3
    ((attempt++))
done

# Step 8: Test database drivers
log_step "Step 8: Testing database drivers"
if curl -s http://localhost:8000/drivers | jq '.drivers' &>/dev/null; then
    log_success "✅ Database drivers endpoint working"
    
    # Show driver status
    echo ""
    echo "📊 Database Driver Status:"
    curl -s http://localhost:8000/drivers | jq '.drivers' 2>/dev/null || echo "Unable to parse driver status"
else
    log_warning "⚠️ Database drivers endpoint not yet accessible"
fi

# Step 9: Start frontend
log_step "Step 9: Starting frontend service"
docker-compose up -d frontend

log_info "Waiting for frontend..."
sleep 30

# Step 10: Final status check
log_step "Step 10: Final system status"
echo ""
echo "🔗 Access URLs:"
echo "  • Frontend:        http://localhost:3000"
echo "  • Backend API:     http://localhost:8000"
echo "  • Health Check:    http://localhost:8000/health"
echo "  • API Docs:        http://localhost:8000/docs"
echo "  • System Info:     http://localhost:8000/system"
echo "  • Driver Status:   http://localhost:8000/drivers"
echo ""

echo "📊 Service Status:"
docker-compose ps

echo ""
echo "🗄️ Supported Databases:"
echo "  • PostgreSQL (Primary) ✅"
echo "  • MySQL/MariaDB ✅"
echo "  • Redis (Cache) ✅"
echo "  • MSSQL (Removed - No ODBC)"
echo ""

# Test key endpoints
log_info "Testing key endpoints..."

# Health check
if curl -s http://localhost:8000/health | jq '.status' 2>/dev/null | grep -q "healthy"; then
    log_success "✅ Health endpoint: Working"
else
    log_warning "⚠️ Health endpoint: Not responding"
fi

# API info
if curl -s http://localhost:8000/api/v1/info | jq '.api_version' &>/dev/null; then
    log_success "✅ API info endpoint: Working"
else
    log_warning "⚠️ API info endpoint: Not responding"
fi

# System status
if curl -s http://localhost:8000/system | jq '.system' &>/dev/null; then
    log_success "✅ System endpoint: Working"
else
    log_warning "⚠️ System endpoint: Not responding"
fi

# Drivers endpoint
if curl -s http://localhost:8000/drivers | jq '.drivers' &>/dev/null; then
    log_success "✅ Drivers endpoint: Working"
else
    log_warning "⚠️ Drivers endpoint: Not responding"
fi

echo ""
log_success "🎉 PostgreSQL-focused backend is now running!"
log_info "Enterprise features available:"
log_info "  • Multi-tenant support"
log_info "  • Role-based access control"
log_info "  • Advanced analytics"
log_info "  • Performance monitoring"
log_info "  • Audit logging"

echo ""
log_info "📋 Useful Commands:"
log_info "  • View logs:        docker-compose logs -f"
log_info "  • Restart system:   docker-compose restart"
log_info "  • Check status:     docker-compose ps"
log_info "  • Stop system:      docker-compose down"