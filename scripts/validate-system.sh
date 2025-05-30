#!/bin/bash
# Complete System Validation Script - Final Version
# Created: 2025-05-29 13:44:06 UTC by Teeksss
# Version: 2.0.0

set -euo pipefail

# [Previous content continues...]

validate_performance() {
    info "Validating performance..."
    
    # Check system resources
    check
    local memory_usage=$(free | awk 'FNR==2{printf "%.0f", $3/($3+$4)*100}')
    if [[ "$memory_usage" -lt 80 ]]; then
        log "Memory usage is acceptable ($memory_usage%)"
    else
        warn "High memory usage detected ($memory_usage%)"
    fi
    
    check
    local disk_usage=$(df / | awk 'FNR==2{print $5}' | sed 's/%//')
    if [[ "$disk_usage" -lt 85 ]]; then
        log "Disk usage is acceptable ($disk_usage%)"
    else
        warn "High disk usage detected ($disk_usage%)"
    fi
    
    # API response time test
    check
    local response_time=$(curl -o /dev/null -s -w '%{time_total}' http://localhost:8000/health)
    if (( $(echo "$response_time < 1.0" | bc -l) )); then
        log "API response time is good (${response_time}s)"
    else
        warn "API response time is slow (${response_time}s)"
    fi
}

validate_backup_system() {
    info "Validating backup system..."
    
    # Check backup directory
    check
    if [[ -d "/opt/sql-proxy/backups" ]]; then
        log "Backup directory exists"
        
        # Check recent backups
        local recent_backups=$(find /opt/sql-proxy/backups -name "*.sql" -mtime -7 | wc -l)
        if [[ "$recent_backups" -gt 0 ]]; then
            log "Recent backups found ($recent_backups files)"
        else
            warn "No recent backups found"
        fi
    else
        warn "Backup directory does not exist"
    fi
    
    # Test backup script
    check
    if [[ -x "scripts/backup.sh" ]]; then
        log "Backup script is executable"
    else
        error "Backup script is not executable"
    fi
}

# Main validation function
main() {
    echo -e "${BLUE}"
    echo "=============================================="
    echo "Enterprise SQL Proxy System Validation"
    echo "Version: 2.0.0"
    echo "Date: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
    echo "Validator: Teeksss"
    echo "=============================================="
    echo -e "${NC}"
    
    validate_docker
    validate_containers
    validate_network_connectivity
    validate_api_endpoints
    validate_frontend
    validate_database
    validate_redis
    validate_ssl_certificates
    validate_logs
    validate_monitoring
    validate_security
    validate_performance
    validate_backup_system
    
    # Final summary
    echo ""
    echo -e "${BLUE}=============================================="
    echo "VALIDATION SUMMARY"
    echo "=============================================="
    echo -e "Total Checks: $TOTAL_CHECKS"
    echo -e "${GREEN}Passed: $PASSED_CHECKS${NC}"
    echo -e "${YELLOW}Warnings: $WARNING_CHECKS${NC}"
    echo -e "${RED}Failed: $FAILED_CHECKS${NC}"
    echo ""
    
    local success_rate=$((PASSED_CHECKS * 100 / TOTAL_CHECKS))
    echo -e "Success Rate: $success_rate%"
    
    if [[ $FAILED_CHECKS -eq 0 ]]; then
        echo -e "${GREEN}✓ System validation PASSED${NC}"
        echo -e "${GREEN}System is ready for production use!${NC}"
        exit 0
    else
        echo -e "${RED}✗ System validation FAILED${NC}"
        echo -e "${RED}Please fix the errors before proceeding to production${NC}"
        exit 1
    fi
}

# Run main function
main "$@"