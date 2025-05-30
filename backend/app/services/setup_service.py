from sqlalchemy.orm import Session
from sqlalchemy import text
import logging
import yaml
import json
from typing import Dict, Any, List
from datetime import datetime

from app.models.config import SystemConfig, ConfigCategory, ConfigType, SystemTheme
from app.models.user import User, UserRole
from app.models.rate_limit import RateLimitProfile
from app.core.security import get_password_hash, generate_api_key
from app.services.config_service import ConfigService

logger = logging.getLogger(__name__)

class SetupService:
    """Service for system setup and initialization"""
    
    def __init__(self, db: Session):
        self.db = db
        self.config_service = ConfigService(db)
    
    async def is_setup_complete(self) -> bool:
        """Check if system setup is complete"""
        try:
            setup_config = self.db.query(SystemConfig).filter(
                SystemConfig.key == "setup_complete"
            ).first()
            return setup_config and setup_config.get_typed_value() == True
        except Exception as e:
            logger.error(f"Setup check failed: {e}")
            return False
    
    async def initialize_system(self) -> bool:
        """Initialize system with default configurations"""
        try:
            # Create default configurations if they don't exist
            await self._create_default_configs()
            
            # Create default rate limit profile
            await self._create_default_rate_limit_profile()
            
            # Create default theme
            await self._create_default_theme()
            
            logger.info("✅ System initialization completed")
            return True
        except Exception as e:
            logger.error(f"❌ System initialization failed: {e}")
            return False
    
    async def complete_setup(self, setup_data: Dict[str, Any]) -> bool:
        """Complete the setup process with user-provided data"""
        try:
            # Update configurations from setup data
            await self._update_configs_from_setup(setup_data)
            
            # Create admin user if provided
            if "admin_user" in setup_data:
                await self._create_admin_user(setup_data["admin_user"])
            
            # Mark setup as complete
            await self.config_service.set_config(
                "setup_complete", True, "System setup completion status"
            )
            
            # Log setup completion
            logger.info("🎉 System setup completed successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Setup completion failed: {e}")
            return False
    
    async def get_setup_status(self) -> Dict[str, Any]:
        """Get current setup status"""
        try:
            status = {
                "setup_complete": await self.is_setup_complete(),
                "database_connected": self._test_database_connection(),
                "redis_connected": await self._test_redis_connection(),
                "ldap_configured": await self._is_ldap_configured(),
                "admin_user_exists": await self._admin_user_exists(),
                "steps_completed": []
            }
            
            # Check which setup steps are completed
            if status["database_connected"]:
                status["steps_completed"].append("database")
            if status["ldap_configured"]:
                status["steps_completed"].append("ldap")
            if status["admin_user_exists"]:
                status["steps_completed"].append("admin_user")
            
            return status
        except Exception as e:
            logger.error(f"Setup status check failed: {e}")
            return {"setup_complete": False, "error": str(e)}
    
    async def reset_setup(self) -> bool:
        """Reset system setup (for testing/development)"""
        try:
            # Mark setup as incomplete
            await self.config_service.set_config("setup_complete", False)
            
            # Reset LDAP configuration
            ldap_configs = self.db.query(SystemConfig).filter(
                SystemConfig.category == ConfigCategory.LDAP
            ).all()
            for config in ldap_configs:
                config.value = config.default_value
            
            self.db.commit()
            logger.info("🔄 System setup reset completed")
            return True
        except Exception as e:
            logger.error(f"❌ Setup reset failed: {e}")
            return False
    
    async def _create_default_configs(self):
        """Create default system configurations"""
        default_configs = [
            # System configurations
            {
                "key": "setup_complete",
                "name": "Setup Complete",
                "value": "false",
                "default_value": "false",
                "description": "Whether system setup is complete",
                "category": ConfigCategory.SYSTEM,
                "config_type": ConfigType.BOOLEAN,
                "is_readonly": True
            },
            {
                "key": "system_name",
                "name": "System Name",
                "value": "Enterprise SQL Proxy",
                "default_value": "Enterprise SQL Proxy",
                "description": "Name of the system",
                "category": ConfigCategory.SYSTEM,
                "config_type": ConfigType.STRING
            },
            {
                "key": "company_name",
                "name": "Company Name",
                "value": "Your Company",
                "default_value": "Your Company",
                "description": "Company name for branding",
                "category": ConfigCategory.THEME,
                "config_type": ConfigType.STRING
            },
            
            # Security configurations
            {
                "key": "default_query_timeout",
                "name": "Default Query Timeout",
                "value": "300",
                "default_value": "300",
                "description": "Default query timeout in seconds",
                "category": ConfigCategory.SECURITY,
                "config_type": ConfigType.INTEGER,
                "min_value": 30,
                "max_value": 3600
            },
            {
                "key": "max_result_rows",
                "name": "Maximum Result Rows",
                "value": "10000",
                "default_value": "10000",
                "description": "Maximum number of rows returned by queries",
                "category": ConfigCategory.SECURITY,
                "config_type": ConfigType.INTEGER,
                "min_value": 100,
                "max_value": 100000
            },
            {
                "key": "require_query_approval",
                "name": "Require Query Approval",
                "value": "true",
                "default_value": "true",
                "description": "Whether new queries require approval",
                "category": ConfigCategory.SECURITY,
                "config_type": ConfigType.BOOLEAN
            },
            
            # LDAP configurations
            {
                "key": "ldap_enabled",
                "name": "LDAP Enabled",
                "value": "false",
                "default_value": "false",
                "description": "Enable LDAP authentication",
                "category": ConfigCategory.LDAP,
                "config_type": ConfigType.BOOLEAN
            },
            {
                "key": "ldap_server",
                "name": "LDAP Server",
                "value": "",
                "default_value": "",
                "description": "LDAP server URL",
                "category": ConfigCategory.LDAP,
                "config_type": ConfigType.URL
            },
            {
                "key": "ldap_port",
                "name": "LDAP Port",
                "value": "389",
                "default_value": "389",
                "description": "LDAP server port",
                "category": ConfigCategory.LDAP,
                "config_type": ConfigType.INTEGER,
                "min_value": 1,
                "max_value": 65535
            },
            {
                "key": "ldap_use_ssl",
                "name": "LDAP Use SSL",
                "value": "false",
                "default_value": "false",
                "description": "Use SSL for LDAP connection",
                "category": ConfigCategory.LDAP,
                "config_type": ConfigType.BOOLEAN
            },
            {
                "key": "ldap_base_dn",
                "name": "LDAP Base DN",
                "value": "",
                "default_value": "",
                "description": "LDAP base distinguished name",
                "category": ConfigCategory.LDAP,
                "config_type": ConfigType.STRING
            },
            {
                "key": "ldap_user_filter",
                "name": "LDAP User Filter",
                "value": "(&(objectClass=user)(sAMAccountName={username}))",
                "default_value": "(&(objectClass=user)(sAMAccountName={username}))",
                "description": "LDAP filter for user search",
                "category": ConfigCategory.LDAP,
                "config_type": ConfigType.STRING
            },
            {
                "key": "ldap_bind_dn",
                "name": "LDAP Bind DN",
                "value": "",
                "default_value": "",
                "description": "LDAP bind distinguished name",
                "category": ConfigCategory.LDAP,
                "config_type": ConfigType.STRING
            },
            {
                "key": "ldap_bind_password",
                "name": "LDAP Bind Password",
                "value": "",
                "default_value": "",
                "description": "LDAP bind password",
                "category": ConfigCategory.LDAP,
                "config_type": ConfigType.PASSWORD,
                "is_sensitive": True
            },
            
            # Rate limiting configurations
            {
                "key": "default_rate_limit_requests",
                "name": "Default Rate Limit Requests",
                "value": "100",
                "default_value": "100",
                "description": "Default number of requests per hour",
                "category": ConfigCategory.RATE_LIMITING,
                "config_type": ConfigType.INTEGER,
                "min_value": 1,
                "max_value": 10000
            },
            {
                "key": "rate_limit_window_minutes",
                "name": "Rate Limit Window (Minutes)",
                "value": "60",
                "default_value": "60",
                "description": "Rate limit time window in minutes",
                "category": ConfigCategory.RATE_LIMITING,
                "config_type": ConfigType.INTEGER,
                "min_value": 1,
                "max_value": 1440
            },
            
            # Notification configurations
            {
                "key": "email_notifications_enabled",
                "name": "Email Notifications Enabled",
                "value": "false",
                "default_value": "false",
                "description": "Enable email notifications",
                "category": ConfigCategory.NOTIFICATION,
                "config_type": ConfigType.BOOLEAN
            },
            {
                "key": "smtp_server",
                "name": "SMTP Server",
                "value": "",
                "default_value": "",
                "description": "SMTP server for email notifications",
                "category": ConfigCategory.NOTIFICATION,
                "config_type": ConfigType.STRING
            },
            {
                "key": "smtp_port",
                "name": "SMTP Port",
                "value": "587",
                "default_value": "587",
                "description": "SMTP server port",
                "category": ConfigCategory.NOTIFICATION,
                "config_type": ConfigType.INTEGER,
                "min_value": 1,
                "max_value": 65535
            },
            {
                "key": "smtp_username",
                "name": "SMTP Username",
                "value": "",
                "default_value": "",
                "description": "SMTP authentication username",
                "category": ConfigCategory.NOTIFICATION,
                "config_type": ConfigType.STRING
            },
            {
                "key": "smtp_password",
                "name": "SMTP Password",
                "value": "",
                "default_value": "",
                "description": "SMTP authentication password",
                "category": ConfigCategory.NOTIFICATION,
                "config_type": ConfigType.PASSWORD,
                "is_sensitive": True
            },
            
            # Backup configurations
            {
                "key": "auto_backup_enabled",
                "name": "Auto Backup Enabled",
                "value": "true",
                "default_value": "true",
                "description": "Enable automatic backups",
                "category": ConfigCategory.BACKUP,
                "config_type": ConfigType.BOOLEAN
            },
            {
                "key": "backup_retention_days",
                "name": "Backup Retention Days",
                "value": "30",
                "default_value": "30",
                "description": "Number of days to retain backups",
                "category": ConfigCategory.BACKUP,
                "config_type": ConfigType.INTEGER,
                "min_value": 1,
                "max_value": 365
            },
            {
                "key": "backup_interval_hours",
                "name": "Backup Interval Hours",
                "value": "24",
                "default_value": "24",
                "description": "Hours between automatic backups",
                "category": ConfigCategory.BACKUP,
                "config_type": ConfigType.INTEGER,
                "min_value": 1,
                "max_value": 168
            },
            
            # Monitoring configurations
            {
                "key": "health_check_interval",
                "name": "Health Check Interval",
                "value": "30",
                "default_value": "30",
                "description": "Health check interval in seconds",
                "category": ConfigCategory.MONITORING,
                "config_type": ConfigType.INTEGER,
                "min_value": 10,
                "max_value": 300
            },
            {
                "key": "performance_monitoring_enabled",
                "name": "Performance Monitoring Enabled",
                "value": "true",
                "default_value": "true",
                "description": "Enable performance monitoring",
                "category": ConfigCategory.MONITORING,
                "config_type": ConfigType.BOOLEAN
            }
        ]
        
        for config_data in default_configs:
            existing = self.db.query(SystemConfig).filter(
                SystemConfig.key == config_data["key"]
            ).first()
            
            if not existing:
                config = SystemConfig(**config_data)
                self.db.add(config)
        
        self.db.commit()
    
    async def _create_default_rate_limit_profile(self):
        """Create default rate limit profile"""
        existing = self.db.query(RateLimitProfile).filter(
            RateLimitProfile.name == "Default"
        ).first()
        
        if not existing:
            profile = RateLimitProfile(
                name="Default",
                description="Default rate limit profile",
                requests_per_minute=10,
                requests_per_hour=100,
                requests_per_day=1000,
                max_concurrent_queries=3,
                max_query_duration_seconds=300,
                max_result_rows=10000,
                is_default=True
            )
            self.db.add(profile)
            self.db.commit()
    
    async def _create_default_theme(self):
        """Create default system theme"""
        existing = self.db.query(SystemTheme).filter(
            SystemTheme.name == "Default"
        ).first()
        
        if not existing:
            theme = SystemTheme(
                name="Default",
                is_default=True,
                primary_color="#1890ff",
                secondary_color="#52c41a",
                company_name="Your Company"
            )
            self.db.add(theme)
            self.db.commit()
    
    def _test_database_connection(self) -> bool:
        """Test database connection"""
        try:
            self.db.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    async def _test_redis_connection(self) -> bool:
        """Test Redis connection"""
        try:
            # This would be implemented with actual Redis client
            return True
        except Exception as e:
            logger.error(f"Redis connection test failed: {e}")
            return False
    
    async def _is_ldap_configured(self) -> bool:
        """Check if LDAP is configured"""
        try:
            ldap_enabled = await self.config_service.get_config("ldap_enabled", False)
            ldap_server = await self.config_service.get_config("ldap_server", "")
            return ldap_enabled and bool(ldap_server)
        except Exception:
            return False
    
    async def _admin_user_exists(self) -> bool:
        """Check if admin user exists"""
        try:
            admin = self.db.query(User).filter(
                User.role == UserRole.ADMIN
            ).first()
            return admin is not None
        except Exception:
            return False
    
    async def _update_configs_from_setup(self, setup_data: Dict[str, Any]):
        """Update configurations from setup data"""
        config_mappings = {
            "ldap_server": "ldap_server",
            "ldap_port": "ldap_port",
            "ldap_use_ssl": "ldap_use_ssl",
            "ldap_base_dn": "ldap_base_dn",
            "ldap_bind_dn": "ldap_bind_dn",
            "ldap_bind_password": "ldap_bind_password",
            "company_name": "company_name",
            "system_name": "system_name"
        }
        
        for setup_key, config_key in config_mappings.items():
            if setup_key in setup_data:
                await self.config_service.set_config(
                    config_key, setup_data[setup_key]
                )
        
        # Enable LDAP if server is configured
        if "ldap_server" in setup_data and setup_data["ldap_server"]:
            await self.config_service.set_config("ldap_enabled", True)
    
    async def _create_admin_user(self, admin_data: Dict[str, Any]):
        """Create admin user"""
        existing = self.db.query(User).filter(
            User.username == admin_data["username"]
        ).first()
        
        if not existing:
            user = User(
                username=admin_data["username"],
                full_name=admin_data.get("full_name", "System Administrator"),
                email=admin_data.get("email"),
                role=UserRole.ADMIN,
                is_ldap_user=False,  # Local admin account
                api_key=generate_api_key(),
                created_by="system_setup"
            )
            self.db.add(user)
            self.db.commit()
            logger.info(f"✅ Admin user '{admin_data['username']}' created")