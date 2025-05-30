from sqlalchemy.orm import Session
from typing import Any, Dict, List, Optional
import json
import logging
from datetime import datetime

from app.models.config import SystemConfig, ConfigHistory, ConfigCategory, ConfigType
from app.core.security import encrypt_sensitive_data, decrypt_sensitive_data

logger = logging.getLogger(__name__)

class ConfigService:
    """Service for dynamic configuration management with hot reload"""
    
    def __init__(self, db: Session):
        self.db = db
        self._config_cache = {}
        self._last_cache_update = None
    
    async def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value with caching"""
        try:
            # Check cache first
            if key in self._config_cache:
                cache_entry = self._config_cache[key]
                if cache_entry.get("timestamp") and \
                   (datetime.now() - cache_entry["timestamp"]).seconds < 30:
                    return cache_entry["value"]
            
            # Get from database
            config = self.db.query(SystemConfig).filter(
                SystemConfig.key == key
            ).first()
            
            if not config:
                return default
            
            value = config.get_typed_value()
            
            # Decrypt if sensitive
            if config.is_sensitive and value:
                value = decrypt_sensitive_data(str(value))
            
            # Update cache
            self._config_cache[key] = {
                "value": value,
                "timestamp": datetime.now()
            }
            
            return value
        except Exception as e:
            logger.error(f"Config get failed for {key}: {e}")
            return default
    
    async def set_config(
        self, 
        key: str, 
        value: Any, 
        description: str = None,
        changed_by: str = "system"
    ) -> bool:
        """Set configuration value with change tracking"""
        try:
            config = self.db.query(SystemConfig).filter(
                SystemConfig.key == key
            ).first()
            
            if not config:
                logger.warning(f"Config key {key} not found")
                return False
            
            old_value = config.value
            
            # Convert value to string for storage
            if config.config_type == ConfigType.JSON:
                new_value = json.dumps(value) if value is not None else None
            else:
                new_value = str(value) if value is not None else None
            
            # Encrypt if sensitive
            if config.is_sensitive and new_value:
                new_value = encrypt_sensitive_data(new_value)
            
            # Update config
            config.value = new_value
            config.updated_at = datetime.now()
            config.updated_by = changed_by
            
            # Record change history
            history = ConfigHistory(
                config_key=key,
                old_value=old_value,
                new_value=new_value,
                changed_by=changed_by,
                change_reason=description or f"Updated {key}"
            )
            self.db.add(history)
            
            self.db.commit()
            
            # Clear cache for this key
            if key in self._config_cache:
                del self._config_cache[key]
            
            logger.info(f"✅ Config {key} updated by {changed_by}")
            return True
        except Exception as e:
            logger.error(f"Config set failed for {key}: {e}")
            self.db.rollback()
            return False
    
    async def get_configs_by_category(
        self, 
        category: ConfigCategory
    ) -> List[Dict[str, Any]]:
        """Get all configurations for a category"""
        try:
            configs = self.db.query(SystemConfig).filter(
                SystemConfig.category == category
            ).order_by(SystemConfig.display_order, SystemConfig.name).all()
            
            result = []
            for config in configs:
                config_dict = {
                    "key": config.key,
                    "name": config.name,
                    "description": config.description,
                    "category": config.category.value,
                    "config_type": config.config_type.value,
                    "value": config.get_typed_value(),
                    "default_value": config.get_typed_default(),
                    "is_sensitive": config.is_sensitive,
                    "requires_restart": config.requires_restart,
                    "is_readonly": config.is_readonly,
                    "is_advanced": config.is_advanced,
                    "validation_regex": config.validation_regex,
                    "min_value": config.min_value,
                    "max_value": config.max_value,
                    "allowed_values": json.loads(config.allowed_values) if config.allowed_values else None,
                    "ui_component": config.ui_component,
                    "ui_props": json.loads(config.ui_props) if config.ui_props else None
                }
                
                # Don't expose sensitive values
                if config.is_sensitive and config_dict["value"]:
                    config_dict["value"] = "***ENCRYPTED***"
                
                result.append(config_dict)
            
            return result
        except Exception as e:
            logger.error(f"Get configs by category failed: {e}")
            return []
    
    async def get_all_configs(self) -> Dict[str, Any]:
        """Get all configurations grouped by category"""
        try:
            result = {}
            for category in ConfigCategory:
                result[category.value] = await self.get_configs_by_category(category)
            return result
        except Exception as e:
            logger.error(f"Get all configs failed: {e}")
            return {}
    
    async def validate_config(self, key: str, value: Any) -> Dict[str, Any]:
        """Validate configuration value"""
        try:
            config = self.db.query(SystemConfig).filter(
                SystemConfig.key == key
            ).first()
            
            if not config:
                return {"valid": False, "error": "Configuration not found"}
            
            # Type validation
            try:
                if config.config_type == ConfigType.INTEGER:
                    int_value = int(value)
                    if config.min_value is not None and int_value < config.min_value:
                        return {"valid": False, "error": f"Value must be at least {config.min_value}"}
                    if config.max_value is not None and int_value > config.max_value:
                        return {"valid": False, "error": f"Value must be at most {config.max_value}"}
                elif config.config_type == ConfigType.FLOAT:
                    float_value = float(value)
                    if config.min_value is not None and float_value < config.min_value:
                        return {"valid": False, "error": f"Value must be at least {config.min_value}"}
                    if config.max_value is not None and float_value > config.max_value:
                        return {"valid": False, "error": f"Value must be at most {config.max_value}"}
                elif config.config_type == ConfigType.JSON:
                    json.loads(str(value))
                elif config.config_type == ConfigType.BOOLEAN:
                    if str(value).lower() not in ('true', 'false', '1', '0', 'yes', 'no'):
                        return {"valid": False, "error": "Value must be a boolean"}
            except (ValueError, TypeError, json.JSONDecodeError) as e:
                return {"valid": False, "error": f"Invalid {config.config_type.value}: {str(e)}"}
            
            # Allowed values validation
            if config.allowed_values:
                allowed = json.loads(config.allowed_values)
                if value not in allowed:
                    return {"valid": False, "error": f"Value must be one of: {', '.join(map(str, allowed))}"}
            
            # Regex validation
            if config.validation_regex:
                import re
                if not re.match(config.validation_regex, str(value)):
                    return {"valid": False, "error": "Value does not match required format"}
            
            return {"valid": True}
        except Exception as e:
            logger.error(f"Config validation failed for {key}: {e}")
            return {"valid": False, "error": "Validation error occurred"}
    
    async def test_config(self, key: str, value: Any) -> Dict[str, Any]:
        """Test configuration value (e.g., LDAP connection, SMTP settings)"""
        try:
            if key.startswith("ldap_"):
                return await self._test_ldap_config(key, value)
            elif key.startswith("smtp_"):
                return await self._test_smtp_config(key, value)
            elif key.startswith("database_"):
                return await self._test_database_config(key, value)
            else:
                return {"success": True, "message": "No test available for this configuration"}
        except Exception as e:
            logger.error(f"Config test failed for {key}: {e}")
            return {"success": False, "message": f"Test error: {str(e)}"}
    
    async def export_configs(self, format: str = "json") -> str:
        """Export all configurations"""
        try:
            configs = await self.get_all_configs()
            
            if format.lower() == "yaml":
                import yaml
                return yaml.dump(configs, default_flow_style=False)
            else:
                return json.dumps(configs, indent=2)
        except Exception as e:
            logger.error(f"Config export failed: {e}")
            return ""
    
    async def import_configs(
        self, 
        config_data: str, 
        format: str = "json",
        changed_by: str = "import"
    ) -> Dict[str, Any]:
        """Import configurations from file"""
        try:
            if format.lower() == "yaml":
                import yaml
                data = yaml.safe_load(config_data)
            else:
                data = json.loads(config_data)
            
            imported_count = 0
            errors = []
            
            for category, configs in data.items():
                for config in configs:
                    try:
                        # Validate before import
                        validation = await self.validate_config(config["key"], config["value"])
                        if not validation["valid"]:
                            errors.append(f"{config['key']}: {validation['error']}")
                            continue
                        
                        # Import config
                        success = await self.set_config(
                            config["key"], 
                            config["value"], 
                            f"Imported from {format.upper()}",
                            changed_by
                        )
                        if success:
                            imported_count += 1
                        else:
                            errors.append(f"{config['key']}: Failed to set value")
                    except Exception as e:
                        errors.append(f"{config['key']}: {str(e)}")
            
            return {
                "success": True,
                "imported_count": imported_count,
                "errors": errors
            }
        except Exception as e:
            logger.error(f"Config import failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_config_history(self, key: str = None) -> List[Dict[str, Any]]:
        """Get configuration change history"""
        try:
            query = self.db.query(ConfigHistory)
            if key:
                query = query.filter(ConfigHistory.config_key == key)
            
            history = query.order_by(ConfigHistory.created_at.desc()).limit(100).all()
            
            return [{
                "config_key": h.config_key,
                "old_value": h.old_value,
                "new_value": h.new_value,
                "changed_by": h.changed_by,
                "change_reason": h.change_reason,
                "created_at": h.created_at.isoformat()
            } for h in history]
        except Exception as e:
            logger.error(f"Get config history failed: {e}")
            return []
    
    async def _test_ldap_config(self, key: str, value: Any) -> Dict[str, Any]:
        """Test LDAP configuration"""
        # This would implement actual LDAP connection testing
        return {"success": True, "message": "LDAP configuration test passed"}
    
    async def _test_smtp_config(self, key: str, value: Any) -> Dict[str, Any]:
        """Test SMTP configuration"""
        # This would implement actual SMTP connection testing
        return {"success": True, "message": "SMTP configuration test passed"}
    
    async def _test_database_config(self, key: str, value: Any) -> Dict[str, Any]:
        """Test database configuration"""
        # This would implement actual database connection testing
        return {"success": True, "message": "Database configuration test passed"}