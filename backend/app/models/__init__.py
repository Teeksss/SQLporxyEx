"""
Models Module - Database Models and Schemas
Created: 2025-05-29 14:06:59 UTC by Teeksss

This module contains all database models for the Enterprise SQL Proxy System
including User, SQLServer, Query, and Notification models.
"""

# Import all models
from app.models.user import (
    User,
    UserRole,
    UserStatus,
    UserSession,
    ServerPermission,
    AuditLog
)
from app.models.sql_server import (
    SQLServerConnection,
    ServerType,
    Environment,
    HealthStatus,
    ConnectionStatus,
    ServerHealthCheck,
    ServerPerformanceMetric,
    ServerConfiguration,
    ServerTag
)
from app.models.query import (
    QueryExecution,
    QueryStatus,
    QueryType,
    RiskLevel,
    QueryApproval,
    ApprovalStatus,
    QueryWhitelist,
    QueryTemplate,
    QueryExport,
    QuerySchedule
)
from app.models.notification import (
    NotificationRule,
    NotificationDelivery,
    NotificationTemplate,
    NotificationPreference,
    NotificationStatus,
    NotificationChannel,
    NotificationPriority
)

# Import base
from app.core.database import Base

# Module metadata
__version__ = "2.0.0"
__author__ = "Teeksss"
__description__ = "Database models for Enterprise SQL Proxy System"

# Model registry for easy access
MODEL_REGISTRY = {
    # User models
    "User": User,
    "UserSession": UserSession,
    "ServerPermission": ServerPermission,
    "AuditLog": AuditLog,
    
    # Server models
    "SQLServerConnection": SQLServerConnection,
    "ServerHealthCheck": ServerHealthCheck,
    "ServerPerformanceMetric": ServerPerformanceMetric,
    "ServerConfiguration": ServerConfiguration,
    "ServerTag": ServerTag,
    
    # Query models
    "QueryExecution": QueryExecution,
    "QueryApproval": QueryApproval,
    "QueryWhitelist": QueryWhitelist,
    "QueryTemplate": QueryTemplate,
    "QueryExport": QueryExport,
    "QuerySchedule": QuerySchedule,
    
    # Notification models
    "NotificationRule": NotificationRule,
    "NotificationDelivery": NotificationDelivery,
    "NotificationTemplate": NotificationTemplate,
    "NotificationPreference": NotificationPreference
}

# Enum registry
ENUM_REGISTRY = {
    # User enums
    "UserRole": UserRole,
    "UserStatus": UserStatus,
    
    # Server enums
    "ServerType": ServerType,
    "Environment": Environment,
    "HealthStatus": HealthStatus,
    "ConnectionStatus": ConnectionStatus,
    
    # Query enums
    "QueryStatus": QueryStatus,
    "QueryType": QueryType,
    "RiskLevel": RiskLevel,
    "ApprovalStatus": ApprovalStatus,
    
    # Notification enums
    "NotificationStatus": NotificationStatus,
    "NotificationChannel": NotificationChannel,
    "NotificationPriority": NotificationPriority
}

# Model metadata
MODEL_METADATA = {
    "total_models": len(MODEL_REGISTRY),
    "total_enums": len(ENUM_REGISTRY),
    "user_models": 4,
    "server_models": 5,
    "query_models": 6,
    "notification_models": 4,
    "created_by": __author__,
    "version": __version__,
    "last_updated": "2025-05-29T14:06:59Z"
}

# Utility functions
def get_model_by_name(name: str):
    """Get model class by name"""
    return MODEL_REGISTRY.get(name)

def get_enum_by_name(name: str):
    """Get enum class by name"""
    return ENUM_REGISTRY.get(name)

def get_all_models():
    """Get all model classes"""
    return list(MODEL_REGISTRY.values())

def get_all_enums():
    """Get all enum classes"""
    return list(ENUM_REGISTRY.values())

def get_model_names():
    """Get all model names"""
    return list(MODEL_REGISTRY.keys())

def get_enum_names():
    """Get all enum names"""
    return list(ENUM_REGISTRY.keys())

def validate_models():
    """Validate all models are properly configured"""
    try:
        for model_name, model_class in MODEL_REGISTRY.items():
            # Check if model has required attributes
            if not hasattr(model_class, '__tablename__'):
                raise ValueError(f"Model {model_name} missing __tablename__")
            
            if not hasattr(model_class, 'id'):
                raise ValueError(f"Model {model_name} missing id field")
        
        return True, "All models are valid"
    except Exception as e:
        return False, str(e)

def get_model_info():
    """Get detailed information about all models"""
    info = {
        "metadata": MODEL_METADATA,
        "models": {},
        "enums": {}
    }
    
    # Add model information
    for name, model in MODEL_REGISTRY.items():
        info["models"][name] = {
            "table_name": getattr(model, '__tablename__', None),
            "module": model.__module__,
            "doc": model.__doc__
        }
    
    # Add enum information
    for name, enum in ENUM_REGISTRY.items():
        info["enums"][name] = {
            "values": [e.value for e in enum],
            "module": enum.__module__,
            "doc": enum.__doc__
        }
    
    return info

# Export all models and utilities
__all__ = [
    # User models
    "User",
    "UserRole",
    "UserStatus", 
    "UserSession",
    "ServerPermission",
    "AuditLog",
    
    # Server models
    "SQLServerConnection",
    "ServerType",
    "Environment",
    "HealthStatus",
    "ConnectionStatus",
    "ServerHealthCheck",
    "ServerPerformanceMetric",
    "ServerConfiguration",
    "ServerTag",
    
    # Query models
    "QueryExecution",
    "QueryStatus",
    "QueryType",
    "RiskLevel",
    "QueryApproval",
    "ApprovalStatus",
    "QueryWhitelist",
    "QueryTemplate",
    "QueryExport",
    "QuerySchedule",
    
    # Notification models
    "NotificationRule",
    "NotificationDelivery",
    "NotificationTemplate",
    "NotificationPreference",
    "NotificationStatus",
    "NotificationChannel",
    "NotificationPriority",
    
    # Base
    "Base",
    
    # Registries
    "MODEL_REGISTRY",
    "ENUM_REGISTRY",
    "MODEL_METADATA",
    
    # Utilities
    "get_model_by_name",
    "get_enum_by_name",
    "get_all_models",
    "get_all_enums",
    "get_model_names",
    "get_enum_names",
    "validate_models",
    "get_model_info"
]