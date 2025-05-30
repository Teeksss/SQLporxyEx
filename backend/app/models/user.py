"""
Complete User Models - Final Version
Created: 2025-05-29 13:50:14 UTC by Teeksss
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, Enum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class UserRole(enum.Enum):
    ADMIN = "admin"
    ANALYST = "analyst"
    POWERBI = "powerbi"
    READONLY = "readonly"


class UserStatus(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class User(Base):
    """User model with complete functionality"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.READONLY)
    status = Column(Enum(UserStatus), default=UserStatus.ACTIVE)
    
    # Profile information
    first_name = Column(String(100))
    last_name = Column(String(100))
    display_name = Column(String(200))
    avatar_url = Column(String(500))
    phone = Column(String(50))
    department = Column(String(100))
    job_title = Column(String(100))
    manager_id = Column(Integer, ForeignKey("users.id"))
    
    # Authentication settings
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_ldap_user = Column(Boolean, default=False)
    must_change_password = Column(Boolean, default=False)
    password_changed_at = Column(DateTime(timezone=True))
    last_login_at = Column(DateTime(timezone=True))
    last_login_ip = Column(String(45))
    login_count = Column(Integer, default=0)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True))
    
    # MFA settings
    mfa_enabled = Column(Boolean, default=False)
    mfa_secret = Column(String(255))
    mfa_backup_codes = Column(JSON)
    
    # Preferences
    timezone = Column(String(50), default="UTC")
    language = Column(String(10), default="en")
    theme = Column(String(20), default="light")
    notification_preferences = Column(JSON)
    dashboard_config = Column(JSON)
    query_preferences = Column(JSON)
    
    # Rate limiting
    rate_limit_override = Column(Integer)
    daily_query_limit = Column(Integer)
    concurrent_query_limit = Column(Integer, default=5)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))
    updated_by = Column(Integer, ForeignKey("users.id"))
    
    # LDAP fields
    ldap_dn = Column(String(500))
    ldap_groups = Column(JSON)
    ldap_last_sync = Column(DateTime(timezone=True))
    
    # Session management
    active_sessions = Column(JSON)
    max_sessions = Column(Integer, default=5)
    
    # Relationships
    manager = relationship("User", remote_side=[id], back_populates="direct_reports")
    direct_reports = relationship("User", back_populates="manager")
    
    # Query relationships
    query_executions = relationship("QueryExecution", back_populates="user")
    query_approvals = relationship("QueryApproval", back_populates="user")
    approved_queries = relationship("QueryApproval", back_populates="approved_by_user", 
                                  foreign_keys="QueryApproval.approved_by")
    
    # Server access relationships
    server_permissions = relationship("ServerPermission", back_populates="user")
    
    # Notification relationships
    notification_rules = relationship("NotificationRule", back_populates="creator")
    notification_preferences_rel = relationship("NotificationPreference", back_populates="user")
    
    # Audit relationships
    audit_logs = relationship("AuditLog", back_populates="user")
    
    # Session relationships
    user_sessions = relationship("UserSession", back_populates="user")
    
    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}', role='{self.role}')>"
    
    @property
    def full_name(self):
        """Get user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.display_name or self.username
    
    @property
    def is_admin(self):
        """Check if user is admin"""
        return self.role == UserRole.ADMIN
    
    @property
    def is_locked(self):
        """Check if user account is locked"""
        if self.locked_until:
            from datetime import datetime
            return datetime.utcnow() < self.locked_until
        return False
    
    @property
    def can_execute_queries(self):
        """Check if user can execute queries"""
        return self.role in [UserRole.ADMIN, UserRole.ANALYST, UserRole.POWERBI] and self.is_active
    
    @property
    def can_approve_queries(self):
        """Check if user can approve queries"""
        return self.role == UserRole.ADMIN and self.is_active


class UserSession(Base):
    """User session tracking"""
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(String(255), unique=True, index=True, nullable=False)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    location = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))
    logout_at = Column(DateTime(timezone=True))

    # Relationships
    user = relationship("User", back_populates="user_sessions")


class ServerPermission(Base):
    """User permissions for specific servers"""
    __tablename__ = "server_permissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    server_id = Column(Integer, ForeignKey("sql_server_connections.id"), nullable=False)
    can_execute = Column(Boolean, default=True)
    can_export = Column(Boolean, default=True)
    can_schedule = Column(Boolean, default=False)
    max_execution_time = Column(Integer, default=300)  # seconds
    max_result_rows = Column(Integer, default=10000)
    allowed_operations = Column(JSON)  # List of allowed SQL operations
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))

    # Relationships
    user = relationship("User", back_populates="server_permissions")
    server = relationship("SQLServerConnection", back_populates="user_permissions")
    creator = relationship("User", foreign_keys=[created_by])

    # Unique constraint
    __table_args__ = (
        {"schema": None},
    )


class AuditLog(Base):
    """Comprehensive audit logging"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(100), nullable=False)
    resource_type = Column(String(100))
    resource_id = Column(String(100))
    details = Column(JSON)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    session_id = Column(String(255))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    severity = Column(String(20), default="INFO")
    category = Column(String(50))
    
    # Security fields
    risk_score = Column(Integer, default=0)
    is_suspicious = Column(Boolean, default=False)
    alert_triggered = Column(Boolean, default=False)

    # Relationships
    user = relationship("User", back_populates="audit_logs")