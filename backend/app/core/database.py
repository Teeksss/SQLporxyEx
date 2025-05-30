"""
Complete Database Configuration - Final Version
Created: 2025-05-29 13:54:25 UTC by Teeksss
"""

import logging
from typing import Generator, Optional
from sqlalchemy import create_engine, event, pool
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
import time

from app.core.config import settings

logger = logging.getLogger(__name__)

# Create SQLAlchemy engine with connection pooling
engine = create_engine(
    str(settings.DATABASE_URL),
    poolclass=QueuePool,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_POOL_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_pre_ping=True,
    echo=settings.DB_ECHO,
    echo_pool=settings.DEBUG,
    future=True,
    connect_args={
        "connect_timeout": 30,
        "command_timeout": 60,
        "application_name": "Enterprise SQL Proxy",
    } if "postgresql" in str(settings.DATABASE_URL) else {}
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False
)

# Create declarative base
Base = declarative_base()


# Database events for monitoring
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Set SQLite pragmas for better performance"""
    if "sqlite" in str(settings.DATABASE_URL):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=1000")
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.close()


@event.listens_for(engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Log slow queries"""
    conn.info.setdefault('query_start_time', []).append(time.time())
    if settings.DEBUG:
        logger.debug(f"Executing query: {statement[:200]}...")


@event.listens_for(engine, "after_cursor_execute")
def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Log query execution time"""
    total = time.time() - conn.info['query_start_time'].pop(-1)
    if total > 1.0:  # Log slow queries (> 1 second)
        logger.warning(f"Slow query detected: {total:.2f}s - {statement[:200]}...")
    elif settings.DEBUG:
        logger.debug(f"Query executed in {total:.3f}s")


# Database dependency
def get_db() -> Generator[Session, None, None]:
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


# Context manager for database sessions
@contextmanager
def get_db_session():
    """Context manager for database sessions"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        logger.error(f"Database transaction error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


# Database health check
def check_database_health() -> bool:
    """Check database connectivity"""
    try:
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            return result.fetchone() is not None
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


# Create all tables
def create_all_tables():
    """Create all database tables"""
    try:
        # Import all models to ensure they're registered
        from app.models import user, sql_server, query, notification
        
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise


# Drop all tables (for testing)
def drop_all_tables():
    """Drop all database tables"""
    try:
        logger.warning("Dropping all database tables...")
        Base.metadata.drop_all(bind=engine)
        logger.info("Database tables dropped successfully")
        
    except Exception as e:
        logger.error(f"Failed to drop database tables: {e}")
        raise


# Database migration utilities
def get_database_version() -> Optional[str]:
    """Get current database schema version"""
    try:
        with engine.connect() as conn:
            result = conn.execute(
                "SELECT version_num FROM alembic_version ORDER BY version_num DESC LIMIT 1"
            )
            row = result.fetchone()
            return row[0] if row else None
    except Exception:
        return None


def get_connection_info() -> dict:
    """Get database connection information"""
    try:
        with engine.connect() as conn:
            # Get database-specific information
            if "postgresql" in str(settings.DATABASE_URL):
                result = conn.execute("SELECT version()")
                version = result.fetchone()[0]
                
                result = conn.execute("SELECT current_database()")
                database = result.fetchone()[0]
                
                result = conn.execute("SELECT current_user")
                user = result.fetchone()[0]
                
                # Get connection count
                result = conn.execute(
                    "SELECT count(*) FROM pg_stat_activity WHERE state = 'active'"
                )
                active_connections = result.fetchone()[0]
                
                return {
                    "type": "PostgreSQL",
                    "version": version,
                    "database": database,
                    "user": user,
                    "active_connections": active_connections,
                    "pool_size": engine.pool.size(),
                    "checked_out": engine.pool.checkedout(),
                    "overflow": engine.pool.overflow(),
                }
                
            elif "sqlite" in str(settings.DATABASE_URL):
                result = conn.execute("SELECT sqlite_version()")
                version = result.fetchone()[0]
                
                return {
                    "type": "SQLite",
                    "version": version,
                    "database": str(settings.DATABASE_URL),
                    "pool_size": engine.pool.size() if hasattr(engine.pool, 'size') else 1,
                }
                
    except Exception as e:
        logger.error(f"Failed to get connection info: {e}")
        return {"error": str(e)}


# Connection pool monitoring
def get_pool_status() -> dict:
    """Get connection pool status"""
    try:
        pool = engine.pool
        return {
            "size": pool.size(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "checked_in": pool.checkedin(),
        }
    except Exception as e:
        logger.error(f"Failed to get pool status: {e}")
        return {"error": str(e)}


# Database maintenance utilities
def vacuum_database():
    """Vacuum the database (PostgreSQL/SQLite)"""
    try:
        with engine.connect() as conn:
            if "postgresql" in str(settings.DATABASE_URL):
                conn.execute("VACUUM ANALYZE")
                logger.info("PostgreSQL VACUUM ANALYZE completed")
            elif "sqlite" in str(settings.DATABASE_URL):
                conn.execute("VACUUM")
                logger.info("SQLite VACUUM completed")
    except Exception as e:
        logger.error(f"Failed to vacuum database: {e}")
        raise


def analyze_database():
    """Update database statistics"""
    try:
        with engine.connect() as conn:
            if "postgresql" in str(settings.DATABASE_URL):
                conn.execute("ANALYZE")
                logger.info("PostgreSQL ANALYZE completed")
            elif "sqlite" in str(settings.DATABASE_URL):
                conn.execute("ANALYZE")
                logger.info("SQLite ANALYZE completed")
    except Exception as e:
        logger.error(f"Failed to analyze database: {e}")
        raise


# Database backup utilities
def create_backup_connection():
    """Create a separate connection for backup operations"""
    backup_engine = create_engine(
        str(settings.DATABASE_URL),
        poolclass=pool.NullPool,  # No connection pooling for backup
        echo=False
    )
    return backup_engine


# Transaction utilities
class DatabaseTransaction:
    """Database transaction context manager with savepoints"""
    
    def __init__(self, db: Session):
        self.db = db
        self.savepoint = None
    
    def __enter__(self):
        self.savepoint = self.db.begin()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.savepoint.rollback()
            logger.error(f"Transaction rolled back due to: {exc_val}")
        else:
            self.savepoint.commit()
        return False


# Query execution utilities
def execute_raw_sql(query: str, params: dict = None) -> list:
    """Execute raw SQL query safely"""
    try:
        with engine.connect() as conn:
            result = conn.execute(query, params or {})
            return result.fetchall()
    except Exception as e:
        logger.error(f"Failed to execute raw SQL: {e}")
        raise


# Database initialization for testing
def init_test_database():
    """Initialize database for testing"""
    if settings.TESTING:
        # Use in-memory SQLite for testing
        global engine, SessionLocal
        engine = create_engine(
            "sqlite:///:memory:",
            echo=False,
            poolclass=pool.StaticPool,
            connect_args={
                "check_same_thread": False,
            },
        )
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        create_all_tables()
        logger.info("Test database initialized")


# Database cleanup for testing
def cleanup_test_database():
    """Cleanup test database"""
    if settings.TESTING:
        drop_all_tables()
        engine.dispose()
        logger.info("Test database cleaned up")


# Export all database utilities
__all__ = [
    "engine",
    "SessionLocal", 
    "Base",
    "get_db",
    "get_db_session",
    "create_all_tables",
    "drop_all_tables",
    "check_database_health",
    "get_database_version",
    "get_connection_info",
    "get_pool_status",
    "vacuum_database",
    "analyze_database",
    "create_backup_connection",
    "DatabaseTransaction",
    "execute_raw_sql",
    "init_test_database",
    "cleanup_test_database"
]