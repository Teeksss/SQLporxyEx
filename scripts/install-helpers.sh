#!/bin/bash

# Enterprise SQL Proxy System - Install Helper Functions
# Created: 2025-05-30 07:49:50 UTC by Teeksss

# Global variables for passwords
POSTGRES_PASSWORD=""
REDIS_PASSWORD=""
SECRET_KEY=""

# Check system requirements
check_system_requirements() {
    log_info "Checking system requirements..."
    
    # Check OS
    if [[ "$OSTYPE" != "linux-gnu"* ]]; then
        log_error "This script is designed for Linux systems"
        exit 1
    fi
    
    # Check available space (5GB minimum)
    local available_space=$(df / | awk 'NR==2 {print $4}')
    if [[ $available_space -lt 5242880 ]]; then
        log_warning "Less than 5GB available space detected"
        log_warning "Installation may fail due to insufficient space"
    fi
    
    # Check memory (2GB minimum)
    local total_mem=$(free -m | awk 'NR==2{print $2}')
    if [[ $total_mem -lt 2048 ]]; then
        log_warning "Less than 2GB RAM detected"
        log_warning "System performance may be affected"
    fi
    
    log_success "System requirements check completed"
}

# Check and handle port conflicts
check_ports() {
    log_info "Checking required ports..."
    
    local ports=(3000 8000 5432 6379)
    local busy_ports=()
    
    for port in "${ports[@]}"; do
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            busy_ports+=($port)
        fi
    done
    
    if [[ ${#busy_ports[@]} -gt 0 ]]; then
        log_warning "The following ports are in use: ${busy_ports[*]}"
        
        echo ""
        read -p "Do you want to continue anyway? (y/N): " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_error "Installation aborted due to port conflicts"
            exit 1
        fi
    else
        log_success "All required ports are available"
    fi
}

# Generate secure passwords
generate_passwords() {
    log_info "Generating secure passwords..."
    
    SECRET_KEY=$(openssl rand -base64 32 | tr -d '=+/')
    POSTGRES_PASSWORD=$(openssl rand -base64 16 | tr -d '=+/' | head -c 16)
    REDIS_PASSWORD=$(openssl rand -base64 16 | tr -d '=+/' | head -c 16)
    
    log_success "Secure passwords generated"
}

# Create project structure
create_project_structure() {
    log_info "Creating project structure..."
    
    # Create main directories
    mkdir -p {backend/{app,tests},frontend/{src,public},scripts,nginx,monitoring,docs,k8s,logs,backups,uploads,ssl}
    
    # Create backend structure
    mkdir -p backend/app/{api/v1,core,models,services,utils}
    mkdir -p backend/{logs,uploads,backups,static}
    
    # Create frontend structure
    mkdir -p frontend/src/{components,pages,services,hooks,store,utils,types}
    mkdir -p frontend/src/assets/{images,styles}
    
    log_success "Project structure created successfully"
}

# Start services
start_services() {
    log_info "Starting Enterprise SQL Proxy System services..."
    
    # Load environment variables
    if [ -f .env ]; then
        export $(grep -v '^#' .env | xargs)
    fi
    
    # Build and start services
    log_info "Building and starting Docker containers..."
    docker-compose up -d --build
    
    log_info "Services are starting... This may take a few minutes..."
    sleep 60
}

# Verify installation
verify_installation() {
    log_info "Verifying installation..."
    
    local max_attempts=30
    local attempt=1
    
    # Check PostgreSQL
    log_info "Checking PostgreSQL..."
    while [[ $attempt -le $max_attempts ]]; do
        if docker-compose exec -T postgres pg_isready -U postgres &>/dev/null; then
            log_success "✅ PostgreSQL is healthy"
            break
        fi
        if [[ $attempt -eq $max_attempts ]]; then
            log_warning "⚠️ PostgreSQL check timeout"
        fi
        sleep 2
        ((attempt++))
    done
    
    # Check Redis
    log_info "Checking Redis..."
    attempt=1
    while [[ $attempt -le $max_attempts ]]; do
        if docker-compose exec -T redis redis-cli ping &>/dev/null; then
            log_success "✅ Redis is healthy"
            break
        fi
        if [[ $attempt -eq $max_attempts ]]; then
            log_warning "⚠️ Redis check timeout"
        fi
        sleep 2
        ((attempt++))
    done
    
    # Check Backend
    log_info "Checking Backend API..."
    attempt=1
    while [[ $attempt -le $max_attempts ]]; do
        if curl -f http://localhost:8000/health &>/dev/null; then
            log_success "✅ Backend API is healthy"
            break
        fi
        if [[ $attempt -eq $max_attempts ]]; then
            log_warning "⚠️ Backend API check timeout"
        fi
        sleep 2
        ((attempt++))
    done
    
    # Check Frontend
    log_info "Checking Frontend..."
    attempt=1
    while [[ $attempt -le $max_attempts ]]; do
        if curl -f http://localhost:3000 &>/dev/null; then
            log_success "✅ Frontend is healthy"
            break
        fi
        if [[ $attempt -eq $max_attempts ]]; then
            log_warning "⚠️ Frontend check timeout (this is normal, may take longer)"
        fi
        sleep 2
        ((attempt++))
    done
}

# Show success message
show_success_message() {
    echo -e "${GREEN}"
    echo "=================================================================="
    echo "🎉 Installation Completed Successfully!"
    echo "=================================================================="
    echo "📊 Enterprise SQL Proxy System v${SCRIPT_VERSION} is now running!"
    echo ""
    echo "🔗 Access URLs:"
    echo "  • Frontend:      http://localhost:3000"
    echo "  • Backend API:   http://localhost:8000"
    echo "  • API Docs:      http://localhost:8000/docs"
    echo "  • Health Check:  http://localhost:8000/health"
    echo ""
    echo "📋 Quick Commands:"
    echo "  • View logs:     docker-compose logs -f"
    echo "  • Stop system:   docker-compose down"
    echo "  • Restart:       docker-compose restart"
    echo "  • Status:        docker-compose ps"
    echo ""
    echo "📊 Service Status:"
    docker-compose ps 2>/dev/null || echo "Unable to get service status"
    echo ""
    echo "🔐 Generated Passwords:"
    echo "  • Database: ${POSTGRES_PASSWORD}"
    echo "  • Redis: ${REDIS_PASSWORD}"
    echo ""
    echo "✅ Created by: ${SCRIPT_AUTHOR}"
    echo "📅 Installation completed: $(date)"
    echo "=================================================================="
    echo -e "${NC}"
}