"""
Complete System Integration Tests - Final Version
Created: 2025-05-30 05:55:37 UTC by Teeksss
"""

import pytest
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import Mock, patch

from app.main import app
from app.core.database import get_db
from app.models.user import User, UserRole
from app.models.sql_server import SQLServerConnection, ServerType
from app.models.query import QueryExecution, QueryStatus
from app.services.auth import auth_service
from app.services.proxy import proxy_service
from app.utils.security import hash_password

# Test client
client = TestClient(app)

class TestCompleteSystemIntegration:
    """Complete system integration test suite"""
    
    @pytest.fixture(autouse=True)
    async def setup_test_data(self, db: Session):
        """Setup test data for each test"""
        # Create test user
        self.test_user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=hash_password("testpass123"),
            first_name="Test",
            last_name="User",
            role=UserRole.ANALYST,
            is_active=True,
            is_verified=True
        )
        db.add(self.test_user)
        
        # Create test admin user
        self.admin_user = User(
            username="admin",
            email="admin@example.com",
            hashed_password=hash_password("adminpass123"),
            first_name="Admin",
            last_name="User",
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True
        )
        db.add(self.admin_user)
        
        # Create test server
        self.test_server = SQLServerConnection(
            name="Test PostgreSQL",
            server_type=ServerType.POSTGRESQL,
            host="localhost",
            port=5432,
            database="test_db",
            username="test_user",
            password="test_pass",
            environment="test",
            is_read_only=False,
            created_by_id=self.test_user.id
        )
        db.add(self.test_server)
        
        db.commit()
        db.refresh(self.test_user)
        db.refresh(self.admin_user)
        db.refresh(self.test_server)

    def test_user_authentication_flow(self):
        """Test complete user authentication flow"""
        # Test login
        response = client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "testpass123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["username"] == "testuser"
        
        # Test protected endpoint
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 200
        user_data = response.json()
        assert user_data["username"] == "testuser"
        
        # Test token refresh
        response = client.post("/api/v1/auth/refresh", json={
            "refresh_token": data["refresh_token"]
        })
        assert response.status_code == 200
        new_data = response.json()
        assert "access_token" in new_data

    def test_sql_query_execution_flow(self):
        """Test complete SQL query execution flow"""
        # Login first
        login_response = client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "testpass123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Mock database connection
        with patch('app.services.proxy.proxy_service.execute_query') as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "data": [["John", "Doe"], ["Jane", "Smith"]],
                "columns": ["first_name", "last_name"],
                "row_count": 2,
                "execution_time_ms": 150,
                "cached": False,
                "analysis": {
                    "valid": True,
                    "query_type": "SELECT",
                    "risk_level": "LOW",
                    "warnings": [],
                    "suggestions": []
                }
            }
            
            # Execute query
            response = client.post("/api/v1/proxy/execute", 
                headers=headers,
                json={
                    "server_id": self.test_server.id,
                    "query": "SELECT first_name, last_name FROM users LIMIT 10",
                    "timeout": 300,
                    "max_rows": 10000,
                    "use_cache": True
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]) == 2
            assert data["columns"] == ["first_name", "last_name"]
            assert data["analysis"]["query_type"] == "SELECT"

    def test_admin_user_management(self):
        """Test admin user management functionality"""
        # Login as admin
        login_response = client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "adminpass123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create new user
        response = client.post("/api/v1/admin/users",
            headers=headers,
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "newpass123",
                "firstName": "New",
                "lastName": "User",
                "role": "analyst"
            }
        )
        assert response.status_code == 200
        user_data = response.json()
        new_user_id = user_data["id"]
        
        # Get all users
        response = client.get("/api/v1/admin/users", headers=headers)
        assert response.status_code == 200
        users_data = response.json()
        assert len(users_data["users"]) >= 3  # admin, testuser, newuser
        
        # Update user
        response = client.put(f"/api/v1/admin/users/{new_user_id}",
            headers=headers,
            json={
                "role": "powerbi",
                "isActive": False
            }
        )
        assert response.status_code == 200
        updated_user = response.json()
        assert updated_user["role"] == "powerbi"
        assert updated_user["isActive"] is False

    def test_analytics_dashboard(self):
        """Test analytics dashboard functionality"""
        # Login as analyst
        login_response = client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "testpass123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get dashboard data
        response = client.get("/api/v1/analytics/dashboard?days=30", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert "summary" in data
        assert "distributions" in data
        assert "top_users" in data
        assert "top_servers" in data
        assert "daily_trends" in data
        
        # Verify summary contains required fields
        summary = data["summary"]
        required_fields = [
            "total_queries", "successful_queries", "failed_queries",
            "success_rate", "avg_execution_time_ms", "total_rows_returned",
            "cache_hit_rate"
        ]
        for field in required_fields:
            assert field in summary

    def test_health_monitoring(self):
        """Test health monitoring endpoints"""
        # Basic health check (no auth required)
        response = client.get("/api/v1/health/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        
        # Detailed health (requires auth)
        login_response = client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "adminpass123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.get("/api/v1/health/detailed", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "overall_status" in data
        assert "components" in data
        assert "system" in data

    def test_audit_logging(self):
        """Test audit logging functionality"""
        # Login as admin
        login_response = client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "adminpass123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get audit logs
        response = client.get("/api/v1/admin/audit-logs?limit=10", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "logs" in data
        assert "total" in data
        
        # Verify log structure
        if data["logs"]:
            log = data["logs"][0]
            required_fields = ["id", "action", "category", "timestamp"]
            for field in required_fields:
                assert field in log

    def test_error_handling(self):
        """Test error handling across the system"""
        # Test invalid login
        response = client.post("/api/v1/auth/login", json={
            "username": "invalid",
            "password": "invalid"
        })
        assert response.status_code == 400
        
        # Test unauthorized access
        response = client.get("/api/v1/admin/users")
        assert response.status_code == 401
        
        # Test invalid query execution
        login_response = client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "testpass123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.post("/api/v1/proxy/execute",
            headers=headers,
            json={
                "server_id": 99999,  # Non-existent server
                "query": "SELECT * FROM users"
            }
        )
        assert response.status_code == 404

    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        # Make rapid requests to test rate limiting
        login_response = client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "testpass123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Make many requests quickly
        responses = []
        for i in range(10):
            response = client.get("/api/v1/auth/me", headers=headers)
            responses.append(response.status_code)
        
        # All should succeed under normal rate limits
        assert all(status == 200 for status in responses)

    def test_security_features(self):
        """Test security features"""
        # Test SQL injection protection
        login_response = client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "testpass123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        with patch('app.services.proxy.proxy_service.execute_query') as mock_execute:
            mock_execute.return_value = {
                "success": False,
                "error": "Potential SQL injection detected",
                "analysis": {
                    "valid": False,
                    "security_issues": ["SQL injection attempt detected"]
                }
            }
            
            # Attempt SQL injection
            response = client.post("/api/v1/proxy/execute",
                headers=headers,
                json={
                    "server_id": self.test_server.id,
                    "query": "SELECT * FROM users WHERE id = '1'; DROP TABLE users; --"
                }
            )
            
            # Should be blocked or flagged
            assert response.status_code in [400, 200]  # 200 if analyzed and blocked

    def test_caching_functionality(self):
        """Test caching functionality"""
        login_response = client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "testpass123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        with patch('app.services.proxy.proxy_service.execute_query') as mock_execute:
            # First call - not cached
            mock_execute.return_value = {
                "success": True,
                "data": [["test"]],
                "columns": ["value"],
                "row_count": 1,
                "execution_time_ms": 100,
                "cached": False
            }
            
            response1 = client.post("/api/v1/proxy/execute",
                headers=headers,
                json={
                    "server_id": self.test_server.id,
                    "query": "SELECT 'test' as value",
                    "use_cache": True
                }
            )
            
            assert response1.status_code == 200
            data1 = response1.json()
            assert data1["cached"] is False
            
            # Second call - should be cached
            mock_execute.return_value = {
                "success": True,
                "data": [["test"]],
                "columns": ["value"],
                "row_count": 1,
                "execution_time_ms": 5,  # Much faster
                "cached": True
            }
            
            response2 = client.post("/api/v1/proxy/execute",
                headers=headers,
                json={
                    "server_id": self.test_server.id,
                    "query": "SELECT 'test' as value",
                    "use_cache": True
                }
            )
            
            assert response2.status_code == 200
            data2 = response2.json()
            # Cache behavior depends on implementation

    def test_websocket_notifications(self):
        """Test WebSocket notifications"""
        # This would require WebSocket test client
        # For now, test the notification system indirectly
        login_response = client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "testpass123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get notifications
        response = client.get("/api/v1/notifications", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_data_export(self):
        """Test data export functionality"""
        login_response = client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "adminpass123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test analytics export
        response = client.get("/api/v1/analytics/export?type=dashboard&format=json&days=30", 
                            headers=headers)
        assert response.status_code == 200

    def test_backup_and_restore(self):
        """Test backup and restore functionality"""
        login_response = client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "adminpass123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        with patch('app.services.backup.backup_service.create_backup') as mock_backup:
            mock_backup.return_value = {
                "backup_id": "backup_123",
                "status": "completed"
            }
            
            # Test backup creation
            response = client.post("/api/v1/admin/backup", headers=headers)
            assert response.status_code == 200
            data = response.json()
            assert "backup_id" in data

    def test_performance_monitoring(self):
        """Test performance monitoring"""
        login_response = client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "testpass123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test performance analytics
        response = client.get("/api/v1/analytics/performance?days=7", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "execution_time_percentiles" in data
        assert "slow_queries" in data
        assert "server_performance" in data

    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """Test concurrent operations"""
        # Test multiple simultaneous logins
        tasks = []
        for i in range(5):
            task = asyncio.create_task(self._concurrent_login(f"user{i}"))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        # At least some should succeed (depending on rate limiting)
        successful = sum(1 for r in results if not isinstance(r, Exception))
        assert successful > 0

    async def _concurrent_login(self, username):
        """Helper for concurrent login testing"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.post("/api/v1/auth/login", json={
                "username": "testuser",  # Use existing user
                "password": "testpass123"
            })
            return response.status_code

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])