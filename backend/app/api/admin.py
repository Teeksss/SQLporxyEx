"""
Complete Admin API Router - Final Version
Created: 2025-05-29 14:34:05 UTC by Teeksss
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc

from app.core import deps
from app.models.user import User, UserRole, UserStatus
from app.models.sql_server import SQLServerConnection, ServerType, Environment
from app.models.query import QueryExecution, QueryStatus
from app.models.audit import AuditLog
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.schemas.server import ServerCreate, ServerUpdate, ServerResponse
from app.services.audit import audit_service
from app.services.sql_proxy import sql_proxy_service

router = APIRouter()


# User Management Endpoints
@router.get("/users", response_model=List[UserResponse])
async def get_all_users(
    current_user: User = Depends(deps.get_current_admin_user),
    db: Session = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=500),
    role: Optional[UserRole] = Query(None),
    status: Optional[UserStatus] = Query(None),
    search: Optional[str] = Query(None)
):
    """Get all users (admin only)"""
    
    query = db.query(User)
    
    if role:
        query = query.filter(User.role == role)
    
    if status:
        query = query.filter(User.status == status)
    
    if search:
        query = query.filter(
            (User.username.ilike(f"%{search}%")) |
            (User.email.ilike(f"%{search}%")) |
            (User.first_name.ilike(f"%{search}%")) |
            (User.last_name.ilike(f"%{search}%"))
        )
    
    users = query.offset(skip).limit(limit).all()
    
    return [UserResponse.from_orm(user) for user in users]


@router.post("/users", response_model=UserResponse)
async def create_user(
    request: Request,
    user_data: UserCreate,
    current_user: User = Depends(deps.get_current_admin_user),
    db: Session = Depends(deps.get_db)
):
    """Create new user (admin only)"""
    
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.username == user_data.username) | 
        (User.email == user_data.email)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this username or email already exists"
        )
    
    # Create new user
    from app.core.security import get_password_hash
    
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        role=user_data.role,
        status=UserStatus.ACTIVE,
        is_active=True,
        is_verified=True
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Log user creation
    await audit_service.log_admin_event(
        admin_action="user_created",
        admin_user_id=current_user.id,
        target_user_id=new_user.id,
        target_resource_type="user",
        target_resource_id=str(new_user.id),
        changes={
            "username": new_user.username,
            "email": new_user.email,
            "role": new_user.role.value
        },
        ip_address=request.client.host
    )
    
    return UserResponse.from_orm(new_user)


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(deps.get_current_admin_user),
    db: Session = Depends(deps.get_db)
):
    """Get user by ID (admin only)"""
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse.from_orm(user)


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    request: Request,
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(deps.get_current_admin_user),
    db: Session = Depends(deps.get_db)
):
    """Update user (admin only)"""
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Track changes
    changes = {}
    
    # Update fields
    if user_data.first_name is not None:
        changes["first_name"] = {"old": user.first_name, "new": user_data.first_name}
        user.first_name = user_data.first_name
    
    if user_data.last_name is not None:
        changes["last_name"] = {"old": user.last_name, "new": user_data.last_name}
        user.last_name = user_data.last_name
    
    if user_data.email is not None:
        changes["email"] = {"old": user.email, "new": user_data.email}
        user.email = user_data.email
    
    if user_data.role is not None:
        changes["role"] = {"old": user.role.value, "new": user_data.role.value}
        user.role = user_data.role
    
    if user_data.status is not None:
        changes["status"] = {"old": user.status.value, "new": user_data.status.value}
        user.status = user_data.status
    
    if user_data.is_active is not None:
        changes["is_active"] = {"old": user.is_active, "new": user_data.is_active}
        user.is_active = user_data.is_active
    
    user.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(user)
    
    # Log user update
    await audit_service.log_admin_event(
        admin_action="user_updated",
        admin_user_id=current_user.id,
        target_user_id=user.id,
        target_resource_type="user",
        target_resource_id=str(user.id),
        changes=changes,
        ip_address=request.client.host
    )
    
    return UserResponse.from_orm(user)


@router.delete("/users/{user_id}")
async def delete_user(
    request: Request,
    user_id: int,
    current_user: User = Depends(deps.get_current_admin_user),
    db: Session = Depends(deps.get_db)
):
    """Delete user (admin only)"""
    
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Store user data for logging
    user_data = {
        "username": user.username,
        "email": user.email,
        "role": user.role.value
    }
    
    db.delete(user)
    db.commit()
    
    # Log user deletion
    await audit_service.log_admin_event(
        admin_action="user_deleted",
        admin_user_id=current_user.id,
        target_user_id=user_id,
        target_resource_type="user",
        target_resource_id=str(user_id),
        changes=user_data,
        ip_address=request.client.host
    )
    
    return {"message": "User deleted successfully"}


# Server Management Endpoints
@router.get("/servers", response_model=List[ServerResponse])
async def get_all_servers(
    current_user: User = Depends(deps.get_current_admin_user),
    db: Session = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=500),
    server_type: Optional[ServerType] = Query(None),
    environment: Optional[Environment] = Query(None),
    is_active: Optional[bool] = Query(None)
):
    """Get all servers (admin only)"""
    
    query = db.query(SQLServerConnection)
    
    if server_type:
        query = query.filter(SQLServerConnection.server_type == server_type)
    
    if environment:
        query = query.filter(SQLServerConnection.environment == environment)
    
    if is_active is not None:
        query = query.filter(SQLServerConnection.is_active == is_active)
    
    servers = query.offset(skip).limit(limit).all()
    
    return [ServerResponse.from_orm(server) for server in servers]


@router.post("/servers", response_model=ServerResponse)
async def create_server(
    request: Request,
    server_data: ServerCreate,
    current_user: User = Depends(deps.get_current_admin_user),
    db: Session = Depends(deps.get_db)
):
    """Create new server connection (admin only)"""
    
    # Check if server already exists
    existing_server = db.query(SQLServerConnection).filter(
        SQLServerConnection.name == server_data.name
    ).first()
    
    if existing_server:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Server with this name already exists"
        )
    
    # Create new server
    new_server = SQLServerConnection(
        name=server_data.name,
        server_type=server_data.server_type,
        host=server_data.host,
        port=server_data.port,
        database=server_data.database,
        username=server_data.username,
        password=server_data.password,  # Should be encrypted in production
        environment=server_data.environment,
        description=server_data.description,
        is_read_only=server_data.is_read_only,
        max_connections=server_data.max_connections,
        connection_timeout=server_data.connection_timeout,
        is_active=True,
        created_by_id=current_user.id
    )
    
    db.add(new_server)
    db.commit()
    db.refresh(new_server)
    
    # Log server creation
    await audit_service.log_admin_event(
        admin_action="server_created",
        admin_user_id=current_user.id,
        target_resource_type="server",
        target_resource_id=str(new_server.id),
        changes={
            "name": new_server.name,
            "server_type": new_server.server_type.value,
            "host": new_server.host,
            "environment": new_server.environment.value
        },
        ip_address=request.client.host
    )
    
    return ServerResponse.from_orm(new_server)


@router.get("/servers/{server_id}", response_model=ServerResponse)
async def get_server(
    server_id: int,
    current_user: User = Depends(deps.get_current_admin_user),
    db: Session = Depends(deps.get_db)
):
    """Get server by ID (admin only)"""
    
    server = db.query(SQLServerConnection).filter(
        SQLServerConnection.id == server_id
    ).first()
    
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )
    
    return ServerResponse.from_orm(server)


@router.put("/servers/{server_id}", response_model=ServerResponse)
async def update_server(
    request: Request,
    server_id: int,
    server_data: ServerUpdate,
    current_user: User = Depends(deps.get_current_admin_user),
    db: Session = Depends(deps.get_db)
):
    """Update server (admin only)"""
    
    server = db.query(SQLServerConnection).filter(
        SQLServerConnection.id == server_id
    ).first()
    
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )
    
    # Track changes
    changes = {}
    
    # Update fields
    update_fields = [
        'name', 'host', 'port', 'database', 'username', 'password',
        'description', 'is_read_only', 'max_connections', 'connection_timeout',
        'is_active'
    ]
    
    for field in update_fields:
        new_value = getattr(server_data, field, None)
        if new_value is not None:
            old_value = getattr(server, field)
            if old_value != new_value:
                changes[field] = {"old": str(old_value), "new": str(new_value)}
                setattr(server, field, new_value)
    
    server.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(server)
    
    # Log server update
    await audit_service.log_admin_event(
        admin_action="server_updated",
        admin_user_id=current_user.id,
        target_resource_type="server",
        target_resource_id=str(server.id),
        changes=changes,
        ip_address=request.client.host
    )
    
    return ServerResponse.from_orm(server)


@router.delete("/servers/{server_id}")
async def delete_server(
    request: Request,
    server_id: int,
    current_user: User = Depends(deps.get_current_admin_user),
    db: Session = Depends(deps.get_db)
):
    """Delete server (admin only)"""
    
    server = db.query(SQLServerConnection).filter(
        SQLServerConnection.id == server_id
    ).first()
    
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )
    
    # Store server data for logging
    server_data = {
        "name": server.name,
        "server_type": server.server_type.value,
        "host": server.host,
        "environment": server.environment.value
    }
    
    db.delete(server)
    db.commit()
    
    # Log server deletion
    await audit_service.log_admin_event(
        admin_action="server_deleted",
        admin_user_id=current_user.id,
        target_resource_type="server",
        target_resource_id=str(server_id),
        changes=server_data,
        ip_address=request.client.host
    )
    
    return {"message": "Server deleted successfully"}


# System Analytics and Monitoring
@router.get("/dashboard", response_model=Dict[str, Any])
async def get_admin_dashboard(
    current_user: User = Depends(deps.get_current_admin_user),
    db: Session = Depends(deps.get_db)
):
    """Get admin dashboard data"""
    
    # Get counts
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    total_servers = db.query(SQLServerConnection).count()
    active_servers = db.query(SQLServerConnection).filter(
        SQLServerConnection.is_active == True
    ).count()
    
    # Get recent query statistics
    last_24h = datetime.utcnow() - timedelta(hours=24)
    recent_queries = db.query(QueryExecution).filter(
        QueryExecution.started_at >= last_24h
    ).count()
    
    successful_queries = db.query(QueryExecution).filter(
        QueryExecution.started_at >= last_24h,
        QueryExecution.status == QueryStatus.SUCCESS
    ).count()
    
    failed_queries = db.query(QueryExecution).filter(
        QueryExecution.started_at >= last_24h,
        QueryExecution.status == QueryStatus.FAILED
    ).count()
    
    # Get top users by query count
    top_users = db.query(
        User.username,
        func.count(QueryExecution.id).label('query_count')
    ).join(QueryExecution).filter(
        QueryExecution.started_at >= last_24h
    ).group_by(User.id, User.username).order_by(
        desc('query_count')
    ).limit(5).all()
    
    # Get recent security events
    recent_security_events = db.query(AuditLog).filter(
        AuditLog.category == "security",
        AuditLog.timestamp >= last_24h
    ).count()
    
    return {
        "users": {
            "total": total_users,
            "active": active_users,
            "inactive": total_users - active_users
        },
        "servers": {
            "total": total_servers,
            "active": active_servers,
            "inactive": total_servers - active_servers
        },
        "queries_24h": {
            "total": recent_queries,
            "successful": successful_queries,
            "failed": failed_queries,
            "success_rate": (successful_queries / recent_queries * 100) if recent_queries > 0 else 0
        },
        "top_users_24h": [
            {"username": user.username, "query_count": user.query_count}
            for user in top_users
        ],
        "security_events_24h": recent_security_events,
        "system_health": await sql_proxy_service.health_check(),
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/audit-logs", response_model=Dict[str, Any])
async def get_audit_logs(
    current_user: User = Depends(deps.get_current_admin_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=500),
    category: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    user_id: Optional[int] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None)
):
    """Get audit logs (admin only)"""
    
    audit_logs = await audit_service.get_audit_logs(
        user_id=user_id,
        action=action,
        category=category,
        severity=severity,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=skip
    )
    
    return audit_logs


@router.get("/system-health", response_model=Dict[str, Any])
async def get_system_health(
    current_user: User = Depends(deps.get_current_admin_user)
):
    """Get detailed system health (admin only)"""
    
    from app.services.health import HealthService
    
    health_service = HealthService()
    return await health_service.get_detailed_status()


@router.post("/system/maintenance")
async def enable_maintenance_mode(
    request: Request,
    maintenance_data: Dict[str, Any],
    current_user: User = Depends(deps.get_current_admin_user)
):
    """Enable/disable maintenance mode (admin only)"""
    
    enabled = maintenance_data.get("enabled", False)
    message = maintenance_data.get("message", "System is under maintenance")
    
    # Log maintenance mode change
    await audit_service.log_admin_event(
        admin_action="maintenance_mode_changed",
        admin_user_id=current_user.id,
        target_resource_type="system",
        target_resource_id="maintenance",
        changes={
            "enabled": enabled,
            "message": message
        },
        ip_address=request.client.host
    )
    
    return {
        "message": f"Maintenance mode {'enabled' if enabled else 'disabled'}",
        "maintenance_enabled": enabled,
        "maintenance_message": message
    }