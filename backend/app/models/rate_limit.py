from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
import json

from app.core.database import Base

class RateLimitType(PyEnum):
    """Rate limit target types"""
    USER = "user"
    IP = "ip"
    ROLE = "role"
    GLOBAL = "global"

class RateLimitProfile(Base):
    __tablename__ = "rate_limit_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text)
    
    # Rate limits
    requests_per_minute = Column(Integer, default=10)
    requests_per_hour = Column(Integer, default=100)
    requests_per_day = Column(Integer, default=1000)
    
    # Query limits
    max_concurrent_queries = Column(Integer, default=3)
    max_query_duration_seconds = Column(Integer, default=300)
    max_result_rows = Column(Integer, default=10000)
    
    # Advanced limits
    max_query_complexity_score = Column(Float, default=100.0)
    allowed_query_types = Column(Text)  # JSON array: ["SELECT", "INSERT"]
    blocked_tables = Column(Text)       # JSON array of blocked table patterns
    allowed_hours = Column(Text)        # JSON array: [9, 10, 11, ..., 17] for business hours
    
    # Profile settings
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=0)  # Higher priority = more permissive
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String)
    
    # Relationships
    users = relationship("User", back_populates="rate_limit_profile")
    rate_limit_rules = relationship("RateLimitRule", back_populates="profile")

class RateLimitRule(Base):
    __tablename__ = "rate_limit_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("rate_limit_profiles.id"))
    
    # Rule identification
    rule_name = Column(String, nullable=False)
    target_type = Column(String, nullable=False)  # user, ip, role, global
    target_value = Column(String)  # user_id, IP address, role name, or "global"
    
    # Limits
    max_requests = Column(Integer, nullable=False)
    window_seconds = Column(Integer, nullable=False)
    
    # Advanced settings
    burst_allowance = Column(Integer, default=0)  # Allow burst above limit
    reset_on_success = Column(Boolean, default=False)  # Reset counter on successful query
    
    # Rule behavior
    is_active = Column(Boolean, default=True)
    applies_to_weekends = Column(Boolean, default=True)
    applies_to_holidays = Column(Boolean, default=True)
    
    # Override settings
    override_global_limits = Column(Boolean, default=False)
    custom_error_message = Column(Text)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))  # Temporary rules
    
    # Relationships
    profile = relationship("RateLimitProfile", back_populates="rate_limit_rules")

class RateLimitExecution(Base):
    __tablename__ = "rate_limit_executions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Tracking information
    target_type = Column(String, nullable=False)
    target_value = Column(String, nullable=False)
    rule_id = Column(Integer, ForeignKey("rate_limit_rules.id"))
    
    # Execution details
    request_count = Column(Integer, default=1)
    window_start = Column(DateTime(timezone=True), nullable=False)
    window_end = Column(DateTime(timezone=True), nullable=False)
    
    # Request metadata
    ip_address = Column(String)
    user_agent = Column(Text)
    endpoint = Column(String)
    
    # Status
    was_blocked = Column(Boolean, default=False)
    reset_reason = Column(String)  # manual, expired, success
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class RateLimitException(Base):
    __tablename__ = "rate_limit_exceptions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Exception target
    target_type = Column(String, nullable=False)  # user, ip, query_pattern
    target_value = Column(String, nullable=False)
    
    # Exception details
    exception_type = Column(String, nullable=False)  # whitelist, blacklist, custom_limit
    description = Column(Text)
    
    # Custom limits for exceptions
    custom_requests_per_hour = Column(Integer)
    custom_max_concurrent = Column(Integer)
    
    # Time-based restrictions
    valid_from = Column(DateTime(timezone=True))
    valid_until = Column(DateTime(timezone=True))
    weekdays_only = Column(Boolean, default=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    created_by = Column(String)
    approved_by = Column(String)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())