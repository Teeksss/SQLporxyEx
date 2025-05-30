from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from pydantic import BaseModel

from app.core.database import get_db
from app.models.user import User, UserRole
from app.api.auth import get_current_user
from app.services.config_service import ConfigService
from app.services.audit_service import AuditService
from app.models.config import ConfigCategory

router = APIRouter()

class ConfigUpdateRequest(BaseModel):
    key: str
    value: Any
    change_reason: str = "Updated via API"

class ConfigBatchUpdateRequest(BaseModel):
    configs: List[ConfigUpdateRequest]
    change_reason: str = "Batch update via API"

def require_admin(current_user: User = Depends(get_current_user)):
    """Dependency to require admin role"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    return current_user

@router.get("/")
async def get_all_configs(
    category: str = None,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get all system configurations"""
    try:
        config_service = ConfigService(db)
        
        if category:
            try:
                cat_enum = ConfigCategory(category)
                return await config_service.get_configs_by_category(cat_enum)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid category")
        else:
            return await config_service.get_all_configs()
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get configurations: {str(e)}"
        )

@router.get("/{key}")
async def get_config(
    key: str,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get specific configuration value"""
    try:
        config_service = ConfigService(db)
        value = await config_service.get_config(key)
        
        if value is None:
            raise HTTPException(status_code=404, detail="Configuration not found")
        
        return {"key": key, "value": value}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get configuration: {str(e)}"
        )

@router.put("/{key}")
async def update_config(
    key: str,
    update_request: Dict[str, Any],
    request: Request,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update specific configuration value"""
    try:
        config_service = ConfigService(db)
        audit_service = AuditService(db)
        
        value = update_request.get("value")
        change_reason = update_request.get("change_reason", "Updated via API")
        
        # Validate configuration
        validation = await config_service.validate_config(key, value)
        if not validation["valid"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid configuration value: {validation['error']}"
            )
        
        # Update configuration
        success = await config_service.set_config(
            key=key,
            value=value,
            description=change_reason,
            changed_by=admin_user.username
        )
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to update configuration"
            )
        
        # Log the change
        await audit_service.log_action(
            user_id=admin_user.id,
            action="config_update",
            resource_type="system_config",
            resource_id=key,
            status="success",
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            details={
                "key": key,
                "new_value": str(value)[:100],  # Truncate long values
                "change_reason": change_reason
            }
        )
        
        return {"message": "Configuration updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update configuration: {str(e)}"
        )

@router.post("/batch-update")
async def batch_update_configs(
    batch_request: ConfigBatchUpdateRequest,
    request: Request,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update multiple configurations in a batch"""
    try:
        config_service = ConfigService(db)
        audit_service = AuditService(db)
        
        results = []
        errors = []
        
        for config_update in batch_request.configs:
            try:
                # Validate configuration
                validation = await config_service.validate_config(
                    config_update.key, 
                    config_update.value
                )
                
                if not validation["valid"]:
                    errors.append({
                        "key": config_update.key,
                        "error": validation["error"]
                    })
                    continue
                
                # Update configuration
                success = await config_service.set_config(
                    key=config_update.key,
                    value=config_update.value,
                    description=config_update.change_reason,
                    changed_by=admin_user.username
                )
                
                if success:
                    results.append({
                        "key": config_update.key,
                        "status": "success"
                    })
                else:
                    errors.append({
                        "key": config_update.key,
                        "error": "Update failed"
                    })
                    
            except Exception as e:
                errors.append({
                    "key": config_update.key,
                    "error": str(e)
                })
        
        # Log batch update
        await audit_service.log_action(
            user_id=admin_user.id,
            action="config_batch_update",
            resource_type="system_config",
            status="success" if not errors else "partial",
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            details={
                "updated_count": len(results),
                "error_count": len(errors),
                "change_reason": batch_request.change_reason
            }
        )
        
        return {
            "message": "Batch update completed",
            "updated": results,
            "errors": errors
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Batch update failed: {str(e)}"
        )

@router.post("/validate")
async def validate_config(
    validation_request: Dict[str, Any],
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Validate configuration value"""
    try:
        config_service = ConfigService(db)
        
        key = validation_request.get("key")
        value = validation_request.get("value")
        
        if not key:
            raise HTTPException(status_code=400, detail="Configuration key required")
        
        validation = await config_service.validate_config(key, value)
        return validation
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Validation failed: {str(e)}"
        )

@router.post("/test")
async def test_config(
    test_request: Dict[str, Any],
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Test configuration value"""
    try:
        config_service = ConfigService(db)
        
        key = test_request.get("key")
        value = test_request.get("value")
        
        if not key:
            raise HTTPException(status_code=400, detail="Configuration key required")
        
        test_result = await config_service.test_config(key, value)
        return test_result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Configuration test failed: {str(e)}"
        )

@router.get("/export")
async def export_configs(
    format: str = "json",
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Export all configurations"""
    try:
        config_service = ConfigService(db)
        
        if format not in ["json", "yaml"]:
            raise HTTPException(status_code=400, detail="Format must be 'json' or 'yaml'")
        
        export_data = await config_service.export_configs(format)
        
        return {
            "format": format,
            "data": export_data,
            "exported_at": "2025-05-29T10:55:34Z"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Export failed: {str(e)}"
        )

@router.post("/import")
async def import_configs(
    import_request: Dict[str, Any],
    request: Request,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Import configurations from file data"""
    try:
        config_service = ConfigService(db)
        audit_service = AuditService(db)
        
        config_data = import_request.get("data")
        format_type = import_request.get("format", "json")
        
        if not config_data:
            raise HTTPException(status_code=400, detail="Configuration data required")
        
        import_result = await config_service.import_configs(
            config_data=config_data,
            format=format_type,
            changed_by=admin_user.username
        )
        
        # Log import
        await audit_service.log_action(
            user_id=admin_user.id,
            action="config_import",
            resource_type="system_config",
            status="success" if import_result["success"] else "error",
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            details=import_result
        )
        
        return import_result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Import failed: {str(e)}"
        )

@router.get("/history")
async def get_config_history(
    key: str = None,
    limit: int = 100,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get configuration change history"""
    try:
        config_service = ConfigService(db)
        history = await config_service.get_config_history(key)
        
        return {
            "history": history[:limit],
            "total_count": len(history)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get config history: {str(e)}"
        )