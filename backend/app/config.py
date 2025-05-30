from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/sql_proxy"
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    
    # LDAP
    LDAP_SERVER: str = "ldap://localhost:389"
    LDAP_BIND_DN: str = "cn=admin,dc=example,dc=com"
    LDAP_BIND_PASSWORD: str = "admin_password"
    LDAP_USER_BASE_DN: str = "ou=users,dc=example,dc=com"
    LDAP_USER_SEARCH_FILTER: str = "(uid={username})"
    
    # JWT
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 3600  # 1 hour in seconds
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Target Database (for proxy queries)
    TARGET_DB_URL: str = "postgresql://target_user:target_password@localhost:5432/target_db"
    
    class Config:
        env_file = ".env"

settings = Settings()