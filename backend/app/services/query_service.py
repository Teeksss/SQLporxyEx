import pyodbc
import logging
import hashlib
import time
from typing import Dict, Any, List, Tuple, Optional
from sqlalchemy.orm import Session
import asyncio
from datetime import datetime

from app.models.query import QueryWhitelist, QueryExecution
from app.models.audit import AuditLog
from app.models.server import SQLServerConnection
from app.utils.sql_parser import SQLParser
from app.services.config_service import ConfigService

logger = logging.getLogger(__name__)

class QueryService:
    """Service for SQL query processing and execution"""
    
    def __init__(self, db: Session, config_service: ConfigService = None):
        self.db = db
        self.config_service = config_service
        self.sql_parser = SQLParser()
    
    async def execute_query(
        self, 
        query: str, 
        user_id: int,
        server_id: int,
        parameters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Execute SQL query through proxy with security checks"""
        start_time = time.time()
        
        try:
            # Parse and analyze query
            parsed_query = self.sql_parser.parse_query(query)
            query_hash = self._generate_query_hash(query)
            
            # Check if query is whitelisted
            whitelist_check = await self._check_whitelist(query_hash, parsed_query)
            if not whitelist_check["allowed"]:
                # Create pending approval entry
                await self._create_pending_approval(
                    query, query_hash, parsed_query, user_id
                )
                
                execution_time = int((time.time() - start_time) * 1000)
                await self._log_query_execution(
                    user_id, query, server_id, "blocked", 
                    execution_time, 0, whitelist_check["reason"]
                )
                
                return {
                    "success": False,
                    "message": whitelist_check["reason"],
                    "requires_approval": True,
                    "query_hash": query_hash
                }
            
            # Get server connection
            server = self.db.query(SQLServerConnection).filter(
                SQLServerConnection.id == server_id,
                SQLServerConnection.is_active == True
            ).first()
            
            if not server:
                raise Exception("SQL Server not found or inactive")
            
            # Execute query
            result = await self._execute_on_server(server, query, parameters)
            
            execution_time = int((time.time() - start_time) * 1000)
            
            # Log successful execution
            await self._log_query_execution(
                user_id, query, server_id, "success",
                execution_time, len(result.get("data", []))
            )
            
            return {
                "success": True,
                "data": result["data"],
                "execution_time": execution_time,
                "row_count": len(result.get("data", [])),
                "columns": result.get("columns", [])
            }
            
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            error_message = str(e)
            
            # Log failed execution
            await self._log_query_execution(
                user_id, query, server_id, "error",
                execution_time, 0, error_message
            )
            
            logger.error(f"Query execution failed: {e}")
            return {
                "success": False,
                "message": error_message,
                "execution_time": execution_time
            }
    
    async def approve_query(
        self, 
        query_hash: str, 
        approved_by: int,
        approved: bool = True
    ) -> bool:
        """Approve or reject a pending query"""
        try:
            whitelist_entry = self.db.query(QueryWhitelist).filter(
                QueryWhitelist.query_hash == query_hash,
                QueryWhitelist.status == "pending"
            ).first()
            
            if not whitelist_entry:
                return False
            
            whitelist_entry.status = "approved" if approved else "rejected"
            whitelist_entry.approved_by = approved_by
            whitelist_entry.approved_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"Query {query_hash} {'approved' if approved else 'rejected'} by user {approved_by}")
            return True
            
        except Exception as e:
            logger.error(f"Query approval failed: {e}")
            self.db.rollback()
            return False
    
    async def get_pending_queries(self) -> List[Dict[str, Any]]:
        """Get all pending query approvals"""
        try:
            pending = self.db.query(QueryWhitelist).filter(
                QueryWhitelist.status == "pending"
            ).order_by(QueryWhitelist.created_at.desc()).all()
            
            result = []
            for entry in pending:
                parsed_info = self.sql_parser.parse_query(entry.original_query)
                
                result.append({
                    "id": entry.id,
                    "query_hash": entry.query_hash,
                    "original_query": entry.original_query,
                    "normalized_query": entry.normalized_query,
                    "query_type": entry.query_type,
                    "risk_level": entry.risk_level,
                    "tables_used": entry.tables_used.split(",") if entry.tables_used else [],
                    "columns_used": entry.columns_used.split(",") if entry.columns_used else [],
                    "created_by": entry.creator.username if entry.creator else "Unknown",
                    "created_at": entry.created_at.isoformat(),
                    "analysis": parsed_info
                })
            
            return result
        except Exception as e:
            logger.error(f"Get pending queries failed: {e}")
            return []
    
    async def test_connection(self, db_config: Dict[str, Any]) -> Dict[str, Any]:
        """Test SQL Server connection"""
        try:
            server = db_config.get("server")
            database = db_config.get("database", "master")
            username = db_config.get("username")
            password = db_config.get("password")
            port = db_config.get("port", 1433)
            
            if not all([server, username, password]):
                return {"success": False, "message": "Missing connection parameters"}
            
            # Build connection string
            if port != 1433:
                server = f"{server},{port}"
            
            connection_string = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={server};"
                f"DATABASE={database};"
                f"UID={username};"
                f"PWD={password};"
                f"Connection Timeout=10;"
            )
            
            # Test connection
            conn = pyodbc.connect(connection_string)
            cursor = conn.cursor()
            cursor.execute("SELECT @@VERSION")
            version = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            
            return {
                "success": True,
                "message": "Connection successful",
                "server_info": {
                    "version": version,
                    "server": server,
                    "database": database
                }
            }
            
        except Exception as e:
            logger.error(f"SQL Server connection test failed: {e}")
            return {"success": False, "message": str(e)}
    
    async def _check_whitelist(
        self, 
        query_hash: str, 
        parsed_query: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check if query is in whitelist"""
        try:
            # Check exact hash match
            whitelist_entry = self.db.query(QueryWhitelist).filter(
                QueryWhitelist.query_hash == query_hash,
                QueryWhitelist.status == "approved"
            ).first()
            
            if whitelist_entry:
                return {"allowed": True, "reason": "Query approved"}
            
            # Check pattern-based rules
            if await self._check_query_patterns(parsed_query):
                return {"allowed": True, "reason": "Query matches approved pattern"}
            
            return {
                "allowed": False, 
                "reason": "Query requires approval - not in whitelist"
            }
            
        except Exception as e:
            logger.error(f"Whitelist check failed: {e}")
            return {"allowed": False, "reason": "Security check failed"}
    
    async def _check_query_patterns(self, parsed_query: Dict[str, Any]) -> bool:
        """Check query against approved patterns"""
        try:
            # Get query approval requirements
            require_approval = await self.config_service.get_config(
                "require_query_approval", True
            ) if self.config_service else True
            
            if not require_approval:
                return True
            
            # Basic safety checks
            query_type = parsed_query.get("type", "").upper()
            
            # Allow simple SELECT queries by default
            if query_type == "SELECT":
                tables = parsed_query.get("tables", [])
                # Allow queries on specific safe tables
                safe_tables = ["sys.tables", "sys.columns", "information_schema"]
                if any(table.lower().startswith(safe) for safe in safe_tables for table in tables):
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Pattern check failed: {e}")
            return False
    
    async def _create_pending_approval(
        self,
        query: str,
        query_hash: str,
        parsed_query: Dict[str, Any],
        user_id: int
    ):
        """Create pending approval entry"""
        try:
            # Check if already exists
            existing = self.db.query(QueryWhitelist).filter(
                QueryWhitelist.query_hash == query_hash
            ).first()
            
            if existing:
                return
            
            whitelist_entry = QueryWhitelist(
                query_hash=query_hash,
                original_query=query,
                normalized_query=parsed_query.get("normalized", query),
                query_type=parsed_query.get("type", "UNKNOWN"),
                risk_level=parsed_query.get("risk_level", "MEDIUM"),
                tables_used=",".join(parsed_query.get("tables", [])),
                columns_used=",".join(parsed_query.get("columns", [])),
                created_by=user_id,
                status="pending"
            )
            
            self.db.add(whitelist_entry)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Create pending approval failed: {e}")
            self.db.rollback()
    
    async def _execute_on_server(
        self,
        server: SQLServerConnection,
        query: str,
        parameters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Execute query on SQL Server"""
        try:
            # Decrypt password
            from app.core.security import decrypt_sensitive_data
            password = decrypt_sensitive_data(server.password)
            
            # Build connection string
            server_address = server.host
            if server.port != 1433:
                server_address = f"{server.host},{server.port}"
            
            connection_string = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={server_address};"
                f"DATABASE={server.database};"
                f"UID={server.username};"
                f"PWD={password};"
                f"Connection Timeout={server.connection_timeout};"
                f"Query Timeout={server.query_timeout};"
            )
            
            # Execute query
            conn = pyodbc.connect(connection_string)
            cursor = conn.cursor()
            
            if parameters:
                cursor.execute(query, parameters)
            else:
                cursor.execute(query)
            
            # Fetch results
            columns = [column[0] for column in cursor.description] if cursor.description else []
            rows = cursor.fetchall()
            
            # Convert to list of dictionaries
            data = []
            for row in rows:
                row_dict = {}
                for i, value in enumerate(row):
                    if i < len(columns):
                        # Handle different data types
                        if value is None:
                            row_dict[columns[i]] = None
                        elif isinstance(value, (int, float, str, bool)):
                            row_dict[columns[i]] = value
                        else:
                            row_dict[columns[i]] = str(value)
                data.append(row_dict)
            
            cursor.close()
            conn.close()
            
            # Check result size limits
            max_rows = await self.config_service.get_config(
                "max_result_rows", 10000
            ) if self.config_service else 10000
            
            if len(data) > max_rows:
                data = data[:max_rows]
                logger.warning(f"Query result truncated to {max_rows} rows")
            
            return {
                "data": data,
                "columns": columns,
                "row_count": len(data)
            }
            
        except Exception as e:
            logger.error(f"Query execution on server failed: {e}")
            raise
    
    async def _log_query_execution(
        self,
        user_id: int,
        query: str,
        server_id: int,
        status: str,
        execution_time: int,
        rows_returned: int,
        error_message: str = None
    ):
        """Log query execution for audit"""
        try:
            log_entry = AuditLog(
                user_id=user_id,
                action="query_execution",
                resource_type="sql_query",
                resource_id=str(server_id),
                details={
                    "query": query[:1000],  # Truncate long queries
                    "server_id": server_id,
                    "execution_time_ms": execution_time,
                    "rows_returned": rows_returned,
                    "error_message": error_message
                },
                status=status,
                ip_address="",  # Would be filled by middleware
                user_agent=""   # Would be filled by middleware
            )
            
            self.db.add(log_entry)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Query execution logging failed: {e}")
    
    def _generate_query_hash(self, query: str) -> str:
        """Generate hash for query identification"""
        # Normalize query for consistent hashing
        normalized = self.sql_parser.normalize_query(query)
        return hashlib.sha256(normalized.encode()).hexdigest()