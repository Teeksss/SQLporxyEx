from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Enum, Float
from sqlalchemy.sql import func
from enum import Enum as PyEnum
import json

from app.core.database import Base

class ConfigCategory(PyEnum):
    """Configuration categories for organization"""
    SYSTEM = "system"
    SECURITY = "security"
    LDAP = "ldap"
    DATABASE = "database"
    RATE_LIMITING = "rate_limiting"
    NOTIFICATION = "notification"
    THEME = "theme"
    BACKUP = "backup"
    MONITORING = "monitoring"

class ConfigType(PyEnum):
    """Configuration value types"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    JSON = "json"
    PASSWORD = "password"
    URL = "url"
    EMAIL = "email"

class SystemConfig(Base):
    __tablename__ = "system_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True, nullable=False)
    value = Column(Text)
    default_value = Column(Text)
    
    # Metadata
    name = Column(String, nullable=False)
    description = Column(Text)
    category = Column(Enum(ConfigCategory), default=ConfigCategory.SYSTEM)
    config_type = Column(Enum(ConfigType), default=ConfigType.STRING)
    
    # Validation
    validation_regex = Column(String)
    min_value = Column(Float)
    max_value = Column(Float)
    allowed_values = Column(Text)  # JSON array
    
    # Behavior
    is_sensitive = Column(Boolean, default=False)  # Encrypt in database
    requires_restart = Column(Boolean, default=False)
    is_readonly = Column(Boolean, default=False)
    is_advanced = Column(Boolean, default=False)  # Hide from basic UI
    
    # UI properties
    display_order = Column(Integer, default=0)
    ui_component = Column(String)  # input, select, switch, etc.
    ui_props = Column(Text)  # JSON for component properties
    
    # Change tracking
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    updated_by = Column(String)
    
    def get_typed_value(self):
        """Get value converted to appropriate type"""
        if not self.value:
            return self.get_typed_default()
        
        try:
            if self.config_type == ConfigType.INTEGER:
                return int(self.value)
            elif self.config_type == ConfigType.FLOAT:
                return float(self.value)
            elif self.config_type == ConfigType.BOOLEAN:
                return self.value.lower() in ('true', '1', 'yes', 'on')
            elif self.config_type == ConfigType.JSON:
                return json.loads(self.value)
            else:
                return self.value
        except (ValueError, json.JSONDecodeError):
            return self.get_typed_default()
    
    def get_typed_default(self):
        """Get default value converted to appropriate type"""
        if not self.default_value:
            return None
        
        try:
            if self.config_type == ConfigType.INTEGER:
                return int(self.default_value)
            elif self.config_type == ConfigType.FLOAT:
                return float(self.default_value)
            elif self.config_type == ConfigType.BOOLEAN:
                return self.default_value.lower() in ('true', '1', 'yes', 'on')
            elif self.config_type == ConfigType.JSON:
                return json.loads(self.default_value)
            else:
                return self.default_value
        except (ValueError, json.JSONDecodeError):
            return None

class ConfigHistory(Base):
    __tablename__ = "config_history"
    
    id = Column(Integer, primary_key=True, index=True)
    config_key = Column(String, nullable=False)
    old_value = Column(Text)
    new_value = Column(Text)
    changed_by = Column(String)
    change_reason = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class SystemTheme(Base):
    __tablename__ = "system_themes"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Theme properties
    primary_color = Column(String, default="#1890ff")
    secondary_color = Column(String, default="#52c41a")
    background_color = Column(String, default="#ffffff")
    text_color = Column(String, default="#000000")
    
    # Logo and branding
    logo_url = Column(String)
    company_name = Column(String)
    favicon_url = Column(String)
    
    # Advanced styling
    css_variables = Column(Text)  # JSON object with CSS custom properties
    custom_css = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())