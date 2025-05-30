#!/bin/bash

# Enterprise SQL Proxy System - Docker Installation Script
# Created: 2025-05-30 07:49:50 UTC by Teeksss

# Install prerequisites
install_prerequisites() {
    log_info "Installing prerequisites..."
    
    # Update package list
    sudo apt-get update -y
    
    # Install basic tools
    sudo apt-get install -y \
        curl \
        wget \
        git \
        unzip \
        nano \
        htop \
        net-tools \
        lsof \
        openssl \
        apt-transport-https \
        ca-certificates \
        gnupg \
        lsb-release \
        software-properties-common
    
    # Install Docker if not present
    install_docker
    
    # Install Docker Compose if not present
    install_docker_compose
    
    log_success "Prerequisites installed successfully"
}

# Install Docker
install_docker() {
    if command -v docker &> /dev/null; then
        log_success "Docker is already installed: $(docker --version)"
        
        # Check if Docker is running
        if ! systemctl is-active --quiet docker; then
            log_info "Starting Docker service..."
            sudo systemctl start docker
            sudo systemctl enable docker
        fi
        
        return 0
    fi
    
    log_info "Installing Docker..."
    
    # Remove old versions
    sudo apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true
    
    # Add Docker's official GPG key
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    # Add Docker repository
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Update package list
    sudo apt-get update -y
    
    # Install Docker Engine
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    
    # Add user to docker group
    sudo usermod -aG docker $USER
    
    # Start and enable Docker
    sudo systemctl start docker
    sudo systemctl enable docker
    
    log_success "Docker installed successfully: $(docker --version)"
    log_warning "Please log out and log back in for Docker group permissions to take effect"
}

# Install Docker Compose
install_docker_compose() {
    if command -v docker-compose &> /dev/null; then
        log_success "Docker Compose is already installed: $(docker-compose --version)"
        return 0
    fi
    
    log_info "Installing Docker Compose..."
    
    # Try installing via apt first
    if sudo apt-get install -y docker-compose &>/dev/null; then
        log_success "Docker Compose installed via apt: $(docker-compose --version)"
        return 0
    fi
    
    # Install latest version from GitHub
    log_info "Installing latest Docker Compose version from GitHub..."
    
    local compose_version
    compose_version=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep -Po '"tag_name": "\K.*?(?=")')
    
    if [[ -z "$compose_version" ]]; then
        compose_version="v2.24.0"  # Fallback version
    fi
    
    # Download Docker Compose
    sudo curl -L "https://github.com/docker/compose/releases/download/${compose_version}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    
    # Make executable
    sudo chmod +x /usr/local/bin/docker-compose
    
    # Create symlink
    sudo ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
    
    log_success "Docker Compose installed successfully: $(docker-compose --version)"
}

# Test Docker installation
test_docker() {
    log_info "Testing Docker installation..."
    
    # Test Docker
    if docker run --rm hello-world &>/dev/null; then
        log_success "Docker is working correctly"
    else
        log_warning "Docker test failed, but continuing installation"
    fi
    
    # Test Docker Compose
    if docker-compose --version &>/dev/null; then
        log_success "Docker Compose is working correctly"
    else
        log_error "Docker Compose test failed"
        return 1
    fi
}