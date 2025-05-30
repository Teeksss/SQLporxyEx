#!/bin/bash

# Enterprise SQL Proxy System - Complete Deployment Script
# Created: 2025-05-30 05:55:37 UTC by Teeksss
# Version: 2.0.0 Final

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="Enterprise SQL Proxy System"
VERSION="2.0.0"
CREATOR="Teeksss"
BUILD_DATE="2025-05-30 05:55:37"
ENVIRONMENT="${ENVIRONMENT:-production}"
DOCKER_REGISTRY="${DOCKER_REGISTRY:-}"
NAMESPACE="${NAMESPACE:-enterprise-sql-proxy}"

# Functions
print_banner() {
    echo -e "${PURPLE}"
    echo "=================================================================="
    echo "🏆 $APP_NAME v$VERSION"
    echo "📅 Build Date: $BUILD_DATE"
    echo "👤 Created by: $CREATOR"
    echo "🌍 Environment: $ENVIRONMENT"
    echo "🚀 Status: Production Ready"
    echo "=================================================================="
    echo -e "${NC}"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check kubectl if deploying to Kubernetes
    if [[ "$DEPLOY_TARGET" == "kubernetes" ]]; then
        if ! command -v kubectl &> /dev/null; then
            log_error "kubectl is not installed"
            exit 1
        fi
    fi
    
    # Check environment file
    if [[ ! -f ".env.${ENVIRONMENT}" ]]; then
        log_warning "Environment file .env.${ENVIRONMENT} not found, using .env"
        if [[ ! -f ".env" ]]; then
            log_error "No environment file found"
            exit 1
        fi
    fi
    
    log_success "Prerequisites check completed"
}

build_images() {
    log_info "Building Docker images..."
    
    # Build backend image
    log_info "Building backend image..."
    docker build \
        --build-arg BUILD_DATE="$BUILD_DATE" \
        --build-arg VERSION="$VERSION" \
        --build-arg CREATOR="$CREATOR" \
        -t esp-backend:$VERSION \
        -t esp-backend:latest \
        -f backend/Dockerfile.prod \
        backend/
    
    # Build frontend image
    log_info "Building frontend image..."
    docker build \
        --build-arg REACT_APP_VERSION="$VERSION" \
        --build-arg REACT_APP_ENVIRONMENT="$ENVIRONMENT" \
        --build-arg BUILD_DATE="$BUILD_DATE" \
        -t esp-frontend:$VERSION \
        -t esp-frontend:latest \
        -f frontend/Dockerfile.prod \
        frontend/
    
    log_success "Docker images built successfully"
}

push_images() {
    if [[ -n "$DOCKER_REGISTRY" ]]; then
        log_info "Pushing images to registry..."
        
        # Tag for registry
        docker tag esp-backend:$VERSION $DOCKER_REGISTRY/esp-backend:$VERSION
        docker tag esp-backend:latest $DOCKER_REGISTRY/esp-backend:latest
        docker tag esp-frontend:$VERSION $DOCKER_REGISTRY/esp-frontend:$VERSION
        docker tag esp-frontend:latest $DOCKER_REGISTRY/esp-frontend:latest
        
        # Push to registry
        docker push $DOCKER_REGISTRY/esp-backend:$VERSION
        docker push $DOCKER_REGISTRY/esp-backend:latest
        docker push $DOCKER_REGISTRY/esp-frontend:$VERSION
        docker push $DOCKER_REGISTRY/esp-frontend:latest
        
        log_success "Images pushed to registry"
    else
        log_info "No registry specified, skipping push"
    fi
}

deploy_docker_compose() {
    log_info "Deploying with Docker Compose..."
    
    # Use production compose file
    export COMPOSE_FILE="docker-compose.prod.yml"
    
    # Load environment variables
    if [[ -f ".env.${ENVIRONMENT}" ]]; then
        set -a
        source ".env.${ENVIRONMENT}"
        set +a
    fi
    
    # Stop existing containers
    docker-compose down --remove-orphans
    
    # Pull latest images
    docker-compose pull
    
    # Start services
    docker-compose up -d
    
    # Wait for services to be healthy
    log_info "Waiting for services to become healthy..."
    sleep 30
    
    # Check health
    check_health_docker_compose
    
    log_success "Docker Compose deployment completed"
}

deploy_kubernetes() {
    log_info "Deploying to Kubernetes..."
    
    # Create namespace if it doesn't exist
    kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
    
    # Apply configurations
    kubectl apply -f k8s/namespace.yaml
    kubectl apply -f k8s/postgres.yaml
    kubectl apply -f k8s/redis.yaml
    kubectl apply -f k8s/backend.yaml
    kubectl apply -f k8s/frontend.yaml
    kubectl apply -f k8s/ingress.yaml
    
    # Wait for deployments
    log_info "Waiting for deployments to be ready..."
    kubectl wait --for=condition=available --timeout=600s deployment --all -n $NAMESPACE
    
    # Check pod status
    kubectl get pods -n $NAMESPACE
    
    log_success "Kubernetes deployment completed"
}

check_health_docker_compose() {
    log_info "Checking application health..."
    
    # Wait a bit for services to fully start
    sleep 10
    
    # Check backend health
    for i in {1..30}; do
        if curl -f http://localhost:8000/health &> /dev/null; then
            log_success "Backend is healthy"
            break
        fi
        if [[ $i -eq 30 ]]; then
            log_error "Backend health check failed"
            return 1
        fi
        sleep 2
    done
    
    # Check frontend
    for i in {1..30}; do
        if curl -f http://localhost/health &> /dev/null; then
            log_success "Frontend is healthy"
            break
        fi
        if [[ $i -eq 30 ]]; then
            log_error "Frontend health check failed"
            return 1
        fi
        sleep 2
    done
    
    # Check database connectivity
    if docker-compose exec -T backend python -c "
from app.core.database import engine
try:
    with engine.connect() as conn:
        conn.execute('SELECT 1')
    print('Database connection successful')
except Exception as e:
    print(f'Database connection failed: {e}')
    exit(1)
" &> /dev/null; then
        log_success "Database connection verified"
    else
        log_error "Database connection failed"
        return 1
    fi
    
    log_success "All health checks passed"
}

check_health_kubernetes() {
    log_info "Checking Kubernetes deployment health..."
    
    # Check pod status
    if kubectl get pods -n $NAMESPACE | grep -q "Running"; then
        log_success "Pods are running"
    else
        log_error "Some pods are not running"
        kubectl get pods -n $NAMESPACE
        return 1
    fi
    
    # Check services
    kubectl get services -n $NAMESPACE
    
    log_success "Kubernetes health check completed"
}

run_database_migrations() {
    log_info "Running database migrations..."
    
    if [[ "$DEPLOY_TARGET" == "docker-compose" ]]; then
        docker-compose exec -T backend python -c "
from app.core.database import create_all_tables
create_all_tables()
print('Database tables created successfully')
"
    elif [[ "$DEPLOY_TARGET" == "kubernetes" ]]; then
        kubectl exec -n $NAMESPACE deployment/backend -- python -c "
from app.core.database import create_all_tables
create_all_tables()
print('Database tables created successfully')
"
    fi
    
    log_success "Database migrations completed"
}

create_admin_user() {
    log_info "Creating default admin user..."
    
    local script="
from app.core.database import SessionLocal
from app.models.user import User, UserRole
from app.utils.security import hash_password
import uuid

db = SessionLocal()
try:
    # Check if admin exists
    admin = db.query(User).filter(User.username == 'admin').first()
    if not admin:
        admin_password = str(uuid.uuid4())[:12]
        admin = User(
            username='admin',
            email='admin@enterprise-sql-proxy.com',
            hashed_password=hash_password(admin_password),
            first_name='System',
            last_name='Administrator',
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True
        )
        db.add(admin)
        db.commit()
        print(f'Admin user created with password: {admin_password}')
        print('IMPORTANT: Change this password immediately after first login!')
    else:
        print('Admin user already exists')
finally:
    db.close()
"
    
    if [[ "$DEPLOY_TARGET" == "docker-compose" ]]; then
        docker-compose exec -T backend python -c "$script"
    elif [[ "$DEPLOY_TARGET" == "kubernetes" ]]; then
        kubectl exec -n $NAMESPACE deployment/backend -- python -c "$script"
    fi
    
    log_success "Admin user setup completed"
}

setup_monitoring() {
    log_info "Setting up monitoring..."
    
    if [[ "$DEPLOY_TARGET" == "docker-compose" ]]; then
        # Monitoring is already included in docker-compose.prod.yml
        log_info "Monitoring services started with Docker Compose"
        
        # Check Prometheus
        for i in {1..20}; do
            if curl -f http://localhost:9090/-/healthy &> /dev/null; then
                log_success "Prometheus is healthy"
                break
            fi
            if [[ $i -eq 20 ]]; then
                log_warning "Prometheus health check failed"
            fi
            sleep 3
        done
        
        # Check Grafana
        for i in {1..20}; do
            if curl -f http://localhost:3000/api/health &> /dev/null; then
                log_success "Grafana is healthy"
                break
            fi
            if [[ $i -eq 20 ]]; then
                log_warning "Grafana health check failed"
            fi
            sleep 3
        done
        
    elif [[ "$DEPLOY_TARGET" == "kubernetes" ]]; then
        # Deploy monitoring stack for Kubernetes
        if [[ -d "k8s/monitoring" ]]; then
            kubectl apply -f k8s/monitoring/
            log_success "Monitoring stack deployed to Kubernetes"
        else
            log_warning "Kubernetes monitoring configurations not found"
        fi
    fi
}

run_smoke_tests() {
    log_info "Running smoke tests..."
    
    # Test API endpoints
    local base_url
    if [[ "$DEPLOY_TARGET" == "docker-compose" ]]; then
        base_url="http://localhost:8000"
    else
        base_url="http://localhost:8000"  # Adjust for your K8s ingress
    fi
    
    # Test health endpoint
    if curl -f "$base_url/health" &> /dev/null; then
        log_success "Health endpoint test passed"
    else
        log_error "Health endpoint test failed"
        return 1
    fi
    
    # Test API documentation
    if curl -f "$base_url/docs" &> /dev/null; then
        log_success "API documentation test passed"
    else
        log_warning "API documentation test failed"
    fi
    
    # Test OpenAPI spec
    if curl -f "$base_url/openapi.json" &> /dev/null; then
        log_success "OpenAPI spec test passed"
    else
        log_warning "OpenAPI spec test failed"
    fi
    
    log_success "Smoke tests completed"
}

backup_previous_deployment() {
    if [[ "$DEPLOY_TARGET" == "docker-compose" ]]; then
        log_info "Creating backup of previous deployment..."
        
        # Create backup directory
        mkdir -p "backups/$(date +%Y%m%d_%H%M%S)"
        local backup_dir="backups/$(date +%Y%m%d_%H%M%S)"
        
        # Backup database
        if docker-compose ps | grep -q postgres; then
            docker-compose exec -T postgres pg_dump -U postgres enterprise_sql_proxy > "$backup_dir/database_backup.sql"
            log_success "Database backup created"
        fi
        
        # Backup volumes
        docker run --rm -v "$(pwd)":/backup -v esp_postgres_data:/data alpine tar czf /backup/"$backup_dir"/postgres_data.tar.gz -C /data .
        docker run --rm -v "$(pwd)":/backup -v esp_redis_data:/data alpine tar czf /backup/"$backup_dir"/redis_data.tar.gz -C /data .
        
        log_success "Backup completed in $backup_dir"
    fi
}

cleanup_old_resources() {
    log_info "Cleaning up old resources..."
    
    # Remove old Docker images
    docker image prune -f
    
    # Remove old volumes (be careful!)
    if [[ "${CLEANUP_VOLUMES:-false}" == "true" ]]; then
        log_warning "Cleaning up old volumes..."
        docker volume prune -f
    fi
    
    log_success "Cleanup completed"
}

show_deployment_info() {
    echo -e "${CYAN}"
    echo "=================================================================="
    echo "🎉 Deployment Completed Successfully!"
    echo "=================================================================="
    echo "📊 Application: $APP_NAME v$VERSION"
    echo "🚀 Environment: $ENVIRONMENT"
    echo "📅 Deployed: $(date)"
    echo ""
    echo "🔗 Access URLs:"
    if [[ "$DEPLOY_TARGET" == "docker-compose" ]]; then
        echo "  • Frontend: http://localhost (or https://localhost if SSL enabled)"
        echo "  • Backend API: http://localhost:8000"
        echo "  • API Docs: http://localhost:8000/docs"
        echo "  • Prometheus: http://localhost:9090"
        echo "  • Grafana: http://localhost:3000 (admin/admin)"
    fi
    echo ""
    echo "📚 Documentation:"
    echo "  • User Guide: README.md"
    echo "  • API Reference: http://localhost:8000/docs"
    echo "  • Admin Guide: docs/admin-guide.md"
    echo ""
    echo "🔧 Management Commands:"
    echo "  • View logs: docker-compose logs -f"
    echo "  • Stop services: docker-compose down"
    echo "  • Update: ./scripts/deploy_complete.sh"
    echo ""
    echo "⚠️  Security Notes:"
    echo "  • Change default admin password immediately"
    echo "  • Review security settings in .env file"
    echo "  • Enable SSL/TLS for production use"
    echo "  • Configure firewall rules appropriately"
    echo ""
    echo "✅ Status: Production Ready!"
    echo "=================================================================="
    echo -e "${NC}"
}

main() {
    print_banner
    
    # Parse command line arguments
    DEPLOY_TARGET="${1:-docker-compose}"
    
    if [[ "$DEPLOY_TARGET" != "docker-compose" && "$DEPLOY_TARGET" != "kubernetes" ]]; then
        log_error "Invalid deployment target. Use 'docker-compose' or 'kubernetes'"
        echo "Usage: $0 [docker-compose|kubernetes]"
        exit 1
    fi
    
    log_info "Starting deployment with target: $DEPLOY_TARGET"
    
    # Run deployment steps
    check_prerequisites
    
    # Create backup if requested
    if [[ "${BACKUP_BEFORE_DEPLOY:-true}" == "true" ]]; then
        backup_previous_deployment
    fi
    
    build_images
    push_images
    
    if [[ "$DEPLOY_TARGET" == "docker-compose" ]]; then
        deploy_docker_compose
    elif [[ "$DEPLOY_TARGET" == "kubernetes" ]]; then
        deploy_kubernetes
    fi
    
    run_database_migrations
    create_admin_user
    setup_monitoring
    
    # Run health checks
    if [[ "$DEPLOY_TARGET" == "docker-compose" ]]; then
        check_health_docker_compose
    elif [[ "$DEPLOY_TARGET" == "kubernetes" ]]; then
        check_health_kubernetes
    fi
    
    run_smoke_tests
    
    # Cleanup if requested
    if [[ "${CLEANUP_AFTER_DEPLOY:-false}" == "true" ]]; then
        cleanup_old_resources
    fi
    
    show_deployment_info
    
    log_success "🎉 Enterprise SQL Proxy System v$VERSION deployed successfully!"
}

# Handle script interruption
trap 'log_error "Deployment interrupted"; exit 1' INT TERM

# Run main function
main "$@"