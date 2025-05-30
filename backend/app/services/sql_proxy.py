"""
Complete SQL Proxy Service - Final Version
Created: 2025-05-29 14:30:36 UTC by Teeksss
"""

import logging
import asyncio
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from contextlib import asynccontextmanager
import sqlalchemy
from sqlalchemy import create_engine, text, MetaData
from sqlalchemy.pool import StaticPool
from sqlalchemy.exc import SQLAlchemyError
import pandas as pd

from app.core.config import settings
from app.core.database import get_db_session
from app.models.sql_server import SQLServerConnection, ServerType, HealthStatus
from app.models.query import QueryExecution, QueryStatus, QueryType, RiskLevel
from app.models.user import User, UserRole
from app.services.cache import cache_service
from app.services.query_analyzer import QueryAnalyzer
from app.services.audit import audit_service

logger = logging.getLogger(__name__)


class SQLProxyService:
    """Complete SQL Proxy Service"""
    
    def __init__(self):
        self.connection_pools = {}
        self.active_connections = {}
        self.query_cache = {}
        self.stats = {
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "cached_queries": 0,
            "total_execution_time": 0,
            "avg_execution_time": 0,
            "active_connections": 0,
            "total_connections": 0
        }
        self.query_analyzer = None
        
    async def initialize(self):
        """Initialize SQL proxy service"""
        try:
            self.query_analyzer = QueryAnalyzer()
            await self.query_analyzer.initialize()
            
            # Initialize connection pools for active servers
            await self._initialize_connection_pools()
            
            # Start connection health monitoring
            asyncio.create_task(self._monitor_connections())
            
            logger.info("✅ SQL Proxy Service initialized")
            
        except Exception as e:
            logger.error(f"❌ SQL Proxy Service initialization failed: {e}")
            raise
    
    async def execute_query(
        self,
        query: str,
        server_id: int,
        user_id: int,
        parameters: Optional[Dict[str, Any]] = None,
        timeout: int = None,
        max_rows: int = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """Execute SQL query"""
        
        start_time = time.time()
        execution_id = None
        
        try:
            # Get server and user
            with get_db_session() as db:
                server = db.query(SQLServerConnection).filter(
                    SQLServerConnection.id == server_id,
                    SQLServerConnection.is_active == True
                ).first()
                
                user = db.query(User).filter(User.id == user_id).first()
                
                if not server:
                    raise ValueError(f"Server {server_id} not found or inactive")
                
                if not user:
                    raise ValueError(f"User {user_id} not found")
            
            # Check user permissions for server
            if not self._check_server_permissions(user, server):
                raise PermissionError(f"User {user.username} does not have access to server {server.name}")
            
            # Analyze query
            analysis_result = self.query_analyzer.analyze_query(
                query, 
                user.role.value, 
                server.environment.value
            )
            
            if not analysis_result["valid"]:
                raise ValueError(f"Query validation failed: {analysis_result['error']}")
            
            # Check if approval required
            if analysis_result.get("requires_approval", False):
                raise ValueError("Query requires approval before execution")
            
            # Create query execution record
            with get_db_session() as db:
                query_execution = QueryExecution(
                    query_hash=analysis_result["metadata"]["query_hash"],
                    user_id=user_id,
                    server_id=server_id,
                    original_query=query,
                    normalized_query=analysis_result["metadata"]["normalized_query"],
                    query_preview=query[:200] + "..." if len(query) > 200 else query,
                    query_type=analysis_result["query_type"],
                    status=QueryStatus.PENDING,
                    risk_level=analysis_result["risk_level"],
                    security_warnings=analysis_result.get("security_issues", []),
                    requires_approval=analysis_result.get("requires_approval", False),
                    timeout_seconds=timeout or settings.QUERY_TIMEOUT,
                    parameters=parameters,
                    started_at=datetime.utcnow()
                )
                
                db.add(query_execution)
                db.commit()
                db.refresh(query_execution)
                execution_id = query_execution.id
            
            # Check cache first
            if use_cache and analysis_result["query_type"] == QueryType.SELECT:
                cached_result = await self._get_cached_result(
                    analysis_result["metadata"]["query_hash"],
                    server_id,
                    parameters
                )
                
                if cached_result:
                    # Update execution record
                    with get_db_session() as db:
                        query_execution = db.query(QueryExecution).filter(
                            QueryExecution.id == execution_id
                        ).first()
                        
                        query_execution.status = QueryStatus.SUCCESS
                        query_execution.completed_at = datetime.utcnow()
                        query_execution.execution_time_ms = int((time.time() - start_time) * 1000)
                        query_execution.rows_returned = cached_result["row_count"]
                        query_execution.is_cached = True
                        query_execution.cache_hit = True
                        
                        db.commit()
                    
                    self.stats["cached_queries"] += 1
                    self.stats["total_queries"] += 1
                    
                    # Log query execution
                    await audit_service.log_event(
                        action="query_executed_cached",
                        user_id=user_id,
                        resource_type="query",
                        resource_id=str(execution_id),
                        details={
                            "server_id": server_id,
                            "query_hash": analysis_result["metadata"]["query_hash"],
                            "execution_time_ms": query_execution.execution_time_ms,
                            "rows_returned": cached_result["row_count"],
                            "cached": True
                        },
                        category="query"
                    )
                    
                    return {
                        "success": True,
                        "execution_id": execution_id,
                        "data": cached_result["data"],
                        "columns": cached_result["columns"],
                        "row_count": cached_result["row_count"],
                        "execution_time_ms": query_execution.execution_time_ms,
                        "cached": True,
                        "analysis": analysis_result
                    }
            
            # Execute query
            result = await self._execute_query_on_server(
                query=analysis_result["metadata"]["normalized_query"],
                server=server,
                parameters=parameters,
                timeout=timeout or settings.QUERY_TIMEOUT,
                max_rows=max_rows or settings.MAX_RESULT_ROWS
            )
            
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            # Update execution record
            with get_db_session() as db:
                query_execution = db.query(QueryExecution).filter(
                    QueryExecution.id == execution_id
                ).first()
                
                query_execution.status = QueryStatus.SUCCESS if result["success"] else QueryStatus.FAILED
                query_execution.completed_at = datetime.utcnow()
                query_execution.execution_time_ms = execution_time_ms
                query_execution.rows_returned = result.get("row_count", 0)
                query_execution.rows_affected = result.get("rows_affected", 0)
                query_execution.result_size_bytes = result.get("result_size_bytes", 0)
                query_execution.error_message = result.get("error")
                query_execution.is_cached = False
                query_execution.cache_hit = False
                
                db.commit()
            
            # Cache result if successful SELECT query
            if (result["success"] and 
                analysis_result["query_type"] == QueryType.SELECT and
                result.get("row_count", 0) > 0):
                await self._cache_result(
                    analysis_result["metadata"]["query_hash"],
                    server_id,
                    parameters,
                    result
                )
            
            # Update stats
            self.stats["total_queries"] += 1
            if result["success"]:
                self.stats["successful_queries"] += 1
            else:
                self.stats["failed_queries"] += 1
            
            self.stats["total_execution_time"] += execution_time_ms
            self.stats["avg_execution_time"] = (
                self.stats["total_execution_time"] / self.stats["total_queries"]
            )
            
            # Log query execution
            await audit_service.log_event(
                action="query_executed",
                user_id=user_id,
                resource_type="query",
                resource_id=str(execution_id),
                details={
                    "server_id": server_id,
                    "query_hash": analysis_result["metadata"]["query_hash"],
                    "execution_time_ms": execution_time_ms,
                    "rows_returned": result.get("row_count", 0),
                    "rows_affected": result.get("rows_affected", 0),
                    "success": result["success"],
                    "cached": False,
                    "risk_level": analysis_result["risk_level"].value
                },
                severity="info" if result["success"] else "warning",
                category="query"
            )
            
            return {
                "success": result["success"],
                "execution_id": execution_id,
                "data": result.get("data"),
                "columns": result.get("columns"),
                "row_count": result.get("row_count", 0),
                "rows_affected": result.get("rows_affected", 0),
                "execution_time_ms": execution_time_ms,
                "cached": False,
                "error": result.get("error"),
                "analysis": analysis_result
            }
            
        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            # Update execution record if created
            if execution_id:
                try:
                    with get_db_session() as db:
                        query_execution = db.query(QueryExecution).filter(
                            QueryExecution.id == execution_id
                        ).first()
                        
                        if query_execution:
                            query_execution.status = QueryStatus.FAILED
                            query_execution.completed_at = datetime.utcnow()
                            query_execution.execution_time_ms = execution_time_ms
                            query_execution.error_message = str(e)
                            
                            db.commit()
                except:
                    pass
            
            # Update stats
            self.stats["total_queries"] += 1
            self.stats["failed_queries"] += 1
            
            # Log query failure
            await audit_service.log_event(
                action="query_failed",
                user_id=user_id,
                resource_type="query",
                resource_id=str(execution_id) if execution_id else None,
                details={
                    "server_id": server_id,
                    "error": str(e),
                    "execution_time_ms": execution_time_ms
                },
                severity="error",
                category="query"
            )
            
            logger.error(f"Query execution failed: {e}")
            
            return {
                "success": False,
                "execution_id": execution_id,
                "error": str(e),
                "execution_time_ms": execution_time_ms
            }
    
    async def _execute_query_on_server(
        self,
        query: str,
        server: SQLServerConnection,
        parameters: Optional[Dict[str, Any]] = None,
        timeout: int = 300,
        max_rows: int = 10000
    ) -> Dict[str, Any]:
        """Execute query on specific server"""
        
        try:
            # Get or create connection pool
            pool = await self._get_connection_pool(server)
            
            if not pool:
                raise Exception(f"Failed to create connection pool for server {server.name}")
            
            # Execute query with timeout
            result = await asyncio.wait_for(
                self._execute_with_pool(pool, query, parameters, max_rows),
                timeout=timeout
            )
            
            return result
            
        except asyncio.TimeoutError:
            raise Exception(f"Query execution timed out after {timeout} seconds")
        except Exception as e:
            logger.error(f"Query execution error on server {server.name}: {e}")
            raise
    
    async def _execute_with_pool(
        self,
        pool,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        max_rows: int = 10000
    ) -> Dict[str, Any]:
        """Execute query using connection pool"""
        
        connection = None
        try:
            # Get connection from pool
            connection = pool.connect()
            self.stats["active_connections"] += 1
            
            # Prepare query
            if parameters:
                stmt = text(query).bindparams(**parameters)
            else:
                stmt = text(query)
            
            # Execute query
            result = connection.execute(stmt)
            
            # Fetch results
            if result.returns_rows:
                # Fetch data with row limit
                rows = result.fetchmany(max_rows)
                columns = list(result.keys())
                
                # Convert to list of lists
                data = [list(row) for row in rows]
                
                # Calculate result size
                result_size_bytes = len(str(data).encode('utf-8'))
                
                return {
                    "success": True,
                    "data": data,
                    "columns": columns,
                    "row_count": len(data),
                    "result_size_bytes": result_size_bytes
                }
            else:
                # Non-SELECT query
                rows_affected = result.rowcount if hasattr(result, 'rowcount') else 0
                
                return {
                    "success": True,
                    "rows_affected": rows_affected,
                    "row_count": 0,
                    "result_size_bytes": 0
                }
                
        except SQLAlchemyError as e:
            logger.error(f"SQL execution error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected execution error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            if connection:
                connection.close()
                self.stats["active_connections"] -= 1
    
    async def _get_connection_pool(self, server: SQLServerConnection):
        """Get or create connection pool for server"""
        
        pool_key = f"{server.id}_{server.host}_{server.port}_{server.database}"
        
        if pool_key in self.connection_pools:
            return self.connection_pools[pool_key]
        
        try:
            # Create connection string
            connection_string = self._build_connection_string(server)
            
            # Create engine with connection pool
            engine = create_engine(
                connection_string,
                pool_size=server.max_connections or 10,
                max_overflow=20,
                pool_timeout=30,
                pool_recycle=3600,
                pool_pre_ping=True,
                echo=settings.DEBUG
            )
            
            # Test connection
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            self.connection_pools[pool_key] = engine
            self.stats["total_connections"] += 1
            
            logger.info(f"Created connection pool for server {server.name}")
            return engine
            
        except Exception as e:
            logger.error(f"Failed to create connection pool for server {server.name}: {e}")
            return None
    
    def _build_connection_string(self, server: SQLServerConnection) -> str:
        """Build database connection string"""
        
        if server.server_type == ServerType.POSTGRESQL:
            return (
                f"postgresql://{server.username}:{server.password}@"
                f"{server.host}:{server.port}/{server.database}"
            )
        elif server.server_type == ServerType.MYSQL:
            return (
                f"mysql+pymysql://{server.username}:{server.password}@"
                f"{server.host}:{server.port}/{server.database}"
            )
        elif server.server_type == ServerType.MSSQL:
            return (
                f"mssql+pyodbc://{server.username}:{server.password}@"
                f"{server.host}:{server.port}/{server.database}?driver=ODBC+Driver+17+for+SQL+Server"
            )
        elif server.server_type == ServerType.ORACLE:
            return (
                f"oracle+cx_oracle://{server.username}:{server.password}@"
                f"{server.host}:{server.port}/{server.database}"
            )
        elif server.server_type == ServerType.SQLITE:
            return f"sqlite:///{server.database}"
        else:
            raise ValueError(f"Unsupported server type: {server.server_type}")
    
    def _check_server_permissions(self, user: User, server: SQLServerConnection) -> bool:
        """Check if user has permission to access server"""
        
        # Admin can access all servers
        if user.role == UserRole.ADMIN:
            return True
        
        # Check allowed roles for server
        if server.allowed_roles:
            return user.role in server.allowed_roles
        
        # Default permissions based on role
        role_permissions = {
            UserRole.ADMIN: True,
            UserRole.ANALYST: True,
            UserRole.POWERBI: server.environment.value != "production",
            UserRole.READONLY: True
        }
        
        return role_permissions.get(user.role, False)
    
    async def _get_cached_result(
        self,
        query_hash: str,
        server_id: int,
        parameters: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Get cached query result"""
        
        try:
            # Create cache key
            param_hash = ""
            if parameters:
                param_str = str(sorted(parameters.items()))
                param_hash = hashlib.md5(param_str.encode()).hexdigest()
            
            cache_key = f"query_result:{query_hash}:{server_id}:{param_hash}"
            
            # Get from cache
            cached_result = await cache_service.get(cache_key)
            
            if cached_result:
                logger.debug(f"Cache hit for query hash {query_hash}")
                return cached_result
            
            return None
            
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    async def _cache_result(
        self,
        query_hash: str,
        server_id: int,
        parameters: Optional[Dict[str, Any]],
        result: Dict[str, Any]
    ):
        """Cache query result"""
        
        try:
            # Don't cache large results
            if result.get("result_size_bytes", 0) > 10 * 1024 * 1024:  # 10MB
                return
            
            # Create cache key
            param_hash = ""
            if parameters:
                param_str = str(sorted(parameters.items()))
                param_hash = hashlib.md5(param_str.encode()).hexdigest()
            
            cache_key = f"query_result:{query_hash}:{server_id}:{param_hash}"
            
            # Cache result
            await cache_service.set(
                cache_key,
                {
                    "data": result.get("data"),
                    "columns": result.get("columns"),
                    "row_count": result.get("row_count", 0),
                    "cached_at": datetime.utcnow().isoformat()
                },
                ttl=settings.QUERY_CACHE_TTL
            )
            
            logger.debug(f"Cached result for query hash {query_hash}")
            
        except Exception as e:
            logger.error(f"Cache set error: {e}")
    
    async def _initialize_connection_pools(self):
        """Initialize connection pools for active servers"""
        
        try:
            with get_db_session() as db:
                servers = db.query(SQLServerConnection).filter(
                    SQLServerConnection.is_active == True
                ).all()
                
                for server in servers:
                    await self._get_connection_pool(server)
                
                logger.info(f"Initialized connection pools for {len(servers)} servers")
                
        except Exception as e:
            logger.error(f"Connection pool initialization error: {e}")
    
    async def _monitor_connections(self):
        """Monitor connection health periodically"""
        
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                
                # Check each connection pool
                for pool_key, engine in list(self.connection_pools.items()):
                    try:
                        with engine.connect() as conn:
                            conn.execute(text("SELECT 1"))
                        logger.debug(f"Connection pool {pool_key} is healthy")
                    except Exception as e:
                        logger.warning(f"Connection pool {pool_key} is unhealthy: {e}")
                        # Remove unhealthy pool
                        del self.connection_pools[pool_key]
                
            except Exception as e:
                logger.error(f"Connection monitoring error: {e}")
    
    async def test_server_connection(self, server_id: int) -> Dict[str, Any]:
        """Test connection to server"""
        
        try:
            with get_db_session() as db:
                server = db.query(SQLServerConnection).filter(
                    SQLServerConnection.id == server_id
                ).first()
                
                if not server:
                    return {
                        "success": False,
                        "error": "Server not found"
                    }
            
            start_time = time.time()
            
            # Get connection pool
            pool = await self._get_connection_pool(server)
            
            if not pool:
                return {
                    "success": False,
                    "error": "Failed to create connection pool"
                }
            
            # Test connection
            with pool.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            response_time_ms = int((time.time() - start_time) * 1000)
            
            return {
                "success": True,
                "message": "Connection successful",
                "response_time_ms": response_time_ms
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_server_health(self, server_id: int) -> Dict[str, Any]:
        """Get server health status"""
        
        try:
            connection_test = await self.test_server_connection(server_id)
            
            if connection_test["success"]:
                status = "healthy"
                details = {
                    "connection": "ok",
                    "response_time_ms": connection_test["response_time_ms"]
                }
            else:
                status = "unhealthy"
                details = {
                    "connection": "failed",
                    "error": connection_test["error"]
                }
            
            return {
                "status": status,
                "details": details,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "details": {"error": str(e)},
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """Service health check"""
        
        try:
            return {
                "status": "healthy",
                "connection_pools": len(self.connection_pools),
                "active_connections": self.stats["active_connections"],
                "stats": self.stats,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get SQL proxy metrics"""
        
        return {
            "stats": self.stats,
            "connection_pools": len(self.connection_pools),
            "cache_enabled": bool(cache_service),
            "analyzer_enabled": bool(self.query_analyzer),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def cleanup(self):
        """Cleanup service resources"""
        
        # Close all connection pools
        for pool_key, engine in self.connection_pools.items():
            try:
                engine.dispose()
                logger.info(f"Disposed connection pool {pool_key}")
            except Exception as e:
                logger.error(f"Error disposing connection pool {pool_key}: {e}")
        
        self.connection_pools.clear()
        
        logger.info("✅ SQL Proxy Service cleanup completed")


# Global SQL proxy service instance
sql_proxy_service = SQLProxyService()