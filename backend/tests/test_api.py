"""
Complete API Testing Suite - Final Version
Created: 2025-05-29 13:19:13 UTC by Teeksss
"""

import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
from datetime import datetime, timedelta

from app.main import app
from app.core.config import settings
from app.models.user import User
from app.models.sql_server import SQLServerConnection
from app.models.query import QueryExecution


class TestAuthenticationAPI:
    """Test authentication endpoints"""
    
    def test_login_success(self, client, analyst_user):
        """Test successful login"""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "analyst",
                "password": "analyst123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == "analyst"
        assert data["user"]["role"] == "analyst"
    
    def test_login_invalid_credentials(self, client, analyst_user):
        """Test login with invalid credentials"""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "analyst",
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 401
        assert "detail" in response.json()
    
    def test_login_inactive_user(self, client, db_session):
        """Test login with inactive user"""
        user = User(
            username="inactive",
            email="inactive@test.com",
            hashed_password="hashed_password",
            role="analyst",
            is_active=False
        )
        db_session.add(user)
        db_session.commit()
        
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": "inactive",
                "password": "password"
            }
        )
        assert response.status_code == 401
    
    def test_get_current_user(self, client, auth_headers_analyst):
        """Test getting current user information"""
        response = client.get(
            "/api/v1/auth/me",
            headers=auth_headers_analyst
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "analyst"
        assert data["role"] == "analyst"


class TestQueryProxyAPI:
    """Test query execution proxy endpoints"""
    
    @patch('app.services.sql_proxy.SQLProxyService.execute_query')
    def test_execute_query_success(self, mock_execute, client, auth_headers_analyst, 
                                   test_sql_server, sample_query_request):
        """Test successful query execution"""
        mock_result = Mock()
        mock_result.success = True
        mock_result.data = [['John Doe', 'john@example.com'], ['Jane Smith', 'jane@example.com']]
        mock_result.columns = ['name', 'email']
        mock_result.execution_time_ms = 150
        mock_execute.return_value = mock_result
        
        sample_query_request["server_id"] = test_sql_server.id
        
        response = client.post(
            "/api/v1/proxy/execute",
            json=sample_query_request,
            headers=auth_headers_analyst
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert len(data["data"]) == 2
        assert data["columns"] == ['name', 'email']
        assert data["execution_time"] == 150
    
    @patch('app.services.export.ExportService.export_results')
    def test_export_query_results(self, mock_export, client, auth_headers_analyst, 
                                  sample_query_execution):
        """Test exporting query results"""
        mock_export.return_value = b"name,email\nJohn Doe,john@example.com"
        
        export_request = {
            "execution_id": sample_query_execution.id,
            "format": "csv"
        }
        
        response = client.post(
            "/api/v1/proxy/export",
            json=export_request,
            headers=auth_headers_analyst
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"


class TestAdminAPI:
    """Test admin endpoints"""
    
    def test_get_system_stats(self, client, auth_headers_admin):
        """Test getting system statistics"""
        response = client.get(
            "/api/v1/admin/stats",
            headers=auth_headers_admin
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_users" in data
        assert "total_queries" in data
        assert "total_servers" in data
    
    def test_get_audit_logs(self, client, auth_headers_admin):
        """Test getting audit logs"""
        response = client.get(
            "/api/v1/admin/audit-logs",
            headers=auth_headers_admin
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data


class TestSecurityAPI:
    """Test security-related endpoints"""
    
    def test_malicious_query_detection(self, client, auth_headers_analyst, 
                                       test_sql_server, malicious_queries):
        """Test that malicious queries are detected and blocked"""
        for malicious_query in malicious_queries:
            request = {
                "query": malicious_query,
                "server_id": test_sql_server.id
            }
            
            with patch('app.services.query_analyzer.QueryAnalyzer.analyze_query') as mock_analyze:
                mock_analyze.return_value.risk_level = "CRITICAL"
                mock_analyze.return_value.security_warnings = ["SQL injection detected"]
                
                response = client.post(
                    "/api/v1/proxy/execute",
                    json=request,
                    headers=auth_headers_analyst
                )
                
                # Should require approval or be blocked
                assert response.status_code in [403, 200]
                if response.status_code == 200:
                    data = response.json()
                    assert data.get("requires_approval") == True
    
    def test_rate_limiting(self, client, auth_headers_analyst, test_sql_server):
        """Test API rate limiting"""
        request = {
            "query": "SELECT 1",
            "server_id": test_sql_server.id
        }
        
        # Make many requests quickly
        responses = []
        for _ in range(100):
            response = client.post(
                "/api/v1/proxy/execute",
                json=request,
                headers=auth_headers_analyst
            )
            responses.append(response.status_code)
        
        # Should hit rate limit
        assert 429 in responses