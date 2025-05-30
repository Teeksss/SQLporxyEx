"""
API Module - REST API Endpoints
Created: 2025-05-29 14:06:59 UTC by Teeksss

This module contains all REST API endpoints for the Enterprise SQL Proxy System
including authentication, proxy, admin, and analytics endpoints.
"""

from fastapi import APIRouter
from app.api.main import api_router
from app.api.auth import router as auth_router
from app.api.proxy import router as proxy_router
from app.api.admin import router as admin_router

# Module metadata
__version__ = "2.0.0"
__author__ = "Teeksss"
__description__ = "REST API endpoints for Enterprise SQL Proxy System"

# API version information
API_VERSION = "v1"
API_TITLE = "Enterprise SQL Proxy API"
API_DESCRIPTION = """
Enterprise SQL Proxy System REST API

A comprehensive API for secure SQL query execution and management.

## Features

- **Authentication**: JWT-based authentication with role-based access control
- **SQL Proxy**: Secure SQL query execution across multiple database types
- **Query Management**: Query history, templates, and approval workflows
- **Administration**: User management, server configuration, and system monitoring
- **Analytics**: Comprehensive metrics and reporting

## Security

All endpoints require authentication unless otherwise specified.
API supports the following authentication methods:

- Bearer Token (JWT)
- API Key (for service accounts)

## Rate Limiting

API endpoints are rate-limited based on user roles:

- Admin: 1000 requests/hour
- Analyst: 500 requests/hour  
- PowerBI: 300 requests/hour
- Readonly: 200 requests/hour

## Error Handling

All API responses follow a consistent error format:

```json
{
    "error": "error_code",
    "detail": "Human readable error message",
    "timestamp": "2025-05-29T14:06:59Z",
    "request_id": "req_123456789"
}