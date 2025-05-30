"""
Complete SQL Server Models - Final Version
Created: 2025-05-29 13:50:14 UTC by Teeksss
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, Enum, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class ServerType(enum.Enum):
    MSSQL = "mssql"
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    ORACLE = "oracle"
    SQLITE = "sqlite"


class Environment(enum.Enum):
    PRODUCTION = "production"
    STAGING = "staging"
    DEVELOPMENT = "development"
    TEST = "test"


class HealthStatus(enum.Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ConnectionStatus(enum.Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    CONNECTING = "connecting"


class SQLServerConnection(Base):
    """SQL Server connection configuration"""
    __tablename__ = "sql_server_connections"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(Text)
    
    # Connection details
    server_type = Column(Enum(ServerType), nullable=False)
    host = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False)
    database = Column(String(255), nullable=False)
    username = Column(String(255), nullable=False)
    password = Column(String(500), nullable=False)  # Encrypted
    
    # Additional connection parameters
    connection_string = Column(Text)
    additional_params = Column(JSON)
    
    # SSL/TLS configuration
    use_ssl = Column(Boolean, default=False)
    ssl_cert_path = Column(String(500))
    ssl_key_path = Column(String(500))
    ssl_ca_path = Column(String(500))
    verify_ssl_cert = Column(Boolean, default=True)
    
    # Environment and access control
    environment = Column(Enum(Environment), default=Environment.DEVELOPMENT)
    is_read_only = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=False)
    
    # Connection pooling
    pool_size = Column(Integer, default=5)
    max_overflow = Column(Integer, default=10)
    pool_timeout = Column(Integer, default=30)
    pool_recycle = Column(Integer, default=3600)
    
    # Query limits
    max_execution_time = Column(Integer, default=300)  # seconds
    max_result_rows = Column(Integer, default=10000)
    max_concurrent_queries = Column(Integer, default=10)
    
    # Health monitoring
    health_status = Column(Enum(HealthStatus), default=HealthStatus.UNKNOWN)
    last_health_check = Column(DateTime(timezone=True))
    health_check_interval = Column(Integer, default=300)  # seconds
    consecutive_failures = Column(Integer, default=0)
    
    # Performance metrics
    avg_response_time_ms = Column(Float)
    success_rate = Column(Float)
    total_queries = Column(Integer, default=0)
    failed_queries = Column(Integer, default=0)
    
    # Connection status
    connection_status = Column(Enum(ConnectionStatus), default=ConnectionStatus.DISCONNECTED)
    last_connection_test = Column(DateTime(timezone=True))
    last_connection_error = Column(Text)
    
    # Metadata
    version = Column(String(100))
    collation = Column(String(100))
    timezone = Column(String(50))
    max_connections = Column(Integer)
    current_connections = Column(Integer, default=0)
    
    # Monitoring configuration
    monitor_slow_queries = Column(Boolean, default=True)
    slow_query_threshold_ms = Column(Integer, default=1000)
    monitor_blocking = Column(Boolean, default=True)
    monitor_deadlocks = Column(Boolean, default=True)
    
    # Backup information
    last_backup_date = Column(DateTime(timezone=True))
    backup_frequency = Column(String(50))
    backup_location = Column(String(500))
    
    # Access control
    allowed_roles = Column(JSON)  # List of roles that can access this server
    restricted_operations = Column(JSON)  # List of restricted SQL operations
    whitelist_only = Column(Boolean, default=False)
    
    # Audit settings
    audit_all_queries = Column(Boolean, default=True)
    audit_failed_queries = Column(Boolean, default=True)
    audit_slow_queries = Column(Boolean, default=True)
    retention_days = Column(Integer, default=365)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    updated_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    query_executions = relationship("QueryExecution", back_populates="server")
    user_permissions = relationship("ServerPermission", back_populates="server")
    health_checks = relationship("ServerHealthCheck", back_populates="server")
    performance_metrics = relationship("ServerPerformanceMetric", back_populates="server")
    
    def __repr__(self):
        return f"<SQLServerConnection(name='{self.name}', type='{self.server_type}', host='{self.host}')>"


class ServerHealthCheck(Base):
    """Server health check history"""
    __tablename__ = "server_health_checks"

    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(Integer, ForeignKey("sql_server_connections.id"), nullable=False)
    
    # Health check details
    status = Column(Enum(HealthStatus), nullable=False)
    response_time_ms = Column(Float)
    error_message = Column(Text)
    
    # Connection test
    connection_successful = Column(Boolean, default=False)
    connection_time_ms = Column(Float)
    
    # Database specific checks
    db_version = Column(String(100))
    db_size_mb = Column(Float)
    active_connections = Column(Integer)
    max_connections = Column(Integer)
    cpu_usage_percent = Column(Float)
    memory_usage_percent = Column(Float)
    disk_usage_percent = Column(Float)
    
    # Performance metrics
    slow_queries_count = Column(Integer)
    blocked_queries_count = Column(Integer)
    deadlocks_count = Column(Integer)
    
    # Timestamp
    checked_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    server = relationship("SQLServerConnection", back_populates="health_checks")


class ServerPerformanceMetric(Base):
    """Server performance metrics over time"""
    __tablename__ = "server_performance_metrics"

    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(Integer, ForeignKey("sql_server_connections.id"), nullable=False)
    
    # Time period
    metric_date = Column(DateTime(timezone=True), nullable=False)
    period_minutes = Column(Integer, default=5)  # 5-minute intervals
    
    # Query metrics
    total_queries = Column(Integer, default=0)
    successful_queries = Column(Integer, default=0)
    failed_queries = Column(Integer, default=0)
    avg_execution_time_ms = Column(Float)
    max_execution_time_ms = Column(Float)
    min_execution_time_ms = Column(Float)
    
    # Performance metrics
    avg_response_time_ms = Column(Float)
    max_response_time_ms = Column(Float)
    throughput_qps = Column(Float)  # Queries per second
    
    # Resource utilization
    cpu_usage_percent = Column(Float)
    memory_usage_percent = Column(Float)
    disk_io_mb_per_sec = Column(Float)
    network_io_mb_per_sec = Column(Float)
    
    # Connection metrics
    active_connections = Column(Integer)
    peak_connections = Column(Integer)
    connection_pool_usage_percent = Column(Float)
    
    # Error metrics
    connection_errors = Column(Integer, default=0)
    timeout_errors = Column(Integer, default=0)
    authentication_errors = Column(Integer, default=0)
    
    # Relationships
    server = relationship("SQLServerConnection", back_populates="performance_metrics")


class ServerConfiguration(Base):
    """Server-specific configuration overrides"""
    __tablename__ = "server_configurations"

    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(Integer, ForeignKey("sql_server_connections.id"), nullable=False)
    
    # Configuration key-value pairs
    config_key = Column(String(255), nullable=False)
    config_value = Column(Text)
    config_type = Column(String(50))  # string, integer, boolean, json
    description = Column(Text)
    
    # Metadata
    is_active = Column(Boolean, default=True)
    is_sensitive = Column(Boolean, default=False)  # Mark sensitive configs
    requires_restart = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    server = relationship("SQLServerConnection")
    creator = relationship("User")

    # Unique constraint
    __table_args__ = (
        {"schema": None},
    )


class ServerTag(Base):
    """Server tagging system"""
    __tablename__ = "server_tags"

    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(Integer, ForeignKey("sql_server_connections.id"), nullable=False)
    tag_name = Column(String(100), nullable=False)
    tag_value = Column(String(255))
    tag_category = Column(String(100))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    server = relationship("SQLServerConnection")
    creator = relationship("User")

    # Unique constraint
    __table_args__ = (
        {"schema": None},
    )