"""
Complete Query Models - Final Version
Created: 2025-05-29 13:50:14 UTC by Teeksss
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, JSON, Enum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class QueryStatus(enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class QueryType(enum.Enum):
    SELECT = "select"
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    CREATE = "create"
    DROP = "drop"
    ALTER = "alter"
    TRUNCATE = "truncate"
    OTHER = "other"


class RiskLevel(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ApprovalStatus(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class QueryExecution(Base):
    """Query execution history and results"""
    __tablename__ = "query_executions"

    id = Column(Integer, primary_key=True, index=True)
    query_hash = Column(String(64), index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    server_id = Column(Integer, ForeignKey("sql_server_connections.id"), nullable=False)
    
    # Query details
    original_query = Column(Text, nullable=False)
    normalized_query = Column(Text)
    query_preview = Column(String(500))
    query_type = Column(Enum(QueryType))
    parameters = Column(JSON)
    
    # Execution details
    status = Column(Enum(QueryStatus), default=QueryStatus.PENDING)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    execution_time_ms = Column(Integer)
    timeout_seconds = Column(Integer, default=300)
    
    # Results
    rows_returned = Column(Integer, default=0)
    rows_affected = Column(Integer, default=0)
    result_size_bytes = Column(Integer, default=0)
    columns_metadata = Column(JSON)
    
    # Error handling
    error_message = Column(Text)
    error_code = Column(String(50))
    error_details = Column(JSON)
    
    # Performance metrics
    parse_time_ms = Column(Integer)
    compile_time_ms = Column(Integer)
    execution_plan = Column(JSON)
    statistics = Column(JSON)
    
    # Security and compliance
    risk_level = Column(Enum(RiskLevel), default=RiskLevel.LOW)
    security_warnings = Column(JSON)
    compliance_flags = Column(JSON)
    requires_approval = Column(Boolean, default=False)
    approval_id = Column(Integer, ForeignKey("query_approvals.id"))
    
    # Caching
    is_cached = Column(Boolean, default=False)
    cache_key = Column(String(255))
    cache_hit = Column(Boolean, default=False)
    cache_ttl = Column(Integer)
    
    # Export tracking
    exported_at = Column(DateTime(timezone=True))
    export_format = Column(String(20))
    export_size_bytes = Column(Integer)
    
    # Relationships
    user = relationship("User", back_populates="query_executions")
    server = relationship("SQLServerConnection", back_populates="query_executions")
    approval = relationship("QueryApproval", back_populates="execution")
    exports = relationship("QueryExport", back_populates="execution")


class QueryApproval(Base):
    """Query approval workflow"""
    __tablename__ = "query_approvals"

    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(Integer, ForeignKey("query_executions.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    approved_by = Column(Integer, ForeignKey("users.id"))
    
    # Request details
    query_hash = Column(String(64), nullable=False)
    query_preview = Column(String(500))
    query_type = Column(Enum(QueryType))
    risk_level = Column(Enum(RiskLevel))
    risk_factors = Column(JSON)
    justification = Column(Text)
    
    # Approval details
    status = Column(Enum(ApprovalStatus), default=ApprovalStatus.PENDING)
    requested_at = Column(DateTime(timezone=True), server_default=func.now())
    reviewed_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))
    
    # Comments and feedback
    admin_comments = Column(Text)
    user_comments = Column(Text)
    rejection_reason = Column(Text)
    
    # Auto-approval settings
    auto_approved = Column(Boolean, default=False)
    approval_rule_id = Column(Integer)
    
    # Relationships
    execution = relationship("QueryExecution", back_populates="approval")
    user = relationship("User", back_populates="query_approvals")
    approved_by_user = relationship("User", back_populates="approved_queries", 
                                  foreign_keys=[approved_by])


class QueryWhitelist(Base):
    """Pre-approved query patterns"""
    __tablename__ = "query_whitelists"

    id = Column(Integer, primary_key=True, index=True)
    query_hash = Column(String(64), unique=True, index=True, nullable=False)
    original_query = Column(Text, nullable=False)
    normalized_query = Column(Text, nullable=False)
    query_pattern = Column(Text)
    query_type = Column(Enum(QueryType))
    
    # Approval details
    risk_level = Column(Enum(RiskLevel), default=RiskLevel.LOW)
    status = Column(Enum(ApprovalStatus), default=ApprovalStatus.APPROVED)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Validity
    expires_at = Column(DateTime(timezone=True))
    max_executions = Column(Integer)
    current_executions = Column(Integer, default=0)
    
    # Restrictions
    allowed_servers = Column(JSON)  # List of server IDs
    allowed_roles = Column(JSON)    # List of roles
    max_execution_time = Column(Integer)
    max_result_rows = Column(Integer)
    
    # Comments
    description = Column(Text)
    approval_comments = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_used_at = Column(DateTime(timezone=True))
    
    # Relationships
    approver = relationship("User", foreign_keys=[approved_by])
    creator = relationship("User", foreign_keys=[created_by])


class QueryTemplate(Base):
    """Reusable query templates"""
    __tablename__ = "query_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(100))
    tags = Column(JSON)
    
    # Template content
    query_template = Column(Text, nullable=False)
    parameters = Column(JSON)  # Parameter definitions
    default_values = Column(JSON)
    
    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_public = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    usage_count = Column(Integer, default=0)
    
    # Validation
    last_validated = Column(DateTime(timezone=True))
    validation_status = Column(String(20))
    validation_errors = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    creator = relationship("User")


class QueryExport(Base):
    """Query result export tracking"""
    __tablename__ = "query_exports"

    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(Integer, ForeignKey("query_executions.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Export details
    format = Column(String(20), nullable=False)  # csv, excel, json, etc.
    filename = Column(String(255))
    file_path = Column(String(500))
    file_size_bytes = Column(Integer)
    row_count = Column(Integer)
    
    # Export settings
    include_headers = Column(Boolean, default=True)
    delimiter = Column(String(10))
    encoding = Column(String(20), default="utf-8")
    compression = Column(String(20))
    
    # Status
    status = Column(String(20), default="pending")
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    download_count = Column(Integer, default=0)
    last_downloaded = Column(DateTime(timezone=True))
    
    # Error handling
    error_message = Column(Text)
    
    # Security
    expires_at = Column(DateTime(timezone=True))
    is_encrypted = Column(Boolean, default=False)
    access_token = Column(String(255))
    
    # Relationships
    execution = relationship("QueryExecution", back_populates="exports")
    user = relationship("User")


class QuerySchedule(Base):
    """Scheduled query executions"""
    __tablename__ = "query_schedules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    server_id = Column(Integer, ForeignKey("sql_server_connections.id"), nullable=False)
    
    # Query details
    query_template = Column(Text, nullable=False)
    parameters = Column(JSON)
    
    # Schedule configuration
    cron_expression = Column(String(100), nullable=False)
    timezone = Column(String(50), default="UTC")
    is_active = Column(Boolean, default=True)
    
    # Execution settings
    timeout_seconds = Column(Integer, default=300)
    max_retries = Column(Integer, default=3)
    retry_delay_seconds = Column(Integer, default=60)
    
    # Output configuration
    export_format = Column(String(20))
    export_path = Column(String(500))
    email_recipients = Column(JSON)
    webhook_url = Column(String(500))
    
    # Execution tracking
    last_execution = Column(DateTime(timezone=True))
    next_execution = Column(DateTime(timezone=True))
    execution_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    
    # Status
    status = Column(String(20), default="active")
    last_error = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    server = relationship("SQLServerConnection")