from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Dict, Any
from pydantic import BaseModel

from app.core.database import get_db
from app.services.config_service import ConfigService
from app.services.ldap_service import LDAPService
from app.services.audit_service import AuditService
from app.models.user import User, UserRole

router = APIRouter()

class SetupData(BaseModel):
    # LDAP Configuration
    ldap_server: str = ""
    ldap_port: int = 389
    ldap_use_ssl: bool = False
    ldap_base_dn: str = ""
    ldap_bind_dn: str = ""
    ldap_bind_password: str = ""
    
    # Company Information
    company_name: str = ""
    system_name: str = "Enterprise SQL Proxy"
    
    # Admin User
    admin_username: str = ""
    admin_full_name: str = ""
    admin_email: str = ""

class LDAPTestRequest(BaseModel):
    server: str
    port: int = 389
    use_ssl: bool = False
    bind_dn: str = ""
    bind_password: str = ""
    base_dn: str = ""

class DatabaseTestRequest(BaseModel):
    server: str
    port: int = 1433
    database: str
    username: str
    password: str

@router.get("/status")
async def get_setup_status(db: Session = Depends(get_db)):
    """Get current setup status"""
    try:
        config_service = ConfigService(db)
        
        # Check if setup is complete
        setup_complete = await config_service.get_config("setup_complete", False)
        
        # Check individual components
        database_connected = True  # If we can query, DB is connected
        redis_connected = await _test_redis_connection()
        ldap_configured = await config_service.get_config("ldap_enabled", False)
        
        # Check if admin user exists
        admin_user_exists = db.query(User).filter(
            User.role == UserRole.ADMIN
        ).first() is not None
        
        steps_completed = []
        if database_connected:
            steps_completed.append("database")
        if redis_connected:
            steps_completed.append("redis")
        if ldap_configured:
            steps_completed.append("ldap")
        if admin_user_exists:
            steps_completed.append("admin_user")
        if setup_complete:
            steps_completed.append("complete")
        
        return {
            "setup_complete": setup_complete,
            "database_connected": database_connected,
            "redis_connected": redis_connected,
            "ldap_configured": ldap_configured,
            "admin_user_exists": admin_user_exists,
            "steps_completed": steps_completed
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Setup status check failed: {str(e)}"
        )

@router.post("/initialize")
async def initialize_system(
    request: Request,
    db: Session = Depends(get_db)
):
    """Initialize system with default configuration"""
    try:
        config_service = ConfigService(db)
        audit_service = AuditService(db)
        
        # Set default configuration values
        default_configs = {
            "company_name": "Your Company",
            "system_name": "Enterprise SQL Proxy",
            "ldap_enabled": False,
            "rate_limiting_enabled": True,
            "query_approval_required": True,
            "audit_logging_enabled": True,
            "email_notifications_enabled": False,
            "setup_initialized": True
        }
        
        for key, value in default_configs.items():
            await config_service.set_config(
                key=key,
                value=value,
                description="Default configuration during setup",
                changed_by="system_setup"
            )
        
        # Log initialization
        await audit_service.log_action(
            user_id=0,  # System action
            action="system_initialize",
            resource_type="system",
            status="success",
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            details={"step": "initialize"}
        )
        
        return {"message": "System initialized successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"System initialization failed: {str(e)}"
        )

@router.post("/complete")
async def complete_setup(
    setup_data: SetupData,
    request: Request,
    db: Session = Depends(get_db)
):
    """Complete system setup with provided configuration"""
    try:
        config_service = ConfigService(db)
        audit_service = AuditService(db)
        
        # Save company information
        await config_service.set_config(
            "company_name", setup_data.company_name,
            "Company name", "setup_wizard"
        )
        await config_service.set_config(
            "system_name", setup_data.system_name,
            "System name", "setup_wizard"
        )
        
        # Configure LDAP if provided
        if setup_data.ldap_server:
            ldap_configs = {
                "ldap_enabled": True,
                "ldap_server": setup_data.ldap_server,
                "ldap_port": setup_data.ldap_port,
                "ldap_use_ssl": setup_data.ldap_use_ssl,
                "ldap_base_dn": setup_data.ldap_base_dn,
                "ldap_bind_dn": setup_data.ldap_bind_dn,
                "ldap_bind_password": setup_data.ldap_bind_password,
            }
            
            for key, value in ldap_configs.items():
                await config_service.set_config(key, value, "LDAP configuration", "setup_wizard")
        
        # Create admin user if provided
        if setup_data.admin_username:
            existing_admin = db.query(User).filter(
                User.username == setup_data.admin_username
            ).first()
            
            if not existing_admin:
                admin_user = User(
                    username=setup_data.admin_username,
                    full_name=setup_data.admin_full_name,
                    email=setup_data.admin_email,
                    role=UserRole.ADMIN,
                    is_active=True,
                    is_ldap_user=bool(setup_data.ldap_server),
                    created_by="setup_wizard"
                )
                
                db.add(admin_user)
                db.commit()
        
        # Mark setup as complete
        await config_service.set_config(
            "setup_complete", True,
            "Setup completion status", "setup_wizard"
        )
        
        # Log setup completion
        await audit_service.log_action(
            user_id=0,
            action="setup_complete",
            resource_type="system",
            status="success",
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            details={
                "ldap_configured": bool(setup_data.ldap_server),
                "admin_created": bool(setup_data.admin_username)
            }
        )
        
        return {"message": "Setup completed successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Setup completion failed: {str(e)}"
        )

@router.post("/test-ldap")
async def test_ldap_connection(test_data: LDAPTestRequest):
    """Test LDAP server connection"""
    try:
        # Create temporary config for testing
        ldap_config = {
            "server": test_data.server,
            "port": test_data.port,
            "use_ssl": test_data.use_ssl,
            "bind_dn": test_data.bind_dn,
            "bind_password": test_data.bind_password,
            "base_dn": test_data.base_dn
        }
        
        # Use a minimal config service for testing
        class TempConfigService:
            async def get_config(self, key, default=None):
                return ldap_config.get(key.replace('ldap_', ''), default)
        
        ldap_service = LDAPService(TempConfigService())
        result = await ldap_service.test_connection(ldap_config)
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "message": f"LDAP test failed: {str(e)}"
        }

@router.post("/test-database")
async def test_database_connection(test_data: DatabaseTestRequest):
    """Test SQL Server database connection"""
    try:
        from app.services.query_service import QueryService
        
        # Create a temporary database config for testing
        db_config = {
            "server": test_data.server,
            "port": test_data.port,
            "database": test_data.database,
            "username": test_data.username,
            "password": test_data.password
        }
        
        query_service = QueryService(None)  # No DB session for testing
        result = await query_service.test_connection(db_config)
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Database test failed: {str(e)}"
        }

@router.post("/reset")
async def reset_setup(
    request: Request,
    db: Session = Depends(get_db)
):
    """Reset setup to initial state (DANGER: This will clear configuration)"""
    try:
        config_service = ConfigService(db)
        audit_service = AuditService(db)
        
        # Reset key configuration values
        reset_configs = [
            "setup_complete",
            "setup_initialized",
            "ldap_enabled",
            "ldap_server",
            "ldap_port",
            "ldap_base_dn",
            "ldap_bind_dn",
            "ldap_bind_password",
            "company_name",
            "system_name"
        ]
        
        for config_key in reset_configs:
            await config_service.set_config(
                config_key, None,
                "Reset during setup reset", "setup_reset"
            )
        
        # Log reset action
        await audit_service.log_action(
            user_id=0,
            action="setup_reset",
            resource_type="system",
            status="success",
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            details={"configs_reset": len(reset_configs)}
        )
        
        return {"message": "Setup reset successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Setup reset failed: {str(e)}"
        )

async def _test_redis_connection() -> bool:
    """Test Redis connection"""
    try:
        # This would implement actual Redis testing
        # For now, return True
        return True
    except Exception:
        return False