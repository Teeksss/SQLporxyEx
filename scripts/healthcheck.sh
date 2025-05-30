#!/bin/bash
# Enterprise SQL Proxy System - Health Check Script
# Created: 2025-05-29 14:45:01 UTC by Teeksss

set -e

# Check if application is responding
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health || echo "000")

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Health check passed"
    exit 0
else
    echo "❌ Health check failed (HTTP $HTTP_CODE)"
    exit 1
fi