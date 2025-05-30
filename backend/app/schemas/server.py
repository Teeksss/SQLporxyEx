"""
Complete Server Schemas - Final Version
Created: 2025-05-29 14:38:00 UTC by Teeksss
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, validator
from app.models.sql_server import ServerType, Environment, HealthStatus
from app.models.user import UserRole


class ServerBase(BaseModel):
    """Base server schema"""
    name: str
    server_type: ServerType
    host: str
    port: int
    database: str
    username: str
    environment: Environment
    description: Optional[str] = None
    is_read_only: bool = False
    max_connections: Optional[int] = 10
    connection_timeout: Optional[int] = 30
    
    @validator('name')
    def name_validation(cls, v):
        if len(v) < 3:
            raise ValueError('Server name must be at least 3 characters')
        return v
    
    @validator('port')
    def port_validation(cls, v):
        if v < 1 or v > 65535:
            raise ValueError('Port must be between 1 and 65535')
        return v


class ServerCreate(ServerBase):
    """Server creation schema"""
    password: str
    
    @validator('password')
    def password_validation(cls, v):
        if len(v) < 1:
            raise ValueError('Password cannot be empty')
        return v


class ServerUpdate(BaseModel):
    """Server update schema"""
    name: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    description: Optional[str] = None
    is_read_only: Optional[bool] = None
    max_connections: Optional[int] = None
    connection_timeout: Optional[int] = None
    is_active: Optional[bool] = None
    allowed_roles: Optional[List[UserRole]] = None


class ServerResponse(BaseModel):
    """Server response schema"""
    id: int
    name: str
    server_type: ServerType
    host: str
    port: int
    database: str
    username: str
    environment: Environment
    description: Optional[str]
    is_read_only: bool
    max_connections: Optional[int]
    connection_timeout: Optional[int]
    is_active: bool
    health_status: HealthStatus
    last_health_check: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    created_by_id: Optional[int]
    allowed_roles: Optional[List[UserRole]]
    
    class Config:
        from_attributes = True
        
    @classmethod
    def from_orm(cls, obj):
        return cls(
            id=obj.id,
            name=obj.name,
            server_type=obj.server_type,
            host=obj.host,
            port=obj.port,
            database=obj.database,
            username=obj.username,
            environment=obj.environment,
            description=obj.description,
            is_read_only=obj.is_read_only,
            max_connections=obj.max_connections,
            connection_timeout=obj.connection_timeout,
            is_active=obj.is_active,
            health_status=obj.health_status,
            last_health_check=obj.last_health_check,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
            created_by_id=obj.created_by_id,
            allowed_roles=obj.allowed_roles
        )


class ServerHealth(BaseModel):
    """Server health schema"""
    server_id: int
    status: HealthStatus
    response_time_ms: Optional[int]
    error_message: Optional[str]
    last_check: datetime
    details: Optional[dict]