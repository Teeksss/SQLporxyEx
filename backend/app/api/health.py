"""
Complete Health API Router - Final Version
Created: 2025-05-29 14:50:40 UTC by Teeksss
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core import deps
from app.models.user import User, UserRole
from app.services.health import health_service
from app.services import get_services_health, get_services_metrics

router = APIRouter()


@router.get(
    "/",
    summary="🩺 Basic Health Check",
    description="Quick health check endpoint for load balancers and monitoring systems",
    response_model=Dict[str, Any],
    status_code=200
)
async def health_check():
    """Basic health check"""
    
    try:
        health_data = await health_service.health_check()
        
        if health_data.get("status") == "healthy":
            return {
                "status": "healthy",
                "message": "Enterprise SQL Proxy System is operational",
                "timestamp": health_data.get("timestamp"),
                "version": "2.0.0",
                "uptime_seconds": health_data.get("uptime_seconds", 0)
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service is unhealthy"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Health check failed: {str(e)}"
        )


@router.get(
    "/detailed",
    summary="🔍 Detailed Health Status",
    description="Comprehensive health status including all system components",
    response_model=Dict[str, Any]
)
async def detailed_health(
    current_user: User = Depends(deps.get_current_user)
):
    """Get detailed health status"""
    
    try:
        # Only allow admin users to see detailed health
        if current_user.role not in [UserRole.ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required for detailed health information"
            )
        
        health_data = await health_service.get_system_health()
        return health_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get detailed health status: {str(e)}"
        )


@router.get(
    "/services",
    summary="⚙️ Services Health",
    description="Health status of all application services",
    response_model=Dict[str, Any]
)
async def services_health(
    current_user: User = Depends(deps.get_current_user)
):
    """Get services health status"""
    
    try:
        # Only allow admin and analyst users
        if current_user.role not in [UserRole.ADMIN, UserRole.ANALYST]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin or analyst access required"
            )
        
        services_health_data = await get_services_health()
        
        return {
            "services": services_health_data,
            "timestamp": "2025-05-29T14:50:40Z",
            "total_services": len(services_health_data),
            "healthy_services": sum(
                1 for service in services_health_data.values()
                if service.get("status") == "healthy"
            ),
            "overall_status": "healthy" if all(
                service.get("status") == "healthy"
                for service in services_health_data.values()
            ) else "degraded"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get services health: {str(e)}"
        )


@router.get(
    "/metrics",
    summary="📊 System Metrics",
    description="System performance and operational metrics",
    response_model=Dict[str, Any]
)
async def system_metrics(
    current_user: User = Depends(deps.get_current_admin_user)
):
    """Get system metrics (admin only)"""
    
    try:
        metrics = await get_services_metrics()
        
        return {
            "metrics": metrics,
            "timestamp": "2025-05-29T14:50:40Z",
            "collection_time": "2025-05-29T14:50:40Z"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system metrics: {str(e)}"
        )


@router.get(
    "/admin",
    summary="👑 Admin Health Dashboard",
    description="Comprehensive health dashboard for administrators",
    response_model=Dict[str, Any]
)
async def admin_health_dashboard(
    current_user: User = Depends(deps.get_current_admin_user)
):
    """Get admin health dashboard (admin only)"""
    
    try:
        detailed_status = await health_service.get_detailed_status()
        
        return {
            "dashboard": detailed_status,
            "generated_at": "2025-05-29T14:50:40Z",
            "generated_by": current_user.username,
            "version": "2.0.0"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get admin health dashboard: {str(e)}"
        )


@router.get(
    "/liveness",
    summary="❤️ Liveness Probe",
    description="Kubernetes liveness probe endpoint",
    status_code=200,
    include_in_schema=False
)
async def liveness_probe():
    """Liveness probe for Kubernetes"""
    
    return {"status": "alive", "timestamp": "2025-05-29T14:50:40Z"}


@router.get(
    "/readiness",
    summary="✅ Readiness Probe",
    description="Kubernetes readiness probe endpoint",
    status_code=200,
    include_in_schema=False
)
async def readiness_probe():
    """Readiness probe for Kubernetes"""
    
    try:
        # Check if critical services are ready
        health_data = await health_service.health_check()
        
        if health_data.get("status") == "healthy":
            return {"status": "ready", "timestamp": "2025-05-29T14:50:40Z"}
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service not ready"
            )
            
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready"
        )


@router.get(
    "/startup",
    summary="🚀 Startup Probe",
    description="Kubernetes startup probe endpoint",
    status_code=200,
    include_in_schema=False
)
async def startup_probe():
    """Startup probe for Kubernetes"""
    
    try:
        # Check if application has started successfully
        health_data = await health_service.health_check()
        
        if health_data.get("status") in ["healthy", "degraded"]:
            return {"status": "started", "timestamp": "2025-05-29T14:50:40Z"}
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service not started"
            )
            
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not started"
        )