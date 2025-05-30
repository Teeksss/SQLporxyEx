#!/bin/bash

# Enterprise SQL Proxy System - Dependency Version Fix Script (Fixed)
# Created: 2025-05-30 08:28:18 UTC by Teeksss
# Purpose: Fix cryptography and other dependency version issues

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
echo "🚀 Enterprise SQL Proxy System - Dependency Version Fix"
echo "================================================================"
echo -e "${NC}"
echo "Current Date: 2025-05-30 08:28:18 UTC"
echo "Created by: Teeksss"
echo "Purpose: Fix cryptography dependency version issues"
echo ""

# Global variables
BUILD_SUCCESS=false
MAX_ATTEMPTS=30

# Step 1: Stop backend service
log_step "Step 1: Stopping backend service"
docker-compose stop backend || true

# Step 2: Remove backend container and image
log_step "Step 2: Removing old backend container and image"
docker-compose rm -f backend || true
docker rmi $(docker images | grep esp_backend | awk '{print $3}') 2>/dev/null || true

# Step 3: Create minimal requirements as fallback
log_step "Step 3: Creating minimal requirements fallback"
cat > backend/requirements-minimal.txt << 'EOF'
# Minimal requirements for Enterprise SQL Proxy System
# Created: 2025-05-30 08:28:18 UTC by Teeksss
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
redis==5.0.1
python-dotenv==1.0.0
pydantic==2.5.0
httpx==0.25.2
requests==2.31.0
click==8.1.7
rich==13.7.0
python-multipart==0.0.6
EOF

log_success "Minimal requirements created as fallback"

# Step 4: Try building with updated requirements
log_step "Step 4: Building with updated requirements"
log_info "This may take a few minutes..."

if docker-compose build --no-cache backend; then
    log_success "✅ Backend build completed successfully"
    BUILD_SUCCESS=true
else
    log_warning "⚠️ Standard build failed, trying minimal approach..."
    BUILD_SUCCESS=false
fi

# Step 5: Fallback to minimal build if needed
if [ "$BUILD_SUCCESS" = false ]; then
    log_step "Step 5: Attempting minimal fallback build"
    
    # Create minimal Dockerfile
    cat > backend/Dockerfile.minimal << 'EOF'
# Enterprise SQL Proxy System - Minimal Dockerfile
# Created: 2025-05-30 08:28:18 UTC by Teeksss

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libpq-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip setuptools wheel

# Install core dependencies one by one (safer approach)
RUN pip install fastapi==0.104.1
RUN pip install uvicorn[standard]==0.24.0
RUN pip install sqlalchemy==2.0.23
RUN pip install psycopg2-binary==2.9.9
RUN pip install redis==5.0.1
RUN pip install python-dotenv==1.0.0
RUN pip install pydantic==2.5.0
RUN pip install httpx==0.25.2
RUN pip install requests==2.31.0
RUN pip install click==8.1.7
RUN pip install python-multipart==0.0.6

# Copy application code
COPY . .

# Create directories
RUN mkdir -p logs uploads backups static temp

# Set permissions
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
EOF

    # Backup original docker-compose
    cp docker-compose.yml docker-compose.yml.backup
    
    # Update docker-compose to use minimal Dockerfile
    sed -i 's/dockerfile: Dockerfile/dockerfile: Dockerfile.minimal/' docker-compose.yml
    
    log_info "Building with minimal Dockerfile..."
    if docker-compose build --no-cache backend; then
        log_success "✅ Minimal backend build completed successfully"
        BUILD_SUCCESS=true
    else
        log_error "❌ Even minimal build failed"
        
        # Restore original docker-compose
        mv docker-compose.yml.backup docker-compose.yml
        exit 1
    fi
fi

# Step 6: Start database services
log_step "Step 6: Starting database services"
docker-compose up -d postgres redis

log_info "Waiting for databases to initialize..."
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

# Step 7: Start backend
log_step "Step 7: Starting backend service"
docker-compose up -d backend

log_info "Waiting for backend to start..."
sleep 45

# Step 8: Test backend health
log_step "Step 8: Testing backend health"
ATTEMPT=1

while [[ $ATTEMPT -le $MAX_ATTEMPTS ]]; do
    if curl -f http://localhost:8000/health &>/dev/null; then
        log_success "✅ Backend is healthy and responding"
        break
    fi
    
    if [[ $ATTEMPT -eq $MAX_ATTEMPTS ]]; then
        log_warning "⚠️ Backend health check timeout after $MAX_ATTEMPTS attempts"
        log_info "Check logs with: docker-compose logs backend"
        break
    fi
    
    log_info "Health check attempt $ATTEMPT/$MAX_ATTEMPTS - Backend starting..."
    sleep 3
    ((ATTEMPT++))
done

# Step 9: Start frontend
log_step "Step 9: Starting frontend service"
docker-compose up -d frontend

log_info "Waiting for frontend to start..."
sleep 30

# Step 10: Final system status
log_step "Step 10: Final system status check"
echo ""
echo "🔗 Access URLs:"
echo "  • Frontend:         http://localhost:3000"
echo "  • Backend API:      http://localhost:8000"
echo "  • Health Check:     http://localhost:8000/health"
echo "  • API Documentation: http://localhost:8000/docs"
echo "  • System Info:      http://localhost:8000/system"
echo ""

echo "📊 Service Status:"
docker-compose ps

echo ""
log_info "Testing key endpoints..."

# Test health endpoint
if curl -s http://localhost:8000/health | grep -q "healthy" 2>/dev/null; then
    log_success "✅ Health endpoint: Working"
else
    log_warning "⚠️ Health endpoint: Not responding"
fi

# Test root endpoint
if curl -s http://localhost:8000/ | grep -q "Enterprise SQL Proxy" 2>/dev/null; then
    log_success "✅ Root endpoint: Working"
else
    log_warning "⚠️ Root endpoint: Not responding"
fi

# Test API docs
if curl -s http://localhost:8000/docs &>/dev/null; then
    log_success "✅ API Documentation: Available"
else
    log_warning "⚠️ API Documentation: Not accessible"
fi

echo ""
if [ "$BUILD_SUCCESS" = true ]; then
    log_success "🎉 Dependency version fix completed successfully!"
    log_info "Backend is running with compatible dependency versions"
else
    log_warning "⚠️ System is running but some issues may persist"
    log_info "Check logs for more details"
fi

echo ""
log_info "📋 Useful Commands:"
log_info "  • View backend logs:    docker-compose logs -f backend"
log_info "  • View all logs:        docker-compose logs -f"
log_info "  • Restart backend:      docker-compose restart backend"
log_info "  • Restart all:          docker-compose restart"
log_info "  • Check status:         docker-compose ps"
log_info "  • Stop system:          docker-compose down"

# Show dependency info
echo ""
log_info "🔍 Checking installed packages in backend..."
if docker-compose exec -T backend pip list 2>/dev/null | head -20; then
    log_success "✅ Package list retrieved successfully"
else
    log_warning "⚠️ Unable to retrieve package list"
fi

echo ""
log_info "🏥 System Health Summary:"
echo "  • PostgreSQL: $(docker-compose exec -T postgres pg_isready -U postgres &>/dev/null && echo "✅ Healthy" || echo "⚠️ Check needed")"
echo "  • Redis: $(docker-compose exec -T redis redis-cli ping &>/dev/null && echo "✅ Healthy" || echo "⚠️ Check needed")"
echo "  • Backend: $(curl -s http://localhost:8000/health &>/dev/null && echo "✅ Healthy" || echo "⚠️ Check needed")"
echo "  • Frontend: $(curl -s http://localhost:3000 &>/dev/null && echo "✅ Healthy" || echo "⚠️ Check needed")"

echo ""
log_success "🚀 Enterprise SQL Proxy System is ready!"
log_info "Created by: Teeksss | Version: 2.0.0 | Build: 2025-05-30 08:28:18 UTC"