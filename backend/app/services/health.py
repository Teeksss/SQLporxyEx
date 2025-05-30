"""
Complete Health Service - Final Version
Created: 2025-05-29 14:45:01 UTC by Teeksss
"""

import logging
import asyncio
import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.database import get_db_session, engine
from app.services.cache import cache_service
from app.services.notification import notification_service

logger = logging.getLogger(__name__)


class HealthService:
    """Complete System Health Monitoring Service"""
    
    def __init__(self):
        self.startup_time = datetime.utcnow()
        self.health_history = []
        self.alert_thresholds = self._load_alert_thresholds()
        self.last_health_check = None
        self.health_status = "unknown"
        
    async def initialize(self):
        """Initialize health service"""
        try:
            # Start health monitoring
            if settings.MONITORING_ENABLED:
                asyncio.create_task(self._periodic_health_check())
            
            logger.info("✅ Health Service initialized")
            
        except Exception as e:
            logger.error(f"❌ Health Service initialization failed: {e}")
            raise
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health status"""
        
        try:
            start_time = time.time()
            
            # Collect all health metrics
            health_data = {
                "overall_status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "uptime_seconds": (datetime.utcnow() - self.startup_time).total_seconds(),
                "version": settings.APP_VERSION,
                "environment": settings.ENVIRONMENT,
                "creator": settings.CREATOR,
                "build_date": settings.BUILD_DATE,
                "components": {},
                "system": {},
                "performance": {},
                "alerts": []
            }
            
            # Database health
            db_health = await self._check_database_health()
            health_data["components"]["database"] = db_health
            
            # Cache health
            cache_health = await self._check_cache_health()
            health_data["components"]["cache"] = cache_health
            
            # System resources
            system_health = await self._check_system_resources()
            health_data["system"] = system_health
            
            # Application health
            app_health = await self._check_application_health()
            health_data["components"]["application"] = app_health
            
            # External services health
            external_health = await self._check_external_services()
            health_data["components"]["external"] = external_health
            
            # Performance metrics
            performance_metrics = await self._get_performance_metrics()
            health_data["performance"] = performance_metrics
            
            # Determine overall status
            health_data["overall_status"] = self._calculate_overall_status(health_data["components"])
            
            # Check for alerts
            alerts = self._check_health_alerts(health_data)
            health_data["alerts"] = alerts
            
            # Calculate response time
            health_data["response_time_ms"] = int((time.time() - start_time) * 1000)
            
            # Update health status
            self.health_status = health_data["overall_status"]
            self.last_health_check = datetime.utcnow()
            
            # Store in history
            self._store_health_history(health_data)
            
            return health_data
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "overall_status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _check_database_health(self) -> Dict[str, Any]:
        """Check database connectivity and performance"""
        
        try:
            start_time = time.time()
            
            with get_db_session() as db:
                # Test basic connectivity
                result = db.execute(text("SELECT 1 as test"))
                test_value = result.scalar()
                
                # Test transaction
                db.execute(text("BEGIN; SELECT 1; COMMIT;"))
                
                # Get database stats
                stats_result = db.execute(text("""
                    SELECT 
                        COUNT(*) as connection_count,
                        (SELECT setting FROM pg_settings WHERE name = 'max_connections') as max_connections
                    FROM pg_stat_activity 
                    WHERE state = 'active'
                """))
                stats = stats_result.fetchone()
                
                response_time = int((time.time() - start_time) * 1000)
                
                return {
                    "status": "healthy" if test_value == 1 else "unhealthy",
                    "response_time_ms": response_time,
                    "active_connections": stats.connection_count if stats else 0,
                    "max_connections": stats.max_connections if stats else 0,
                    "connection_url": str(settings.DATABASE_URL).replace(settings.POSTGRES_PASSWORD, "***"),
                    "pool_size": settings.DATABASE_POOL_SIZE,
                    "details": {
                        "connectivity": "ok",
                        "transactions": "ok",
                        "performance": "good" if response_time < 100 else "slow" if response_time < 500 else "poor"
                    }
                }
                
        except SQLAlchemyError as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "response_time_ms": int((time.time() - start_time) * 1000)
            }
        except Exception as e:
            logger.error(f"Database health check error: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def _check_cache_health(self) -> Dict[str, Any]:
        """Check cache service health"""
        
        try:
            if not settings.CACHE_ENABLED:
                return {
                    "status": "disabled",
                    "message": "Cache is disabled"
                }
            
            start_time = time.time()
            
            # Test cache operations
            test_key = "health_check_test"
            test_value = f"test_{int(time.time())}"
            
            # Set test value
            await cache_service.set(test_key, test_value, ttl=60)
            
            # Get test value
            retrieved_value = await cache_service.get(test_key)
            
            # Delete test value
            await cache_service.delete(test_key)
            
            response_time = int((time.time() - start_time) * 1000)
            
            # Get cache info
            cache_info = await cache_service.get_info()
            
            return {
                "status": "healthy" if retrieved_value == test_value else "unhealthy",
                "response_time_ms": response_time,
                "test_passed": retrieved_value == test_value,
                "redis_info": cache_info,
                "connection_url": str(settings.REDIS_URL).replace(settings.REDIS_PASSWORD, "***"),
                "details": {
                    "connectivity": "ok" if retrieved_value == test_value else "failed",
                    "operations": "ok" if retrieved_value == test_value else "failed",
                    "performance": "good" if response_time < 50 else "slow" if response_time < 200 else "poor"
                }
            }
            
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def _check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage"""
        
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available_gb = memory.available / (1024**3)
            memory_total_gb = memory.total / (1024**3)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_free_gb = disk.free / (1024**3)
            disk_total_gb = disk.total / (1024**3)
            
            # Network stats
            network = psutil.net_io_counters()
            
            # Process info
            process = psutil.Process()
            process_memory = process.memory_info()
            process_cpu = process.cpu_percent()
            
            return {
                "cpu": {
                    "usage_percent": cpu_percent,
                    "count": cpu_count,
                    "status": "healthy" if cpu_percent < 80 else "warning" if cpu_percent < 95 else "critical"
                },
                "memory": {
                    "usage_percent": memory_percent,
                    "available_gb": round(memory_available_gb, 2),
                    "total_gb": round(memory_total_gb, 2),
                    "status": "healthy" if memory_percent < 80 else "warning" if memory_percent < 95 else "critical"
                },
                "disk": {
                    "usage_percent": disk_percent,
                    "free_gb": round(disk_free_gb, 2),
                    "total_gb": round(disk_total_gb, 2),
                    "status": "healthy" if disk_percent < 80 else "warning" if disk_percent < 95 else "critical"
                },
                "network": {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv
                },
                "process": {
                    "cpu_percent": process_cpu,
                    "memory_mb": round(process_memory.rss / (1024**2), 2),
                    "pid": process.pid
                }
            }
            
        except Exception as e:
            logger.error(f"System resources check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def _check_application_health(self) -> Dict[str, Any]:
        """Check application-specific health"""
        
        try:
            # Import here to avoid circular imports
            from app.services import get_services_health
            
            # Get all services health
            services_health = await get_services_health()
            
            # Count healthy services
            healthy_count = sum(1 for service in services_health.values() 
                              if service.get("status") == "healthy")
            total_count = len(services_health)
            
            # Application status
            app_status = "healthy" if healthy_count == total_count else "degraded" if healthy_count > 0 else "unhealthy"
            
            return {
                "status": app_status,
                "services": services_health,
                "services_healthy": healthy_count,
                "services_total": total_count,
                "uptime_seconds": (datetime.utcnow() - self.startup_time).total_seconds(),
                "startup_time": self.startup_time.isoformat(),
                "settings": {
                    "environment": settings.ENVIRONMENT,
                    "debug": settings.DEBUG,
                    "monitoring_enabled": settings.MONITORING_ENABLED,
                    "cache_enabled": settings.CACHE_ENABLED,
                    "emails_enabled": settings.EMAILS_ENABLED
                }
            }
            
        except Exception as e:
            logger.error(f"Application health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def _check_external_services(self) -> Dict[str, Any]:
        """Check external service dependencies"""
        
        external_status = {}
        
        try:
            # Email service (if enabled)
            if settings.EMAILS_ENABLED:
                external_status["email"] = await self._check_email_service()
            
            # Notification services
            if settings.NOTIFICATIONS_ENABLED:
                external_status["notifications"] = await self._check_notification_services()
            
            # LDAP service (if enabled)
            if settings.LDAP_ENABLED:
                external_status["ldap"] = await self._check_ldap_service()
            
            return external_status
            
        except Exception as e:
            logger.error(f"External services check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def _check_email_service(self) -> Dict[str, Any]:
        """Check email service connectivity"""
        
        try:
            import smtplib
            
            start_time = time.time()
            
            # Test SMTP connection
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
            if settings.SMTP_TLS:
                server.starttls()
            
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            
            server.quit()
            
            response_time = int((time.time() - start_time) * 1000)
            
            return {
                "status": "healthy",
                "response_time_ms": response_time,
                "smtp_host": settings.SMTP_HOST,
                "smtp_port": settings.SMTP_PORT
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def _check_notification_services(self) -> Dict[str, Any]:
        """Check notification services"""
        
        notification_status = {}
        
        # Slack
        if settings.SLACK_WEBHOOK_URL:
            try:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        settings.SLACK_WEBHOOK_URL,
                        json={"text": "Health check test"},
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        notification_status["slack"] = {
                            "status": "healthy" if response.status < 400 else "unhealthy",
                            "response_code": response.status
                        }
            except Exception as e:
                notification_status["slack"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        
        # Teams
        if settings.TEAMS_WEBHOOK_URL:
            try:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    payload = {
                        "@type": "MessageCard",
                        "@context": "http://schema.org/extensions",
                        "text": "Health check test"
                    }
                    async with session.post(
                        settings.TEAMS_WEBHOOK_URL,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        notification_status["teams"] = {
                            "status": "healthy" if response.status < 400 else "unhealthy",
                            "response_code": response.status
                        }
            except Exception as e:
                notification_status["teams"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        
        return notification_status
    
    async def _check_ldap_service(self) -> Dict[str, Any]:
        """Check LDAP service connectivity"""
        
        try:
            # This would require python-ldap package
            # For now, return a placeholder
            return {
                "status": "not_implemented",
                "message": "LDAP health check not implemented"
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get application performance metrics"""
        
        try:
            # This would typically come from application metrics
            # For now, return basic metrics
            
            return {
                "response_times": {
                    "avg_response_time_ms": 150,  # Placeholder
                    "p95_response_time_ms": 300,  # Placeholder
                    "p99_response_time_ms": 500   # Placeholder
                },
                "throughput": {
                    "requests_per_second": 100,   # Placeholder
                    "queries_per_minute": 50      # Placeholder
                },
                "errors": {
                    "error_rate_percent": 0.1,    # Placeholder
                    "timeout_rate_percent": 0.05  # Placeholder
                }
            }
            
        except Exception as e:
            logger.error(f"Performance metrics collection failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def _calculate_overall_status(self, components: Dict[str, Any]) -> str:
        """Calculate overall system status based on component health"""
        
        statuses = []
        for component_name, component_data in components.items():
            if isinstance(component_data, dict):
                status = component_data.get("status", "unknown")
                statuses.append(status)
        
        if not statuses:
            return "unknown"
        
        # If any component is unhealthy, system is unhealthy
        if "unhealthy" in statuses:
            return "unhealthy"
        
        # If any component is degraded/warning, system is degraded
        if "degraded" in statuses or "warning" in statuses:
            return "degraded"
        
        # If all components are healthy, system is healthy
        if all(status == "healthy" for status in statuses):
            return "healthy"
        
        return "degraded"
    
    def _check_health_alerts(self, health_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for health alerts based on thresholds"""
        
        alerts = []
        
        try:
            # Check CPU usage
            cpu_usage = health_data.get("system", {}).get("cpu", {}).get("usage_percent", 0)
            if cpu_usage > self.alert_thresholds["cpu_critical"]:
                alerts.append({
                    "level": "critical",
                    "component": "cpu",
                    "message": f"CPU usage is critically high: {cpu_usage}%",
                    "value": cpu_usage,
                    "threshold": self.alert_thresholds["cpu_critical"]
                })
            elif cpu_usage > self.alert_thresholds["cpu_warning"]:
                alerts.append({
                    "level": "warning",
                    "component": "cpu",
                    "message": f"CPU usage is high: {cpu_usage}%",
                    "value": cpu_usage,
                    "threshold": self.alert_thresholds["cpu_warning"]
                })
            
            # Check memory usage
            memory_usage = health_data.get("system", {}).get("memory", {}).get("usage_percent", 0)
            if memory_usage > self.alert_thresholds["memory_critical"]:
                alerts.append({
                    "level": "critical",
                    "component": "memory",
                    "message": f"Memory usage is critically high: {memory_usage}%",
                    "value": memory_usage,
                    "threshold": self.alert_thresholds["memory_critical"]
                })
            elif memory_usage > self.alert_thresholds["memory_warning"]:
                alerts.append({
                    "level": "warning",
                    "component": "memory",
                    "message": f"Memory usage is high: {memory_usage}%",
                    "value": memory_usage,
                    "threshold": self.alert_thresholds["memory_warning"]
                })
            
            # Check disk usage
            disk_usage = health_data.get("system", {}).get("disk", {}).get("usage_percent", 0)
            if disk_usage > self.alert_thresholds["disk_critical"]:
                alerts.append({
                    "level": "critical",
                    "component": "disk",
                    "message": f"Disk usage is critically high: {disk_usage}%",
                    "value": disk_usage,
                    "threshold": self.alert_thresholds["disk_critical"]
                })
            elif disk_usage > self.alert_thresholds["disk_warning"]:
                alerts.append({
                    "level": "warning",
                    "component": "disk",
                    "message": f"Disk usage is high: {disk_usage}%",
                    "value": disk_usage,
                    "threshold": self.alert_thresholds["disk_warning"]
                })
            
            # Check database response time
            db_response_time = health_data.get("components", {}).get("database", {}).get("response_time_ms", 0)
            if db_response_time > self.alert_thresholds["db_response_critical"]:
                alerts.append({
                    "level": "critical",
                    "component": "database",
                    "message": f"Database response time is critically high: {db_response_time}ms",
                    "value": db_response_time,
                    "threshold": self.alert_thresholds["db_response_critical"]
                })
            elif db_response_time > self.alert_thresholds["db_response_warning"]:
                alerts.append({
                    "level": "warning",
                    "component": "database",
                    "message": f"Database response time is high: {db_response_time}ms",
                    "value": db_response_time,
                    "threshold": self.alert_thresholds["db_response_warning"]
                })
            
        except Exception as e:
            logger.error(f"Health alerts check failed: {e}")
            alerts.append({
                "level": "error",
                "component": "health_check",
                "message": f"Failed to check health alerts: {str(e)}"
            })
        
        return alerts
    
    def _load_alert_thresholds(self) -> Dict[str, float]:
        """Load alert thresholds configuration"""
        
        return {
            "cpu_warning": 80.0,
            "cpu_critical": 95.0,
            "memory_warning": 80.0,
            "memory_critical": 95.0,
            "disk_warning": 80.0,
            "disk_critical": 95.0,
            "db_response_warning": 500.0,  # milliseconds
            "db_response_critical": 2000.0,  # milliseconds
            "cache_response_warning": 100.0,  # milliseconds
            "cache_response_critical": 500.0   # milliseconds
        }
    
    def _store_health_history(self, health_data: Dict[str, Any]):
        """Store health check results in history"""
        
        try:
            # Keep only last 100 health checks
            if len(self.health_history) >= 100:
                self.health_history.pop(0)
            
            # Store simplified health data
            self.health_history.append({
                "timestamp": health_data["timestamp"],
                "overall_status": health_data["overall_status"],
                "response_time_ms": health_data.get("response_time_ms", 0),
                "alerts_count": len(health_data.get("alerts", []))
            })
            
        except Exception as e:
            logger.error(f"Failed to store health history: {e}")
    
    async def _periodic_health_check(self):
        """Periodic health check task"""
        
        while True:
            try:
                await asyncio.sleep(settings.HEALTH_CHECK_INTERVAL)
                
                # Perform health check
                health_data = await self.get_system_health()
                
                # Send alerts if critical issues found
                critical_alerts = [
                    alert for alert in health_data.get("alerts", [])
                    if alert.get("level") == "critical"
                ]
                
                if critical_alerts and settings.NOTIFICATIONS_ENABLED:
                    await self._send_health_alerts(critical_alerts)
                
            except Exception as e:
                logger.error(f"Periodic health check failed: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retry
    
    async def _send_health_alerts(self, alerts: List[Dict[str, Any]]):
        """Send health alerts via notifications"""
        
        try:
            if not notification_service:
                return
            
            alert_messages = []
            for alert in alerts:
                alert_messages.append(
                    f"🚨 {alert['level'].upper()}: {alert['message']}"
                )
            
            message = f"""
            🔥 **Critical Health Alert - Enterprise SQL Proxy System**
            
            **Server:** {settings.ENVIRONMENT}
            **Time:** {datetime.utcnow().isoformat()}
            
            **Critical Issues:**
            {chr(10).join(alert_messages)}
            
            Please investigate immediately.
            """
            
            await notification_service.send_notification(
                notification_type="health_alert",
                recipients=["admin@company.com"],  # Configure admin emails
                subject="Critical Health Alert - Enterprise SQL Proxy",
                message=message,
                priority="high"
            )
            
        except Exception as e:
            logger.error(f"Failed to send health alerts: {e}")
    
    async def get_detailed_status(self) -> Dict[str, Any]:
        """Get detailed system status for admin dashboard"""
        
        health_data = await self.get_system_health()
        
        # Add additional details
        health_data["history"] = self.health_history[-20:]  # Last 20 checks
        health_data["thresholds"] = self.alert_thresholds
        health_data["monitoring"] = {
            "enabled": settings.MONITORING_ENABLED,
            "check_interval": settings.HEALTH_CHECK_INTERVAL,
            "last_check": self.last_health_check.isoformat() if self.last_health_check else None
        }
        
        return health_data
    
    async def health_check(self) -> Dict[str, Any]:
        """Quick health check for service monitoring"""
        
        try:
            return {
                "status": self.health_status,
                "last_check": self.last_check.isoformat() if self.last_health_check else None,
                "uptime_seconds": (datetime.utcnow() - self.startup_time).total_seconds(),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def cleanup(self):
        """Cleanup service resources"""
        
        logger.info("✅ Health Service cleanup completed")


# Global health service instance
health_service = HealthService()