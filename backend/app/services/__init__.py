"""
Complete Services Package - Final Version
Created: 2025-05-29 14:38:00 UTC by Teeksss
"""

import logging
from typing import Dict, Any

from .auth import AuthService
from .sql_proxy import SQLProxyService
from .query_analyzer import QueryAnalyzer
from .cache import CacheService
from .health import HealthService
from .notification import NotificationService
from .rate_limiter import RateLimiterService
from .audit import AuditService

logger = logging.getLogger(__name__)

# Service instances
services = {
    'auth': None,
    'sql_proxy': None,
    'query_analyzer': None,
    'cache': None,
    'health': None,
    'notification': None,
    'rate_limiter': None,
    'audit': None
}


async def initialize_all_services() -> bool:
    """Initialize all services"""
    
    try:
        logger.info("🚀 Initializing all services...")
        
        # Initialize Cache Service first (others depend on it)
        logger.info("📦 Initializing Cache Service...")
        cache_service = CacheService()
        await cache_service.initialize()
        services['cache'] = cache_service
        
        # Initialize Rate Limiter Service
        logger.info("🚦 Initializing Rate Limiter Service...")
        rate_limiter_service = RateLimiterService()
        await rate_limiter_service.initialize()
        services['rate_limiter'] = rate_limiter_service
        
        # Initialize Audit Service
        logger.info("📋 Initializing Audit Service...")
        audit_service = AuditService()
        await audit_service.initialize()
        services['audit'] = audit_service
        
        # Initialize Auth Service
        logger.info("🔐 Initializing Auth Service...")
        auth_service = AuthService()
        await auth_service.initialize()
        services['auth'] = auth_service
        
        # Initialize Query Analyzer
        logger.info("🔍 Initializing Query Analyzer...")
        query_analyzer = QueryAnalyzer()
        await query_analyzer.initialize()
        services['query_analyzer'] = query_analyzer
        
        # Initialize SQL Proxy Service
        logger.info("🗄️ Initializing SQL Proxy Service...")
        sql_proxy_service = SQLProxyService()
        await sql_proxy_service.initialize()
        services['sql_proxy'] = sql_proxy_service
        
        # Initialize Notification Service
        logger.info("📧 Initializing Notification Service...")
        notification_service = NotificationService()
        await notification_service.initialize()
        services['notification'] = notification_service
        
        # Initialize Health Service last (monitors others)
        logger.info("💚 Initializing Health Service...")
        health_service = HealthService()
        await health_service.initialize()
        services['health'] = health_service
        
        logger.info("✅ All services initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Service initialization failed: {e}")
        return False


async def shutdown_all_services():
    """Shutdown all services gracefully"""
    
    try:
        logger.info("🔄 Shutting down all services...")
        
        # Shutdown in reverse order
        shutdown_order = [
            'health', 'notification', 'sql_proxy', 'query_analyzer',
            'auth', 'audit', 'rate_limiter', 'cache'
        ]
        
        for service_name in shutdown_order:
            service = services.get(service_name)
            if service:
                try:
                    logger.info(f"🔄 Shutting down {service_name} service...")
                    await service.cleanup()
                    services[service_name] = None
                except Exception as e:
                    logger.error(f"❌ Error shutting down {service_name} service: {e}")
        
        logger.info("✅ All services shut down successfully")
        
    except Exception as e:
        logger.error(f"❌ Service shutdown failed: {e}")


async def get_services_health() -> Dict[str, Any]:
    """Get health status of all services"""
    
    health_status = {}
    
    for service_name, service in services.items():
        if service:
            try:
                health_status[service_name] = await service.health_check()
            except Exception as e:
                health_status[service_name] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        else:
            health_status[service_name] = {
                "status": "not_initialized"
            }
    
    return health_status


async def get_services_metrics() -> Dict[str, Any]:
    """Get metrics from all services"""
    
    metrics = {}
    
    for service_name, service in services.items():
        if service and hasattr(service, 'get_metrics'):
            try:
                metrics[service_name] = await service.get_metrics()
            except Exception as e:
                metrics[service_name] = {
                    "error": str(e)
                }
    
    return metrics


def get_service(service_name: str):
    """Get service instance by name"""
    return services.get(service_name)


# Export service instances for convenience
def get_auth_service() -> AuthService:
    return services.get('auth')


def get_sql_proxy_service() -> SQLProxyService:
    return services.get('sql_proxy')


def get_cache_service() -> CacheService:
    return services.get('cache')


def get_health_service() -> HealthService:
    return services.get('health')


def get_notification_service() -> NotificationService:
    return services.get('notification')


def get_rate_limiter_service() -> RateLimiterService:
    return services.get('rate_limiter')


def get_audit_service() -> AuditService:
    return services.get('audit')


def get_query_analyzer() -> QueryAnalyzer:
    return services.get('query_analyzer')