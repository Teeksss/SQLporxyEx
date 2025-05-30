from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.core.database import get_db
from app.models.user import User, UserRole
from app.api.auth import get_current_user
from app.services.discovery_service import DiscoveryService

router = APIRouter()

def require_admin(current_user: User = Depends(get_current_user)):
    """Dependency to require admin role"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    return current_user

@router.get("/")
async def discover_all_services(
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Discover all available services on the network"""
    try:
        discovery_service = DiscoveryService()
        result = await discovery_service.discover_all_services()
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Service discovery failed: {str(e)}"
        )

@router.get("/ldap")
async def discover_ldap_servers(
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Discover LDAP servers on the network"""
    try:
        discovery_service = DiscoveryService()
        ldap_servers = await discovery_service.discover_ldap_servers()
        
        return {
            "ldap_servers": ldap_servers,
            "count": len(ldap_servers)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"LDAP discovery failed: {str(e)}"
        )

@router.get("/sql-servers")
async def discover_sql_servers(
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Discover SQL Server instances on the network"""
    try:
        discovery_service = DiscoveryService()
        sql_servers = await discovery_service.discover_sql_servers()
        
        return {
            "sql_servers": sql_servers,
            "count": len(sql_servers)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"SQL Server discovery failed: {str(e)}"
        )