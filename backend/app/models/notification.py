"""
Complete Notification Models - Final Version
Created: 2025-05-29 13:50:14 UTC by Teeksss
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Enum, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class NotificationStatus(enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"


class NotificationChannel(enum.Enum):
    EMAIL = "email"
    WEBHOOK = "webhook"
    SLACK = "slack"
    TEAMS = "teams"
    SMS = "sms"


class NotificationPriority(enum.Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationRule(Base):
    """Notification rules for automated notifications"""
    __tablename__ = "notification_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(Text)
    notification_type = Column(String(100), nullable=False)
    conditions = Column(JSON)  # JSON conditions for when to trigger
    actions = Column(JSON)     # JSON actions to take
    priority = Column(Enum(NotificationPriority), default=NotificationPriority.NORMAL)
    cooldown_minutes = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))

    # Relationships
    creator = relationship("User", back_populates="notification_rules")
    deliveries = relationship("NotificationDelivery", back_populates="rule")


class NotificationDelivery(Base):
    """Record of notification deliveries"""
    __tablename__ = "notification_deliveries"

    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, ForeignKey("notification_rules.id"), nullable=True)
    type = Column(String(100), nullable=False)
    channel = Column(Enum(NotificationChannel), nullable=False)
    priority = Column(Enum(NotificationPriority), default=NotificationPriority.NORMAL)
    recipients = Column(Text)  # Comma-separated list
    subject = Column(String(500))
    message = Column(Text)
    data = Column(JSON)  # Additional data
    status = Column(Enum(NotificationStatus), default=NotificationStatus.PENDING)
    error_message = Column(Text)
    delivered_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    rule = relationship("NotificationRule", back_populates="deliveries")


class NotificationTemplate(Base):
    """Email and notification templates"""
    __tablename__ = "notification_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(Text)
    type = Column(String(100), nullable=False)
    subject_template = Column(String(500))
    body_template = Column(Text)
    html_template = Column(Text)
    variables = Column(JSON)  # List of available variables
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))

    # Relationships
    creator = relationship("User")


class NotificationPreference(Base):
    """User notification preferences"""
    __tablename__ = "notification_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    notification_type = Column(String(100), nullable=False)
    channel = Column(Enum(NotificationChannel), nullable=False)
    is_enabled = Column(Boolean, default=True)
    min_priority = Column(Enum(NotificationPriority), default=NotificationPriority.LOW)
    cooldown_minutes = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="notification_preferences")

    # Unique constraint
    __table_args__ = (
        {"schema": None},
    )