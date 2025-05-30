"""
Complete Testing Framework Configuration
Created: 2025-05-29 13:14:20 UTC by Teeksss
"""

import pytest
import asyncio
from typing import Generator, AsyncGenerator
import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
import redis
from unittest.mock import Mock, AsyncMock
import tempfile
import shutil
from pathlib import Path

from app.main import app
from app.core.database import Base, get_db
from app.core.config import settings
from app.models.user import User
from app.models.sql_server import SQLServerConnection
from app.models.query import QueryExecution, QueryWhitelist
from app.services.auth import create_access_token
from app.services.user import hash_password

# Test database configuration
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"

# Create test engine
test_engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    # Create tables
    Base.metadata.create_all(bind=test_engine)
    
    # Create session
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        # Drop tables after test
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def override_get_db(db_session):
    """Override the get_db dependency to use test database."""
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client(override_get_db):
    """Create a test client."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="function")
async def async_client(override_get_db):
    """Create an async test client."""
    async with httpx.AsyncClient(app=app, base_url="http://test") as async_test_client:
        yield async_test_client


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    mock_redis_client = Mock()
    mock_redis_client.get = AsyncMock(return_value=None)
    mock_redis_client.set = AsyncMock(return_value=True)
    mock_redis_client.delete = AsyncMock(return_value=True)
    mock_redis_client.exists = AsyncMock(return_value=False)
    mock_redis_client.lpush = AsyncMock(return_value=1)
    mock_redis_client.rpop = AsyncMock(return_value=None)
    return mock_redis_client


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_directory = tempfile.mkdtemp()
    yield Path(temp_directory)
    shutil.rmtree(temp_directory)


# User fixtures
@pytest.fixture
def admin_user(db_session):
    """Create an admin user for testing."""
    user = User(
        username="admin",
        email="admin@test.com",
        hashed_password=hash_password("admin123"),
        role="admin",
        is_active=True,
        is_verified=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def analyst_user(db_session):
    """Create an analyst user for testing."""
    user = User(
        username="analyst",
        email="analyst@test.com",
        hashed_password=hash_password("analyst123"),
        role="analyst",
        is_active=True,
        is_verified=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def readonly_user(db_session):
    """Create a readonly user for testing."""
    user = User(
        username="readonly",
        email="readonly@test.com",
        hashed_password=hash_password("readonly123"),
        role="readonly",
        is_active=True,
        is_verified=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


# Authentication fixtures
@pytest.fixture
def admin_token(admin_user):
    """Create admin authentication token."""
    return create_access_token(data={"sub": admin_user.username})


@pytest.fixture
def analyst_token(analyst_user):
    """Create analyst authentication token."""
    return create_access_token(data={"sub": analyst_user.username})


@pytest.fixture
def readonly_token(readonly_user):
    """Create readonly authentication token."""
    return create_access_token(data={"sub": readonly_user.username})


@pytest.fixture
def auth_headers_admin(admin_token):
    """Create authorization headers for admin."""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def auth_headers_analyst(analyst_token):
    """Create authorization headers for analyst."""
    return {"Authorization": f"Bearer {analyst_token}"}


@pytest.fixture
def auth_headers_readonly(readonly_token):
    """Create authorization headers for readonly."""
    return {"Authorization": f"Bearer {readonly_token}"}


# SQL Server fixtures
@pytest.fixture
def test_sql_server(db_session):
    """Create a test SQL server connection."""
    server = SQLServerConnection(
        name="Test SQL Server",
        description="Test database server",
        server_type="mssql",
        host="localhost",
        port=1433,
        database="test_db",
        username="test_user",
        password="test_password",
        environment="test",
        is_read_only=True,
        is_active=True,
        health_status="healthy"
    )
    db_session.add(server)
    db_session.commit()
    db_session.refresh(server)
    return server


@pytest.fixture
def test_postgresql_server(db_session):
    """Create a test PostgreSQL server connection."""
    server = SQLServerConnection(
        name="Test PostgreSQL Server",
        description="Test PostgreSQL database server",
        server_type="postgresql",
        host="localhost",
        port=5432,
        database="test_db",
        username="test_user",
        password="test_password",
        environment="test",
        is_read_only=False,
        is_active=True,
        health_status="healthy"
    )
    db_session.add(server)
    db_session.commit()
    db_session.refresh(server)
    return server


# Query fixtures
@pytest.fixture
def sample_query_execution(db_session, analyst_user, test_sql_server):
    """Create a sample query execution."""
    execution = QueryExecution(
        query_hash="test_hash_123",
        user_id=analyst_user.id,
        server_id=test_sql_server.id,
        original_query="SELECT * FROM users",
        query_preview="SELECT * FROM users",
        status="success",
        execution_time_ms=150,
        rows_returned=10
    )
    db_session.add(execution)
    db_session.commit()
    db_session.refresh(execution)
    return execution


@pytest.fixture
def sample_query_whitelist(db_session, admin_user):
    """Create a sample query whitelist entry."""
    whitelist = QueryWhitelist(
        query_hash="approved_hash_123",
        original_query="SELECT COUNT(*) FROM users",
        normalized_query="SELECT COUNT(*) FROM USERS",
        query_type="SELECT",
        risk_level="LOW",
        status="approved",
        created_by=admin_user.id,
        approved_by=admin_user.id
    )
    db_session.add(whitelist)
    db_session.commit()
    db_session.refresh(whitelist)
    return whitelist


# Mock external services
@pytest.fixture
def mock_smtp():
    """Mock SMTP service."""
    with pytest.mock.patch('aiosmtplib.send') as mock_send:
        mock_send.return_value = True
        yield mock_send


@pytest.fixture
def mock_ldap():
    """Mock LDAP service."""
    mock_ldap_client = Mock()
    mock_ldap_client.simple_bind_s = Mock(return_value=True)
    mock_ldap_client.search_s = Mock(return_value=[
        ('cn=testuser,ou=users,dc=test,dc=com', {
            'mail': [b'testuser@test.com'],
            'sAMAccountName': [b'testuser'],
            'memberOf': [b'cn=analysts,ou=groups,dc=test,dc=com']
        })
    ])
    return mock_ldap_client


@pytest.fixture
def mock_sql_connection():
    """Mock SQL database connection."""
    mock_connection = Mock()
    mock_cursor = Mock()
    
    mock_cursor.fetchall.return_value = [
        ['John Doe', 'john@example.com'],
        ['Jane Smith', 'jane@example.com']
    ]
    mock_cursor.description = [
        ('name',), ('email',)
    ]
    mock_cursor.rowcount = 2
    
    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
    mock_connection.cursor.return_value.__exit__.return_value = None
    
    return mock_connection


# Data fixtures
@pytest.fixture
def sample_query_request():
    """Sample query request data."""
    return {
        "query": "SELECT * FROM users WHERE active = 1",
        "server_id": 1,
        "parameters": {},
        "timeout": 30
    }


@pytest.fixture
def sample_server_data():
    """Sample server configuration data."""
    return {
        "name": "Production SQL Server",
        "description": "Main production database",
        "server_type": "mssql",
        "host": "prod-sql.example.com",
        "port": 1433,
        "database": "prod_db",
        "username": "sql_user",
        "password": "secure_password",
        "environment": "production",
        "is_read_only": False,
        "use_ssl": True,
        "verify_ssl_cert": True
    }


@pytest.fixture
def sample_user_data():
    """Sample user creation data."""
    return {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "SecurePass123!",
        "role": "analyst",
        "is_active": True
    }


# Performance testing fixtures
@pytest.fixture
def performance_test_queries():
    """Sample queries for performance testing."""
    return [
        "SELECT COUNT(*) FROM users",
        "SELECT * FROM users WHERE created_at > '2023-01-01'",
        "SELECT u.*, p.name as profile_name FROM users u LEFT JOIN profiles p ON u.id = p.user_id",
        "SELECT DATE(created_at) as date, COUNT(*) as count FROM users GROUP BY DATE(created_at)",
        "SELECT * FROM users WHERE email LIKE '%@example.com' ORDER BY created_at DESC LIMIT 100"
    ]


# Security testing fixtures
@pytest.fixture
def malicious_queries():
    """Sample malicious queries for security testing."""
    return [
        "SELECT * FROM users; DROP TABLE users; --",
        "SELECT * FROM users WHERE id = 1 OR 1=1",
        "SELECT * FROM users UNION SELECT username, password FROM admin_users",
        "EXEC xp_cmdshell 'dir'",
        "SELECT * FROM users WHERE name = 'admin' AND password = '' OR '1'='1'"
    ]


# Configuration fixtures
@pytest.fixture
def test_settings():
    """Test application settings."""
    return {
        "SECRET_KEY": "test-secret-key-for-testing-only",
        "ACCESS_TOKEN_EXPIRE_MINUTES": 30,
        "DATABASE_URL": SQLALCHEMY_TEST_DATABASE_URL,
        "REDIS_URL": "redis://localhost:6379/1",
        "EMAILS_ENABLED": False,
        "NOTIFICATIONS_ENABLED": False,
        "RATE_LIMIT_ENABLED": False,
        "QUERY_APPROVAL_REQUIRED": False,
        "DEBUG": True,
        "TESTING": True
    }


# Helper functions for tests
@pytest.fixture
def create_test_user():
    """Helper function to create test users."""
    def _create_user(db_session, username="testuser", email="test@example.com", role="analyst"):
        user = User(
            username=username,
            email=email,
            hashed_password=hash_password("testpass123"),
            role=role,
            is_active=True,
            is_verified=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user
    return _create_user


@pytest.fixture
def create_test_server():
    """Helper function to create test servers."""
    def _create_server(db_session, name="Test Server", server_type="mssql", host="localhost"):
        server = SQLServerConnection(
            name=name,
            description=f"Test {server_type} server",
            server_type=server_type,
            host=host,
            port=1433 if server_type == "mssql" else 5432,
            database="test_db",
            username="test_user",
            password="test_password",
            environment="test",
            is_read_only=True,
            is_active=True,
            health_status="healthy"
        )
        db_session.add(server)
        db_session.commit()
        db_session.refresh(server)
        return server
    return _create_server


# Cleanup fixtures
@pytest.fixture(autouse=True)
def cleanup_test_files(temp_dir):
    """Automatically cleanup test files after each test."""
    yield
    # Cleanup is handled by temp_dir fixture


# Integration test fixtures
@pytest.fixture
def integration_test_data():
    """Complete dataset for integration testing."""
    return {
        "users": [
            {"username": "admin1", "email": "admin1@test.com", "role": "admin"},
            {"username": "analyst1", "email": "analyst1@test.com", "role": "analyst"},
            {"username": "analyst2", "email": "analyst2@test.com", "role": "analyst"},
            {"username": "readonly1", "email": "readonly1@test.com", "role": "readonly"},
        ],
        "servers": [
            {"name": "SQL Server 1", "type": "mssql", "host": "sql1.test.com"},
            {"name": "PostgreSQL 1", "type": "postgresql", "host": "pg1.test.com"},
            {"name": "MySQL 1", "type": "mysql", "host": "mysql1.test.com"},
        ],
        "queries": [
            "SELECT COUNT(*) FROM users",
            "SELECT * FROM users WHERE role = 'admin'",
            "SELECT u.*, r.name as role_name FROM users u JOIN roles r ON u.role_id = r.id",
        ]
    }