"""
Complete Application Configuration - Final Version
Created: 2025-05-29 14:45:01 UTC by Teeksss
"""

import os
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseSettings, validator, PostgresDsn, RedisDsn
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings with validation"""
    
    # =============================================================================
    # APPLICATION SETTINGS
    # =============================================================================
    APP_NAME: str = "Enterprise SQL Proxy System"
    APP_VERSION: str = "2.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    RELOAD: bool = True
    WORKERS: int = 1
    CREATOR: str = "Teeksss"
    BUILD_DATE: str = "2025-05-29 14:45:01"
    
    # =============================================================================
    # SERVER SETTINGS
    # =============================================================================
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    SECRET_KEY: str = "your-super-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    SESSION_TIMEOUT_MINUTES: int = 480
    
    # =============================================================================
    # DATABASE SETTINGS
    # =============================================================================
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "enterprise_sql_proxy"
    DATABASE_URL: Optional[PostgresDsn] = None
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 30
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_RECYCLE: int = 3600
    
    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql",
            user=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_HOST"),
            port=str(values.get("POSTGRES_PORT")),
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )
    
    # =============================================================================
    # REDIS SETTINGS
    # =============================================================================
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0
    REDIS_URL: Optional[RedisDsn] = None
    REDIS_POOL_SIZE: int = 20
    REDIS_TIMEOUT: int = 30
    
    @validator("REDIS_URL", pre=True)
    def assemble_redis_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        password = values.get("REDIS_PASSWORD")
        auth_part = f":{password}@" if password else ""
        return f"redis://{auth_part}{values.get('REDIS_HOST')}:{values.get('REDIS_PORT')}/{values.get('REDIS_DB')}"
    
    # =============================================================================
    # CACHE SETTINGS
    # =============================================================================
    CACHE_ENABLED: bool = True
    CACHE_DEFAULT_TIMEOUT: int = 3600
    CACHE_KEY_PREFIX: str = "esp:"
    QUERY_CACHE_TTL: int = 1800
    
    # =============================================================================
    # SECURITY SETTINGS
    # =============================================================================
    SSL_ENABLED: bool = False
    ADVANCED_SECURITY: bool = True
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_NUMBERS: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    DEFAULT_RATE_LIMIT: int = 1000
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 15
    
    # CORS Settings
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1", "0.0.0.0"]
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # =============================================================================
    # QUERY SETTINGS
    # =============================================================================
    QUERY_TIMEOUT: int = 300
    MAX_RESULT_ROWS: int = 10000
    QUERY_APPROVAL_REQUIRED: bool = False
    QUERY_ANALYSIS_ENABLED: bool = True
    
    # =============================================================================
    # AUDIT & LOGGING SETTINGS
    # =============================================================================
    AUDIT_LOG_ENABLED: bool = True
    AUDIT_RETENTION_DAYS: int = 365
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "detailed"
    
    # =============================================================================
    # MONITORING SETTINGS
    # =============================================================================
    MONITORING_ENABLED: bool = True
    PROMETHEUS_ENABLED: bool = True
    HEALTH_CHECK_INTERVAL: int = 300
    
    # =============================================================================
    # EMAIL SETTINGS
    # =============================================================================
    EMAILS_ENABLED: bool = False
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_TLS: bool = True
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_ADDRESS: str = ""
    SMTP_FROM_NAME: str = "Enterprise SQL Proxy"
    
    # =============================================================================
    # NOTIFICATION SETTINGS
    # =============================================================================
    NOTIFICATIONS_ENABLED: bool = True
    SLACK_WEBHOOK_URL: str = ""
    TEAMS_WEBHOOK_URL: str = ""
    
    # =============================================================================
    # LDAP SETTINGS
    # =============================================================================
    LDAP_ENABLED: bool = False
    LDAP_SERVER: str = ""
    LDAP_PORT: int = 389
    LDAP_USE_SSL: bool = False
    LDAP_BASE_DN: str = ""
    LDAP_USER_DN: str = ""
    LDAP_PASSWORD: str = ""
    LDAP_USER_SEARCH_BASE: str = ""
    LDAP_GROUP_SEARCH_BASE: str = ""
    
    # =============================================================================
    # BACKUP SETTINGS
    # =============================================================================
    BACKUP_ENABLED: bool = False
    BACKUP_SCHEDULE: str = "0 2 * * *"
    BACKUP_RETENTION_DAYS: int = 30
    BACKUP_PATH: str = "/app/backups"
    
    # =============================================================================
    # EXTERNAL INTEGRATIONS
    # =============================================================================
    ANALYTICS_ENABLED: bool = False
    GOOGLE_ANALYTICS_ID: str = ""
    SENTRY_ENABLED: bool = False
    SENTRY_DSN: str = ""
    
    # =============================================================================
    # DEVELOPMENT SETTINGS
    # =============================================================================
    TESTING: bool = False
    TEST_DATABASE_URL: str = ""
    API_DOCS_ENABLED: bool = True
    OPENAPI_URL: str = "/openapi.json"
    DOCS_URL: str = "/docs"
    REDOC_URL: str = "/redoc"
    
    # =============================================================================
    # FEATURE FLAGS
    # =============================================================================
    FEATURE_USER_REGISTRATION: bool = False
    FEATURE_SOCIAL_LOGIN: bool = False
    FEATURE_TWO_FACTOR_AUTH: bool = False
    FEATURE_API_VERSIONING: bool = True
    FEATURE_REAL_TIME_NOTIFICATIONS: bool = True
    FEATURE_ADVANCED_ANALYTICS: bool = True
    FEATURE_QUERY_SHARING: bool = True
    FEATURE_SCHEDULED_QUERIES: bool = True
    FEATURE_DATA_EXPORT: bool = True
    FEATURE_CUSTOM_THEMES: bool = True
    
    # =============================================================================
    # PERFORMANCE SETTINGS
    # =============================================================================
    MAX_CONCURRENT_QUERIES: int = 100
    QUERY_MEMORY_LIMIT_MB: int = 512
    CONNECTION_POOL_SIZE: int = 20
    ASYNC_WORKER_COUNT: int = 4
    CACHE_SIZE_LIMIT_MB: int = 1024
    
    # =============================================================================
    # COMPLIANCE SETTINGS
    # =============================================================================
    GDPR_COMPLIANCE: bool = True
    SOX_COMPLIANCE: bool = False
    HIPAA_COMPLIANCE: bool = False
    DATA_RETENTION_DAYS: int = 2555  # 7 years
    ANONYMIZE_LOGS: bool = True
    
    # =============================================================================
    # VALIDATION METHODS
    # =============================================================================
    @validator("SECRET_KEY")
    def validate_secret_key(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v
    
    @validator("ENVIRONMENT")
    def validate_environment(cls, v: str) -> str:
        if v not in ["development", "staging", "production"]:
            raise ValueError("ENVIRONMENT must be one of: development, staging, production")
        return v
    
    @validator("LOG_LEVEL")
    def validate_log_level(cls, v: str) -> str:
        if v.upper() not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ValueError("LOG_LEVEL must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL")
        return v.upper()
    
    @validator("PASSWORD_MIN_LENGTH")
    def validate_password_min_length(cls, v: int) -> int:
        if v < 8:
            raise ValueError("PASSWORD_MIN_LENGTH must be at least 8")
        return v
    
    # =============================================================================
    # COMPUTED PROPERTIES
    # =============================================================================
    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"
    
    @property
    def is_staging(self) -> bool:
        return self.ENVIRONMENT == "staging"
    
    @property
    def app_info(self) -> Dict[str, str]:
        return {
            "name": self.APP_NAME,
            "version": self.APP_VERSION,
            "environment": self.ENVIRONMENT,
            "creator": self.CREATOR,
            "build_date": self.BUILD_DATE,
        }
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Global settings instance
settings = get_settings()

# Environment-specific configurations
if settings.is_production:
    # Production overrides
    settings.DEBUG = False
    settings.RELOAD = False
    settings.API_DOCS_ENABLED = False
    settings.WORKERS = max(4, os.cpu_count() or 4)
elif settings.is_staging:
    # Staging overrides
    settings.DEBUG = False
    settings.RELOAD = False
    settings.WORKERS = 2
else:
    # Development overrides
    settings.DEBUG = True
    settings.RELOAD = True
    settings.WORKERS = 1

# Export settings
__all__ = ["settings", "get_settings", "Settings"]