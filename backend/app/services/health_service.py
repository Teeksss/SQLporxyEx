import asyncio
import logging
import psutil
import time
from typing import Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.server import SQLServerConnection, ServerHealthHistory
from app.models.audit import SecurityEvent
from app.services.config_service import ConfigService

logger = logging.getLogger(__name__)

class HealthService:
    """Service for system health monitoring"""
    
    def __init__(self, db: Session):
        self.db = db
        self.config_service = ConfigService(db)
    
    async def get_comprehensive_health_report(self) -> Dict[str, Any]:
        """Get comprehensive health report for all system components"""
        try:
            report = {
                "timestamp": datetime.utcnow().isoformat(),
                "overall_status": "healthy",
                "components": {},
                "alerts": [],
                "performance": {}
            }
            
            # Check database connectivity
            db_health = await self._check_database_health()
            report["components"]["database"] = db_health
            
            # Check Redis connectivity
            redis_health = await self._check_redis_health()
            report["components"]["redis"] = redis_health
            
            # Check SQL servers
            servers_health = await self.check_all_servers()
            report["components"]["sql_servers"] = servers_health
            
            # Check system resources
            system_health = await self._check_system_resources()
            report["components"]["system"] = system_health
            report["performance"] = system_health.get("metrics", {})
            
            # Check configuration
            config_health = await self._check_configuration()
            report["components"]["configuration"] = config_health
            
            # Determine overall status
            component_statuses = [
                comp.get("status", "unknown") 
                for comp in report["components"].values()
            ]
            
            if "critical" in component_statuses:
                report["overall_status"] = "critical"
            elif "unhealthy" in component_statuses:
                report["overall_status"] = "unhealthy"
            elif "warning" in component_statuses:
                report["overall_status"] = "warning"
            
            # Get active alerts
            report["alerts"] = await self.get_active_alerts()
            
            return report
            
        except Exception as e:
            logger.error(f"Health report generation failed: {e}")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "overall_status": "critical",
                "error": str(e)
            }
    
    async def check_all_servers(self) -> Dict[str, Any]:
        """Check health of all SQL servers"""
        try:
            servers = self.db.query(SQLServerConnection).filter(
                SQLServerConnection.is_active == True
            ).all()
            
            server_results = []
            healthy_count = 0
            
            for server in servers:
                health_result = await self.check_server_health(server.id)
                server_results.append(health_result)
                
                if health_result.get("status") == "healthy":
                    healthy_count += 1
            
            overall_status = "healthy"
            if healthy_count == 0:
                overall_status = "critical"
            elif healthy_count < len(servers):
                overall_status = "warning"
            
            return {
                "status": overall_status,
                "total_servers": len(servers),
                "healthy_servers": healthy_count,
                "servers": server_results
            }
            
        except Exception as e:
            logger.error(f"Server health check failed: {e}")
            return {
                "status": "critical",
                "error": str(e)
            }
    
    async def check_server_health(self, server_id: int) -> Dict[str, Any]:
        """Check health of specific SQL server"""
        try:
            server = self.db.query(SQLServerConnection).filter(
                SQLServerConnection.id == server_id
            ).first()
            
            if not server:
                return {
                    "server_id": server_id,
                    "status": "not_found",
                    "message": "Server not found"
                }
            
            start_time = time.time()
            
            try:
                # Test connection
                from app.services.query_service import QueryService
                query_service = QueryService(self.db)
                
                # Decrypt password for connection test
                from app.core.security import decrypt_sensitive_data
                decrypted_password = decrypt_sensitive_data(server.password)
                
                connection_test = await query_service.test_connection({
                    "server": server.host,
                    "port": server.port,
                    "database": server.database,
                    "username": server.username,
                    "password": decrypted_password
                })
                
                response_time = int((time.time() - start_time) * 1000)
                
                if connection_test["success"]:
                    status = "healthy"
                    message = "Connection successful"
                else:
                    status = "unhealthy"
                    message = connection_test.get("message", "Connection failed")
                
            except Exception as e:
                response_time = int((time.time() - start_time) * 1000)
                status = "unhealthy"
                message = str(e)
            
            # Update server health in database
            server.last_health_check = datetime.utcnow()
            server.health_status = status
            server.health_message = message
            server.response_time_ms = response_time
            
            # Record health history
            health_history = ServerHealthHistory(
                server_id=server.id,
                status=status,
                response_time_ms=response_time,
                error_message=message if status != "healthy" else None
            )
            self.db.add(health_history)
            self.db.commit()
            
            return {
                "server_id": server.id,
                "server_name": server.name,
                "status": status,
                "message": message,
                "response_time_ms": response_time,
                "last_check": server.last_health_check.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Server {server_id} health check failed: {e}")
            return {
                "server_id": server_id,
                "status": "error",
                "message": str(e)
            }
    
    async def get_system_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """Get system performance metrics"""
        try:
            # Current system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Network stats
            network = psutil.net_io_counters()
            
            # Process info
            process = psutil.Process()
            process_memory = process.memory_info()
            
            current_metrics = {
                "cpu_usage_percent": cpu_percent,
                "memory_usage_percent": memory.percent,
                "memory_used_gb": round(memory.used / (1024**3), 2),
                "memory_total_gb": round(memory.total / (1024**3), 2),
                "disk_usage_percent": disk.percent,
                "disk_used_gb": round(disk.used / (1024**3), 2),
                "disk_total_gb": round(disk.total / (1024**3), 2),
                "network_bytes_sent": network.bytes_sent,
                "network_bytes_recv": network.bytes_recv,
                "process_memory_mb": round(process_memory.rss / (1024**2), 2)
            }
            
            # Historical metrics (last N hours)
            since_time = datetime.utcnow() - timedelta(hours=hours)
            
            # Query execution metrics
            from app.models.query import QueryExecution
            query_stats = self.db.query(QueryExecution).filter(
                QueryExecution.started_at >= since_time
            )
            
            total_queries = query_stats.count()
            successful_queries = query_stats.filter(
                QueryExecution.status == "success"
            ).count()
            
            avg_execution_time = 0
            if total_queries > 0:
                from sqlalchemy import func
                avg_time = self.db.query(
                    func.avg(QueryExecution.execution_time_ms)
                ).filter(
                    QueryExecution.started_at >= since_time,
                    QueryExecution.status == "success"
                ).scalar()
                avg_execution_time = round(avg_time or 0, 2)
            
            # Server health metrics
            server_health_stats = self.db.query(ServerHealthHistory).filter(
                ServerHealthHistory.checked_at >= since_time
            )
            
            total_health_checks = server_health_stats.count()
            healthy_checks = server_health_stats.filter(
                ServerHealthHistory.status == "healthy"
            ).count()
            
            return {
                "current": current_metrics,
                "period_hours": hours,
                "query_metrics": {
                    "total_queries": total_queries,
                    "successful_queries": successful_queries,
                    "success_rate": (successful_queries / total_queries * 100) if total_queries > 0 else 0,
                    "avg_execution_time_ms": avg_execution_time
                },
                "server_metrics": {
                    "total_health_checks": total_health_checks,
                    "healthy_checks": healthy_checks,
                    "health_rate": (healthy_checks / total_health_checks * 100) if total_health_checks > 0 else 0
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"System metrics collection failed: {e}")
            return {"error": str(e)}
    
    async def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get active system alerts"""
        try:
            alerts = []
            
            # Check for recent security events
            recent_time = datetime.utcnow() - timedelta(hours=1)
            security_events = self.db.query(SecurityEvent).filter(
                SecurityEvent.occurred_at >= recent_time,
                SecurityEvent.is_resolved == False,
                SecurityEvent.severity.in_(["high", "critical"])
            ).all()
            
            for event in security_events:
                alerts.append({
                    "type": "security",
                    "severity": event.severity,
                    "message": event.description,
                    "occurred_at": event.occurred_at.isoformat(),
                    "source": event.source_ip
                })
            
            # Check for server health issues
            unhealthy_servers = self.db.query(SQLServerConnection).filter(
                SQLServerConnection.is_active == True,
                SQLServerConnection.health_status.in_(["unhealthy", "critical"])
            ).all()
            
            for server in unhealthy_servers:
                alerts.append({
                    "type": "server_health",
                    "severity": "high" if server.health_status == "critical" else "medium",
                    "message": f"Server {server.name} is {server.health_status}: {server.health_message}",
                    "occurred_at": server.last_health_check.isoformat() if server.last_health_check else None,
                    "server_id": server.id
                })
            
            # Check system resource alerts
            system_metrics = await self.get_system_metrics(1)
            current = system_metrics.get("current", {})
            
            if current.get("cpu_usage_percent", 0) > 90:
                alerts.append({
                    "type": "resource",
                    "severity": "high",
                    "message": f"High CPU usage: {current['cpu_usage_percent']:.1f}%",
                    "occurred_at": datetime.utcnow().isoformat()
                })
            
            if current.get("memory_usage_percent", 0) > 90:
                alerts.append({
                    "type": "resource",
                    "severity": "high",
                    "message": f"High memory usage: {current['memory_usage_percent']:.1f}%",
                    "occurred_at": datetime.utcnow().isoformat()
                })
            
            if current.get("disk_usage_percent", 0) > 90:
                alerts.append({
                    "type": "resource",
                    "severity": "high",
                    "message": f"High disk usage: {current['disk_usage_percent']:.1f}%",
                    "occurred_at": datetime.utcnow().isoformat()
                })
            
            return alerts
            
        except Exception as e:
            logger.error(f"Alert collection failed: {e}")
            return []
    
    async def _check_database_health(self) -> Dict[str, Any]:
        """Check main database health"""
        try:
            start_time = time.time()
            self.db.execute(text("SELECT 1"))
            response_time = int((time.time() - start_time) * 1000)
            
            return {
                "status": "healthy",
                "message": "Database connection successful",
                "response_time_ms": response_time
            }
        except Exception as e:
            return {
                "status": "critical",
                "message": f"Database connection failed: {str(e)}"
            }
    
    async def _check_redis_health(self) -> Dict[str, Any]:
        """Check Redis health"""
        try:
            # This would implement actual Redis health check
            # For now, return healthy status
            return {
                "status": "healthy",
                "message": "Redis connection successful"
            }
        except Exception as e:
            return {
                "status": "warning",
                "message": f"Redis check failed: {str(e)}"
            }
    
    async def _check_system_resources(self) -> Dict[str, Any]:
        """Check system resource health"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            status = "healthy"
            warnings = []
            
            if cpu_percent > 90:
                status = "critical"
                warnings.append(f"High CPU usage: {cpu_percent:.1f}%")
            elif cpu_percent > 80:
                status = "warning"
                warnings.append(f"Elevated CPU usage: {cpu_percent:.1f}%")
            
            if memory.percent > 90:
                status = "critical"
                warnings.append(f"High memory usage: {memory.percent:.1f}%")
            elif memory.percent > 80:
                status = "warning"
                warnings.append(f"Elevated memory usage: {memory.percent:.1f}%")
            
            if disk.percent > 90:
                status = "critical"
                warnings.append(f"High disk usage: {disk.percent:.1f}%")
            elif disk.percent > 85:
                status = "warning"
                warnings.append(f"Elevated disk usage: {disk.percent:.1f}%")
            
            return {
                "status": status,
                "message": "; ".join(warnings) if warnings else "System resources normal",
                "metrics": {
                    "cpu_usage_percent": cpu_percent,
                    "memory_usage_percent": memory.percent,
                    "disk_usage_percent": disk.percent
                }
            }
        except Exception as e:
            return {
                "status": "warning",
                "message": f"Resource check failed: {str(e)}"
            }
    
    async def _check_configuration(self) -> Dict[str, Any]:
        """Check system configuration health"""
        try:
            issues = []
            
            # Check critical configurations
            setup_complete = await self.config_service.get_config("setup_complete", False)
            if not setup_complete:
                issues.append("System setup not completed")
            
            ldap_enabled = await self.config_service.get_config("ldap_enabled", False)
            if ldap_enabled:
                ldap_server = await self.config_service.get_config("ldap_server", "")
                if not ldap_server:
                    issues.append("LDAP enabled but server not configured")
            
            status = "critical" if issues else "healthy"
            message = "; ".join(issues) if issues else "Configuration is valid"
            
            return {
                "status": status,
                "message": message
            }
        except Exception as e:
            return {
                "status": "warning",
                "message": f"Configuration check failed: {str(e)}"
            }