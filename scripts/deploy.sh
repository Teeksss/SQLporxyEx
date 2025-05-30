#!/bin/bash
# Complete Production Deployment Script
# Created: 2025-05-29 13:19:13 UTC by Teeksss
# Version: 2.0.0

set -euo pipefail

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_FILE="/tmp/sql-proxy-deploy-$(date +%Y%m%d-%H%M%S).log"

# Default values
ENVIRONMENT="production"
DOMAIN=""
SKIP_BACKUP=false
SKIP_TESTS=false
FORCE_DEPLOY=false
DRY_RUN=false
VERBOSE=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $*${NC}" | tee -a "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $*${NC}" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $*${NC}" | tee -a "$LOG_FILE"
    exit 1
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $*${NC}" | tee -a "$LOG_FILE"
}

# Usage function
usage() {
    cat << EOF
Enterprise SQL Proxy Deployment Script v2.0.0
Created by Teeksss on 2025-05-29

Usage: $0 [OPTIONS]

OPTIONS:
    -e, --env ENVIRONMENT       Deployment environment (production, staging) [default: production]
    -d, --domain DOMAIN         Domain name for the deployment
    --skip-backup              Skip database backup before deployment
    --skip-tests               Skip running tests before deployment
    --force                    Force deployment even if tests fail
    --dry-run                  Show what would be done without executing
    -v, --verbose              Enable verbose output
    -h, --help                 Show this help message

EXAMPLES:
    $0 --env production --domain sql-proxy.company.com
    $0 --env staging --skip-backup --dry-run
    $0 --force --skip-tests

ENVIRONMENT VARIABLES:
    GIT_COMMIT_SHA             Git commit SHA for this deployment
    DOCKER_REGISTRY            Docker registry URL
    NOTIFICATION_WEBHOOK       Webhook URL for deployment notifications

EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -e|--env)
                ENVIRONMENT="$2"
                shift 2
                ;;
            -d|--domain)
                DOMAIN="$2"
                shift 2
                ;;
            --skip-backup)
                SKIP_BACKUP=true
                shift
                ;;
            --skip-tests)
                SKIP_TESTS=true
                shift
                ;;
            --force)
                FORCE_DEPLOY=true
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                ;;
        esac
    done
}

# Validate deployment environment
validate_environment() {
    log "Validating deployment environment..."
    
    # Check if environment is valid
    if [[ ! "$ENVIRONMENT" =~ ^(production|staging)$ ]]; then
        error "Invalid environment: $ENVIRONMENT. Must be 'production' or 'staging'"
    fi
    
    # Check if running as root for production
    if [[ "$ENVIRONMENT" == "production" && $EUID -eq 0 ]]; then
        warn "Running as root in production environment"
    fi
    
    # Check required commands
    local required_commands=("docker" "docker-compose" "curl" "git")
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            error "Required command not found: $cmd"
        fi
    done
    
    # Check Docker daemon
    if ! docker info &> /dev/null; then
        error "Docker daemon is not running"
    fi
    
    # Validate environment file
    local env_file=".env.$ENVIRONMENT"
    if [[ ! -f "$env_file" ]]; then
        error "Environment file not found: $env_file"
    fi
    
    # Check disk space (minimum 10GB)
    local available_space=$(df / | awk 'NR==2 {print $4}')
    if [[ $available_space -lt 10485760 ]]; then # 10GB in KB
        error "Insufficient disk space. At least 10GB required"
    fi
    
    # Check memory (minimum 4GB)
    local available_memory=$(free -m | awk 'NR==2{print $7}')
    if [[ $available_memory -lt 4096 ]]; then # 4GB in MB
        warn "Less than 4GB memory available. Performance may be affected"
    fi
    
    log "Environment validation completed successfully"
}

# Pre-deployment checks
pre_deployment_checks() {
    log "Running pre-deployment checks..."
    
    # Check Git status
    if [[ -d ".git" ]]; then
        local git_status=$(git status --porcelain)
        if [[ -n "$git_status" && "$ENVIRONMENT" == "production" ]]; then
            warn "Uncommitted changes detected in production deployment"
            if [[ "$FORCE_DEPLOY" != true ]]; then
                error "Aborting deployment. Use --force to override"
            fi
        fi
        
        # Get current commit SHA
        GIT_COMMIT_SHA=${GIT_COMMIT_SHA:-$(git rev-parse HEAD)}
        export GIT_COMMIT_SHA
        log "Deploying commit: $GIT_COMMIT_SHA"
    fi
    
    # Check if services are already running
    if docker-compose ps | grep -q "Up"; then
        warn "Some services are already running"
    fi
    
    # Validate configuration files
    local config_files=("docker-compose.yml" "docker-compose.$ENVIRONMENT.yml" "nginx/nginx.$ENVIRONMENT.conf")
    for config_file in "${config_files[@]}"; do
        if [[ -f "$config_file" ]]; then
            log "Validating $config_file..."
            if [[ "$config_file" == *"docker-compose"* ]]; then
                docker-compose -f "$config_file" config &> /dev/null || error "Invalid Docker Compose file: $config_file"
            fi
        fi
    done
    
    log "Pre-deployment checks completed"
}

# Run tests
run_tests() {
    if [[ "$SKIP_TESTS" == true ]]; then
        warn "Skipping tests as requested"
        return 0
    fi
    
    log "Running test suite..."
    
    # Backend tests
    log "Running backend tests..."
    if [[ "$DRY_RUN" != true ]]; then
        cd "$PROJECT_DIR/backend"
        if ! python -m pytest tests/ -v --tb=short; then
            if [[ "$FORCE_DEPLOY" != true ]]; then
                error "Backend tests failed. Use --force to override"
            else
                warn "Backend tests failed but continuing with --force"
            fi
        fi
        cd "$PROJECT_DIR"
    fi
    
    # Frontend tests
    log "Running frontend tests..."
    if [[ "$DRY_RUN" != true ]]; then
        cd "$PROJECT_DIR/frontend"
        if ! npm test -- --run; then
            if [[ "$FORCE_DEPLOY" != true ]]; then
                error "Frontend tests failed. Use --force to override"
            else
                warn "Frontend tests failed but continuing with --force"
            fi
        fi
        cd "$PROJECT_DIR"
    fi
    
    # Integration tests
    log "Running integration tests..."
    if [[ "$DRY_RUN" != true && -x "$PROJECT_DIR/scripts/test-integration.sh" ]]; then
        if ! "$PROJECT_DIR/scripts/test-integration.sh"; then
            if [[ "$FORCE_DEPLOY" != true ]]; then
                error "Integration tests failed. Use --force to override"
            else
                warn "Integration tests failed but continuing with --force"
            fi
        fi
    fi
    
    log "All tests completed successfully"
}

# Backup existing data
backup_data() {
    if [[ "$SKIP_BACKUP" == true ]]; then
        warn "Skipping backup as requested"
        return 0
    fi
    
    log "Creating backup before deployment..."
    
    local backup_dir="/opt/sql-proxy/backups/pre-deploy-$(date +%Y%m%d-%H%M%S)"
    
    if [[ "$DRY_RUN" != true ]]; then
        # Create backup directory
        sudo mkdir -p "$backup_dir"
        
        # Backup database
        if docker-compose ps postgres | grep -q "Up"; then
            log "Backing up PostgreSQL database..."
            docker-compose exec -T postgres pg_dump -U sql_proxy_user sql_proxy > "$backup_dir/database.sql"
        fi
        
        # Backup configuration files
        log "Backing up configuration files..."
        cp -r ./config "$backup_dir/" 2>/dev/null || true
        cp .env.* "$backup_dir/" 2>/dev/null || true
        
        # Backup data volumes
        log "Backing up data volumes..."
        if [[ -d "/opt/sql-proxy/data" ]]; then
            sudo tar -czf "$backup_dir/data-volumes.tar.gz" /opt/sql-proxy/data/
        fi
        
        log "Backup completed: $backup_dir"
        echo "$backup_dir" > /tmp/sql-proxy-last-backup.txt
    else
        log "DRY RUN: Would create backup at $backup_dir"
    fi
}

# Build Docker images
build_images() {
    log "Building Docker images..."
    
    if [[ "$DRY_RUN" != true ]]; then
        # Build backend image
        log "Building backend image..."
        docker build \
            --build-arg BUILD_VERSION="2.0.0" \
            --build-arg BUILD_DATE="$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
            --build-arg GIT_COMMIT="$GIT_COMMIT_SHA" \
            -t sql-proxy-backend:2.0.0 \
            -t sql-proxy-backend:latest \
            ./backend/
        
        # Build frontend image
        log "Building frontend image..."
        docker build \
            --build-arg BUILD_VERSION="2.0.0" \
            --build-arg BUILD_DATE="$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
            --build-arg GIT_COMMIT="$GIT_COMMIT_SHA" \
            --build-arg REACT_APP_API_URL="${REACT_APP_API_URL:-http://localhost:8000/api}" \
            --build-arg REACT_APP_WS_URL="${REACT_APP_WS_URL:-ws://localhost:8000/ws}" \
            -t sql-proxy-frontend:2.0.0 \
            -t sql-proxy-frontend:latest \
            ./frontend/
        
        # Tag images for registry if configured
        if [[ -n "${DOCKER_REGISTRY:-}" ]]; then
            log "Tagging images for registry: $DOCKER_REGISTRY"
            docker tag sql-proxy-backend:2.0.0 "$DOCKER_REGISTRY/sql-proxy-backend:2.0.0"
            docker tag sql-proxy-frontend:2.0.0 "$DOCKER_REGISTRY/sql-proxy-frontend:2.0.0"
        fi
        
        log "Docker images built successfully"
    else
        log "DRY RUN: Would build Docker images"
    fi
}

# Deploy services
deploy_services() {
    log "Deploying services..."
    
    local compose_files=("-f" "docker-compose.yml")
    if [[ -f "docker-compose.$ENVIRONMENT.yml" ]]; then
        compose_files+=("-f" "docker-compose.$ENVIRONMENT.yml")
    fi
    
    if [[ "$DRY_RUN" != true ]]; then
        # Set environment variables
        export ENVIRONMENT
        export DOMAIN
        export BUILD_VERSION="2.0.0"
        export BUILD_DATE="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
        
        # Pull latest images if using registry
        if [[ -n "${DOCKER_REGISTRY:-}" ]]; then
            log "Pulling latest images from registry..."
            docker-compose "${compose_files[@]}" pull
        fi
        
        # Stop existing services
        log "Stopping existing services..."
        docker-compose "${compose_files[@]}" down --remove-orphans
        
        # Start new services
        log "Starting services..."
        docker-compose "${compose_files[@]}" up -d
        
        # Wait for services to be healthy
        log "Waiting for services to be healthy..."
        local max_attempts=30
        local attempt=1
        
        while [[ $attempt -le $max_attempts ]]; do
            if docker-compose "${compose_files[@]}" ps | grep -q "unhealthy"; then
                log "Waiting for services to be healthy... (attempt $attempt/$max_attempts)"
                sleep 10
                ((attempt++))
            else
                break
            fi
        done
        
        if [[ $attempt -gt $max_attempts ]]; then
            error "Services failed to become healthy within timeout"
        fi
        
        log "Services deployed successfully"
    else
        log "DRY RUN: Would deploy services with compose files: ${compose_files[*]}"
    fi
}

# Post-deployment verification
post_deployment_verification() {
    log "Running post-deployment verification..."
    
    if [[ "$DRY_RUN" != true ]]; then
        # Check service health
        log "Checking service health..."
        local services=("backend" "frontend" "postgres" "redis")
        
        for service in "${services[@]}"; do
            if ! docker-compose ps "$service" | grep -q "Up (healthy)"; then
                warn "Service $service is not healthy"
            else
                log "Service $service is healthy"
            fi
        done
        
        # Test API endpoints
        log "Testing API endpoints..."
        local api_url="http://localhost:8000"
        if [[ -n "$DOMAIN" ]]; then
            api_url="https://$DOMAIN"
        fi
        
        # Health check
        if curl -s -f "$api_url/health" > /dev/null; then
            log "Health endpoint is responding"
        else
            error "Health endpoint is not responding"
        fi
        
        # API version check
        local api_version=$(curl -s "$api_url/version" | jq -r '.version' 2>/dev/null || echo "unknown")
        log "API version: $api_version"
        
        # Database connectivity check
        if docker-compose exec -T postgres pg_isready -U sql_proxy_user > /dev/null; then
            log "Database is accessible"
        else
            error "Database is not accessible"
        fi
        
        # Redis connectivity check
        if docker-compose exec -T redis redis-cli ping | grep -q "PONG"; then
            log "Redis is accessible"
        else
            error "Redis is not accessible"
        fi
        
        log "Post-deployment verification completed successfully"
    else
        log "DRY RUN: Would run post-deployment verification"
    fi
}

# Send deployment notification
send_notification() {
    local status="$1"
    local message="$2"
    
    if [[ -n "${NOTIFICATION_WEBHOOK:-}" ]]; then
        log "Sending deployment notification..."
        
        local payload=$(cat << EOF
{
    "text": "SQL Proxy Deployment $status",
    "attachments": [
        {
            "color": "$([[ "$status" == "SUCCESS" ]] && echo "good" || echo "danger")",
            "fields": [
                {
                    "title": "Environment",
                    "value": "$ENVIRONMENT",
                    "short": true
                },
                {
                    "title": "Version",
                    "value": "2.0.0",
                    "short": true
                },
                {
                    "title": "Commit",
                    "value": "${GIT_COMMIT_SHA:0:8}",
                    "short": true
                },
                {
                    "title": "Domain",
                    "value": "${DOMAIN:-localhost}",
                    "short": true
                },
                {
                    "title": "Message",
                    "value": "$message",
                    "short": false
                }
            ],
            "footer": "Deployed by Teeksss",
            "ts": $(date +%s)
        }
    ]
}
EOF
        )
        
        if [[ "$DRY_RUN" != true ]]; then
            curl -s -X POST \
                -H "Content-Type: application/json" \
                -d "$payload" \
                "$NOTIFICATION_WEBHOOK" > /dev/null || warn "Failed to send notification"
        else
            log "DRY RUN: Would send notification: $status - $message"
        fi
    fi
}

# Cleanup function
cleanup() {
    log "Cleaning up temporary files..."
    # Add any cleanup tasks here
}

# Main deployment function
main() {
    log "Starting Enterprise SQL Proxy deployment..."
    log "Environment: $ENVIRONMENT"
    log "Domain: ${DOMAIN:-localhost}"
    log "Dry Run: $DRY_RUN"
    
    # Trap cleanup on exit
    trap cleanup EXIT
    
    try {
        validate_environment
        pre_deployment_checks
        run_tests
        backup_data
        build_images
        deploy_services
        post_deployment_verification
        
        log "Deployment completed successfully!"
        send_notification "SUCCESS" "Deployment completed successfully"
        
    } catch {
        error "Deployment failed: $1"
        send_notification "FAILED" "Deployment failed: $1"
    }
}

# Error handling
try() {
    local exit_code=0
    "$@" || exit_code=$?
    return $exit_code
}

catch() {
    if [[ $? -ne 0 ]]; then
        "$@"
    fi
}

# Parse arguments and run main function
parse_args "$@"
main

log "Deployment script completed at $(date)"
log "Log file: $LOG_FILE"