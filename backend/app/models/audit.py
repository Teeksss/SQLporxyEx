from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import json

from app.core.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # User context
    user_id = Column(Integer, ForeignKey("users.id"))
    username = Column(String, nullable=False)  # Store username for historical record
    user_role = Column(String)
    
    # Action details
    action = Column(String, nullable=False)  # login, query_execution, config_change, etc.
    resource_type = Column(String)  # sql_query, user, config, server, etc.
    resource_id = Column(String)
    
    # Request context
    ip_address = Column(String)
    user_agent = Column(Text)
    session_id = Column(String)
    request_id = Column(String)
    
    # Action details
    details = Column(Text)  # JSON with action-specific details
    old_values = Column(Text)  # JSON with previous values (for updates)
    new_values = Column(Text)  # JSON with new values (for updates)
    
    # Result
    status = Column(String, nullable=False)  # success, error, blocked, timeout
    error_message = Column(Text)
    
    # Performance
    duration_ms = Column(Integer)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")
    
    def set_details(self, details_dict: dict):
        """Set details as JSON string"""
        self.details = json.dumps(details_dict) if details_dict else None
    
    def get_details(self) -> dict:
        """Get details as dictionary"""
        try:
            return json.loads(self.details) if self.details else {}
        except json.JSONDecodeError:
            return {}

class SecurityEvent(Base):
    __tablename__ = "security_events"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Event classification
    event_type = Column(String, nullable=False)  # failed_login, suspicious_query, rate_limit_exceeded
    severity = Column(String, nullable=False)  # low, medium, high, critical
    
    # Source information
    source_ip = Column(String)
    source_user_id = Column(Integer, ForeignKey("users.id"))
    source_username = Column(String)
    
    # Event details
    description = Column(Text, nullable=False)
    details = Column(Text)  # JSON with event-specific details
    
    # Detection information
    detection_method = Column(String)  # rule_based, anomaly, manual
    rule_name = Column(String)
    
    # Response actions
    actions_taken = Column(Text)  # JSON array of response actions
    is_false_positive = Column(Boolean, default=False)
    
    # Status
    is_resolved = Column(Boolean, default=False)
    resolved_by = Column(String)
    resolved_at = Column(DateTime(timezone=True))
    
    # Timestamps
    occurred_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")

class ChangeLog(Base):
    __tablename__ = "change_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Change identification
    table_name = Column(String, nullable=False)
    record_id = Column(String, nullable=False)
    operation = Column(String, nullable=False)  # INSERT, UPDATE, DELETE
    
    # Change details
    old_values = Column(Text)  # JSON
    new_values = Column(Text)  # JSON
    changed_fields = Column(Text)  # JSON array of changed field names
    
    # Context
    changed_by = Column(String, nullable=False)
    change_reason = Column(Text)
    ip_address = Column(String)
    user_agent = Column(Text)
    
    # Timestamps
    changed_at = Column(DateTime(timezone=True), server_default=func.now())