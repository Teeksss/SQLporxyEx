from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Enum, Float
from sqlalchemy.sql import func
from enum import Enum as PyEnum
import json

from app.core.database import Base

class ServerType(PyEnum):
    """SQL Server types"""
    MSSQL = "mssql"
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"
    ORACLE = "oracle"

class ConnectionMethod(PyEnum):
    """Connection methods"""
    ODBC = "odbc"
    NATIVE = "native"
    JDBC = "jdbc"

class SQLServerConnection(Base):
    __tablename__ = "sql_server_connections"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic connection info
    name = Column(String, unique=True, nullable=False)
    description = Column(Text)
    server_type = Column(Enum(ServerType), default=ServerType.MSSQL)
    
    # Connection details
    host = Column(String, nullable=False)
    port = Column(Integer, default=1433)
    database = Column(String, nullable=False)
    username = Column(String, nullable=False)
    password = Column(String, nullable=False)  # Encrypted
    
    # Connection settings
    connection_method = Column(Enum(ConnectionMethod), default=ConnectionMethod.ODBC)
    connection_string_template = Column(Text)
    connection_timeout = Column(Integer, default=30)
    query_timeout = Column(Integer, default=300)
    max_pool_size = Column(Integer, default=10)
    
    # SSL/TLS settings
    use_ssl = Column(Boolean, default=False)
    ssl_cert_path = Column(String)
    ssl_key_path = Column(String)
    ssl_ca_path = Column(String)
    verify_ssl_cert = Column(Boolean, default=True)
    
    # Advanced settings
    connection_properties = Column(Text)  # JSON for additional properties
    environment = Column(String, default="production")  # production, staging, development
    
    # Access control
    allowed_user_roles = Column(Text)  # JSON array of allowed roles
    allowed_users = Column(Text)       # JSON array of specific user IDs
    ip_whitelist = Column(Text)        # JSON array of allowed IP ranges
    
    # Operational settings
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    is_read_only = Column(Boolean, default=False)
    maintenance_mode = Column(Boolean, default=False)
    
    # Monitoring
    last_health_check = Column(DateTime(timezone=True))
    health_status = Column(String, default="unknown")  # healthy, unhealthy, unknown
    health_message = Column(Text)
    response_time_ms = Column(Integer)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String)
    
    def get_connection_string(self) -> str:
        """Generate connection string based on server type and settings"""
        if self.connection_string_template:
            return self.connection_string_template.format(
                host=self.host,
                port=self.port,
                database=self.database,
                username=self.username,
                password="***"  # Don't expose password
            )
        
        if self.server_type == ServerType.MSSQL:
            server_addr = f"{self.host},{self.port}" if self.port != 1433 else self.host
            return (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={server_addr};"
                f"DATABASE={self.database};"
                f"UID={self.username};"
                f"PWD=***;"
                f"Connection Timeout={self.connection_timeout};"
                f"Encrypt={'yes' if self.use_ssl else 'no'};"
            )
        
        return f"host={self.host} port={self.port} dbname={self.database}"
    
    def is_user_allowed(self, user_id: int, user_role: str) -> bool:
        """Check if user is allowed to access this server"""
        try:
            if self.allowed_user_roles:
                allowed_roles = json.loads(self.allowed_user_roles)
                if user_role not in allowed_roles:
                    return False
            
            if self.allowed_users:
                allowed_users = json.loads(self.allowed_users)
                if user_id not in allowed_users:
                    return False
            
            return True
        except (json.JSONDecodeError, TypeError):
            return True

class ServerHealthHistory(Base):
    __tablename__ = "server_health_history"
    
    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(Integer, nullable=False)
    
    # Health metrics
    status = Column(String, nullable=False)  # healthy, unhealthy, timeout, error
    response_time_ms = Column(Integer)
    error_message = Column(Text)
    
    # Performance metrics
    cpu_usage_percent = Column(Float)
    memory_usage_percent = Column(Float)
    disk_usage_percent = Column(Float)
    active_connections = Column(Integer)
    
    # Timestamp
    checked_at = Column(DateTime(timezone=True), server_default=func.now())