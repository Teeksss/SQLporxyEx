"""
Tests Module - Test Suite for Enterprise SQL Proxy System
Created: 2025-05-29 14:11:08 UTC by Teeksss

This module contains all tests for the Enterprise SQL Proxy System
including unit tests, integration tests, and test utilities.
"""

import pytest
import asyncio
from typing import Generator, Any
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Test configuration
TEST_CONFIG = {
    "database_url": "sqlite:///./test.db",
    "test_user_username": "test_user",
    "test_user_email": "test@example.com",
    "test_user_password": "TestPassword123!",
    "test_server_name": "Test SQL Server",
    "test_server_host": "localhost",
    "test_server_port": 1433,
    "test_server_database": "test_db",
    "parallel_tests": True,
    "coverage_threshold": 80
}

# Test metadata
TEST_METADATA = {
    "version": "2.0.0",
    "author": "Teeksss",
    "description": "Comprehensive test suite for Enterprise SQL Proxy System",
    "test_categories": [
        "unit_tests",
        "integration_tests", 
        "api_tests",
        "security_tests",
        "performance_tests"
    ],
    "total_test_files": 15,
    "estimated_test_count": 250,
    "coverage_target": "90%",
    "last_updated": "2025-05-29T14:11:08Z"
}

# Export all test components
__all__ = [
    # Configuration
    "TEST_CONFIG",
    "TEST_METADATA",
    
    # Test utilities
    "TestDatabase",
    "TestDataFactory",
    "TestAuthHelper", 
    "TestMockHelper",
    
    # Fixtures
    "test_db",
    "test_client",
    "test_user",
    "test_server",
    "test_query",
    "auth_headers",
    "admin_headers",
    "mock_db_session",
    "mock_redis",
    
    # Test runners
    "run_unit_tests",
    "run_integration_tests",
    "run_api_tests",
    "run_security_tests",
    "run_performance_tests",
    "run_all_tests",
    
    # Utilities
    "validate_test_config",
    "get_test_info",
    "test_health_check"
]