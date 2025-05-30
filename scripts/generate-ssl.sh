#!/bin/bash
# SSL Certificate Generation Script for Enterprise SQL Proxy
# Created: 2025-05-29 12:24:15 UTC by Teeksss
# Version: 2.0.0

set -euo pipefail

# Configuration
SSL_DIR="${SSL_DIR:-./ssl}"
DOMAIN="${DOMAIN:-localhost}"
COUNTRY="${COUNTRY:-US}"
STATE="${STATE:-State}"
CITY="${CITY:-City}"
ORGANIZATION="${ORGANIZATION:-Enterprise Corp}"
ORGANIZATIONAL_UNIT="${ORGANIZATIONAL_UNIT:-IT Department}"
EMAIL="${EMAIL:-admin@localhost}"
KEY_SIZE="${KEY_SIZE:-2048}"
DAYS="${DAYS:-365}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR] $(date +'%Y-%m-%d %H:%M:%S')${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS] $(date +'%Y-%m-%d %H:%M:%S')${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING] $(date +'%Y-%m-%d %H:%M:%S')${NC} $1"
}

# Check if OpenSSL is available
check_openssl() {
    if ! command -v openssl &> /dev/null; then
        error "OpenSSL is not installed or not in PATH"
        exit 1
    fi
    
    local openssl_version=$(openssl version)
    log "Using OpenSSL: $openssl_version"
}

# Create SSL directory
create_ssl_directory() {
    if [ ! -d "$SSL_DIR" ]; then
        mkdir -p "$SSL_DIR"
        chmod 750 "$SSL_DIR"
        log "Created SSL directory: $SSL_DIR"
    else
        log "SSL directory already exists: $SSL_DIR"
    fi
}

# Generate CA private key
generate_ca_key() {
    local ca_key="$SSL_DIR/ca-key.pem"
    
    if [ -f "$ca_key" ]; then
        warning "CA private key already exists: $ca_key"
        return 0
    fi
    
    log "Generating CA private key..."
    
    openssl genrsa -out "$ca_key" 4096
    chmod 400 "$ca_key"
    
    success "CA private key generated: $ca_key"
}

# Generate CA certificate
generate_ca_cert() {
    local ca_key="$SSL_DIR/ca-key.pem"
    local ca_cert="$SSL_DIR/ca-cert.pem"
    
    if [ -f "$ca_cert" ]; then
        warning "CA certificate already exists: $ca_cert"
        return 0
    fi
    
    log "Generating CA certificate..."
    
    cat > "$SSL_DIR/ca.conf" << EOF
[req]
distinguished_name = req_distinguished_name
x509_extensions = v3_ca
prompt = no

[req_distinguished_name]
C = $COUNTRY
ST = $STATE
L = $CITY
O = $ORGANIZATION
OU = $ORGANIZATIONAL_UNIT - Certificate Authority
CN = $ORGANIZATION Root CA
emailAddress = $EMAIL

[v3_ca]
basicConstraints = critical,CA:TRUE
keyUsage = critical,keyCertSign,cRLSign
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always,issuer:always
EOF
    
    openssl req -new -x509 -days $((DAYS * 3)) -key "$ca_key" -out "$ca_cert" \
        -config "$SSL_DIR/ca.conf" -extensions v3_ca
    
    chmod 444 "$ca_cert"
    
    success "CA certificate generated: $ca_cert"
}

# Generate server private key
generate_server_key() {
    local server_key="$SSL_DIR/key.pem"
    
    if [ -f "$server_key" ]; then
        warning "Server private key already exists: $server_key"
        return 0
    fi
    
    log "Generating server private key..."
    
    openssl genrsa -out "$server_key" $KEY_SIZE
    chmod 400 "$server_key"
    
    success "Server private key generated: $server_key"
}

# Generate server certificate signing request
generate_server_csr() {
    local server_key="$SSL_DIR/key.pem"
    local server_csr="$SSL_DIR/server.csr"
    
    if [ -f "$server_csr" ]; then
        warning "Server CSR already exists: $server_csr"
        return 0
    fi
    
    log "Generating server certificate signing request..."
    
    cat > "$SSL_DIR/server.conf" << EOF
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = $COUNTRY
ST = $STATE
L = $CITY
O = $ORGANIZATION
OU = $ORGANIZATIONAL_UNIT
CN = $DOMAIN
emailAddress = $EMAIL

[v3_req]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = $DOMAIN
DNS.2 = localhost
DNS.3 = *.localhost
IP.1 = 127.0.0.1
IP.2 = ::1
EOF
    
    # Add additional domains if provided
    if [ -n "${ADDITIONAL_DOMAINS:-}" ]; then
        local dns_count=4
        IFS=',' read -ra DOMAINS <<< "$ADDITIONAL_DOMAINS"
        for domain in "${DOMAINS[@]}"; do
            echo "DNS.$dns_count = $domain" >> "$SSL_DIR/server.conf"
            ((dns_count++))
        done
    fi
    
    openssl req -new -key "$server_key" -out "$server_csr" -config "$SSL_DIR/server.conf"
    
    success "Server CSR generated: $server_csr"
}

# Generate server certificate
generate_server_cert() {
    local ca_key="$SSL_DIR/ca-key.pem"
    local ca_cert="$SSL_DIR/ca-cert.pem"
    local server_csr="$SSL_DIR/server.csr"
    local server_cert="$SSL_DIR/cert.pem"
    
    if [ -f "$server_cert" ]; then
        warning "Server certificate already exists: $server_cert"
        return 0
    fi
    
    log "Generating server certificate..."
    
    cat > "$SSL_DIR/server_cert.conf" << EOF
[v3_req]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth, clientAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = $DOMAIN
DNS.2 = localhost
DNS.3 = *.localhost
IP.1 = 127.0.0.1
IP.2 = ::1
EOF
    
    # Add additional domains if provided
    if [ -n "${ADDITIONAL_DOMAINS:-}" ]; then
        local dns_count=4
        IFS=',' read -ra DOMAINS <<< "$ADDITIONAL_DOMAINS"
        for domain in "${DOMAINS[@]}"; do
            echo "DNS.$dns_count = $domain" >> "$SSL_DIR/server_cert.conf"
            ((dns_count++))
        done
    fi
    
    openssl x509 -req -in "$server_csr" -CA "$ca_cert" -CAkey "$ca_key" \
        -CAcreateserial -out "$server_cert" -days $DAYS \
        -extensions v3_req -extfile "$SSL_DIR/server_cert.conf"
    
    chmod 444 "$server_cert"
    
    success "Server certificate generated: $server_cert"
}

# Generate client certificates (for mutual TLS)
generate_client_cert() {
    local client_name="${1:-client}"
    local client_key="$SSL_DIR/client-key.pem"
    local client_csr="$SSL_DIR/client.csr"
    local client_cert="$SSL_DIR/client-cert.pem"
    local ca_key="$SSL_DIR/ca-key.pem"
    local ca_cert="$SSL_DIR/ca-cert.pem"
    
    if [ -f "$client_cert" ]; then
        warning "Client certificate already exists: $client_cert"
        return 0
    fi
    
    log "Generating client certificate for: $client_name"
    
    # Generate client private key
    openssl genrsa -out "$client_key" $KEY_SIZE
    chmod 400 "$client_key"
    
    # Create client certificate configuration
    cat > "$SSL_DIR/client.conf" << EOF
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = $COUNTRY
ST = $STATE
L = $CITY
O = $ORGANIZATION
OU = $ORGANIZATIONAL_UNIT - Client
CN = $client_name
emailAddress = $EMAIL

[v3_req]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
extendedKeyUsage = clientAuth
EOF
    
    # Generate client CSR
    openssl req -new -key "$client_key" -out "$client_csr" -config "$SSL_DIR/client.conf"
    
    # Generate client certificate
    openssl x509 -req -in "$client_csr" -CA "$ca_cert" -CAkey "$ca_key" \
        -CAcreateserial -out "$client_cert" -days $DAYS \
        -extensions v3_req -extfile "$SSL_DIR/client.conf"
    
    chmod 444 "$client_cert"
    
    success "Client certificate generated: $client_cert"
}

# Generate DH parameters for enhanced security
generate_dhparam() {
    local dhparam_file="$SSL_DIR/dhparam.pem"
    
    if [ -f "$dhparam_file" ]; then
        warning "DH parameters already exist: $dhparam_file"
        return 0
    fi
    
    log "Generating Diffie-Hellman parameters (this may take a while)..."
    
    openssl dhparam -out "$dhparam_file" 2048
    chmod 444 "$dhparam_file"
    
    success "DH parameters generated: $dhparam_file"
}

# Verify certificates
verify_certificates() {
    local ca_cert="$SSL_DIR/ca-cert.pem"
    local server_cert="$SSL_DIR/cert.pem"
    local client_cert="$SSL_DIR/client-cert.pem"
    
    log "Verifying certificates..."
    
    # Verify CA certificate
    if openssl x509 -in "$ca_cert" -text -noout > /dev/null 2>&1; then
        success "CA certificate is valid"
    else
        error "CA certificate is invalid"
        return 1
    fi
    
    # Verify server certificate
    if openssl verify -CAfile "$ca_cert" "$server_cert" > /dev/null 2>&1; then
        success "Server certificate is valid"
    else
        error "Server certificate is invalid"
        return 1
    fi
    
    # Verify client certificate (if exists)
    if [ -f "$client_cert" ]; then
        if openssl verify -CAfile "$ca_cert" "$client_cert" > /dev/null 2>&1; then
            success "Client certificate is valid"
        else
            error "Client certificate is invalid"
            return 1
        fi
    fi
    
    return 0
}

# Display certificate information
display_certificate_info() {
    local server_cert="$SSL_DIR/cert.pem"
    
    log "Certificate Information:"
    echo "=========================="
    
    # Display certificate details
    openssl x509 -in "$server_cert" -text -noout | grep -A1 "Subject:\|Issuer:\|Not Before:\|Not After:\|DNS:\|IP Address:"
    
    echo ""
    log "Certificate files created in: $SSL_DIR"
    ls -la "$SSL_DIR"/*.pem 2>/dev/null || true
}

# Create certificate bundle
create_certificate_bundle() {
    local server_cert="$SSL_DIR/cert.pem"
    local ca_cert="$SSL_DIR/ca-cert.pem"
    local bundle_cert="$SSL_DIR/fullchain.pem"
    
    log "Creating certificate bundle..."
    
    cat "$server_cert" "$ca_cert" > "$bundle_cert"
    chmod 444 "$bundle_cert"
    
    success "Certificate bundle created: $bundle_cert"
}

# Cleanup temporary files
cleanup_temp_files() {
    log "Cleaning up temporary files..."
    
    rm -f "$SSL_DIR"/*.csr
    rm -f "$SSL_DIR"/*.conf
    rm -f "$SSL_DIR"/*.srl
    
    success "Temporary files cleaned up"
}

# Create Docker secrets (if using Docker Swarm)
create_docker_secrets() {
    if command -v docker &> /dev/null && docker info 2>/dev/null | grep -q "Swarm: active"; then
        log "Creating Docker secrets..."
        
        docker secret create sql_proxy_cert "$SSL_DIR/cert.pem" 2>/dev/null || warning "Failed to create cert secret (may already exist)"
        docker secret create sql_proxy_key "$SSL_DIR/key.pem" 2>/dev/null || warning "Failed to create key secret (may already exist)"
        docker secret create sql_proxy_ca "$SSL_DIR/ca-cert.pem" 2>/dev/null || warning "Failed to create CA secret (may already exist)"
        
        success "Docker secrets created"
    fi
}

# Set proper permissions
set_permissions() {
    log "Setting proper file permissions..."
    
    # Set directory permissions
    chmod 750 "$SSL_DIR"
    
    # Set file permissions
    chmod 400 "$SSL_DIR"/*-key.pem 2>/dev/null || true  # Private keys
    chmod 444 "$SSL_DIR"/*.pem 2>/dev/null || true      # Certificates and public files
    
    # Set ownership (if running as root)
    if [ "$(id -u)" -eq 0 ] && [ -n "${SSL_USER:-}" ]; then
        chown -R "${SSL_USER}:${SSL_GROUP:-$SSL_USER}" "$SSL_DIR"
    fi
    
    success "File permissions set"
}

# Main function
main() {
    local generate_client="${GENERATE_CLIENT:-false}"
    local generate_dhparam="${GENERATE_DHPARAM:-true}"
    
    log "=== SSL Certificate Generation Started ==="
    log "Domain: $DOMAIN"
    log "Organization: $ORGANIZATION"
    log "SSL Directory: $SSL_DIR"
    log "Key Size: $KEY_SIZE bits"
    log "Validity: $DAYS days"
    
    # Check dependencies
    check_openssl
    
    # Create SSL directory
    create_ssl_directory
    
    # Generate CA
    generate_ca_key
    generate_ca_cert
    
    # Generate server certificates
    generate_server_key
    generate_server_csr
    generate_server_cert
    
    # Generate client certificates (optional)
    if [ "$generate_client" = "true" ]; then
        generate_client_cert "sql-proxy-client"
    fi
    
    # Generate DH parameters (optional)
    if [ "$generate_dhparam" = "true" ]; then
        generate_dhparam
    fi
    
    # Create certificate bundle
    create_certificate_bundle
    
    # Verify certificates
    if verify_certificates; then
        success "All certificates verified successfully"
    else
        error "Certificate verification failed"
        exit 1
    fi
    
    # Set permissions
    set_permissions
    
    # Create Docker secrets (if applicable)
    create_docker_secrets
    
    # Display information
    display_certificate_info
    
    # Cleanup
    cleanup_temp_files
    
    success "=== SSL Certificate Generation Completed ==="
    
    echo ""
    log "Next steps:"
    echo "1. Copy the generated certificates to your application"
    echo "2. Update your configuration to use SSL"
    echo "3. Import ca-cert.pem to your client systems if needed"
    echo "4. Test the SSL configuration"
    
    if [ "$DOMAIN" = "localhost" ]; then
        warning "Certificates generated for localhost - not suitable for production use"
    fi
}

# Handle script options
while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--domain)
            DOMAIN="$2"
            shift 2
            ;;
        -o|--organization)
            ORGANIZATION="$2"
            shift 2
            ;;
        --ssl-dir)
            SSL_DIR="$2"
            shift 2
            ;;
        --key-size)
            KEY_SIZE="$2"
            shift 2
            ;;
        --days)
            DAYS="$2"
            shift 2
            ;;
        --client)
            GENERATE_CLIENT="true"
            shift
            ;;
        --no-dhparam)
            GENERATE_DHPARAM="false"
            shift
            ;;
        --additional-domains)
            ADDITIONAL_DOMAINS="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -d, --domain DOMAIN           Domain name for the certificate (default: localhost)"
            echo "  -o, --organization ORG        Organization name (default: Enterprise Corp)"
            echo "  --ssl-dir DIR                 SSL directory (default: ./ssl)"
            echo "  --key-size SIZE               RSA key size (default: 2048)"
            echo "  --days DAYS                   Certificate validity in days (default: 365)"
            echo "  --client                      Generate client certificate"
            echo "  --no-dhparam                  Skip DH parameters generation"
            echo "  --additional-domains DOMAINS  Additional domains (comma-separated)"
            echo "  -h, --help                    Show this help message"
            echo ""
            echo "Example:"
            echo "  $0 --domain sql-proxy.company.com --organization 'Company Inc' --client"
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Run main function
main