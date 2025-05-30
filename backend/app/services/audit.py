"""
Complete Audit Service - Final Version
Created: 2025-05-29 14:30:36 UTC by Teeksss
"""

import logging
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc

from app.core.config import settings
from app.core.database import get_db_session
from app.models.audit import AuditLog
from app.models.user import User
from app.services.cache import cache_service
from app.services.notification import notification_service

logger = logging.getLogger(__name__)


class AuditService:
    """Complete Audit Logging Service"""
    
    def __init__(self):
        self.audit_queue = asyncio.Queue()
        self.stats = {
            "total_logs": 0,
            "security_events": 0,
            "query_events": 0,
            "admin_events": 0,
            "suspicious_events": 0,
            "alerts_triggered": 0
        }
        self.suspicious_patterns = self._load_suspicious_patterns()
        
    async def initialize(self):
        """Initialize audit service"""
        try:
            # Start audit processing worker
            asyncio.create_task(self._audit_worker())
            
            # Start cleanup task
            asyncio.create_task(self._cleanup_old_logs())
            
            logger.info("✅ Audit Service initialized")
            
        except Exception as e:
            logger.error(f"❌ Audit Service initialization failed: {e}")
            raise
    
    async def log_event(
        self,
        action: str,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        severity: str = "info",
        category: str = "general",
        session_id: Optional[str] = None
    ) -> int:
        """Log audit event"""
        
        try:
            # Create audit log entry
            audit_data = {
                "action": action,
                "user_id": user_id,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "details": details or {},
                "severity": severity,
                "category": category,
                "session_id": session_id,
                "timestamp": datetime.utcnow(),
                "risk_score": self._calculate_risk_score(action, details, ip_address),
                "is_suspicious": False,
                "alert_triggered": False
            }
            
            # Check for suspicious activity
            audit_data["is_suspicious"] = await self._check_suspicious_activity(audit_data)
            
            # Queue for processing
            await self.audit_queue.put(audit_data)
            
            self.stats["total_logs"] += 1
            
            # Update category stats
            if category == "security":
                self.stats["security_events"] += 1
            elif category == "query":
                self.stats["query_events"] += 1
            elif category == "admin":
                self.stats["admin_events"] += 1
            
            if audit_data["is_suspicious"]:
                self.stats["suspicious_events"] += 1
            
            return 1  # Placeholder for audit log ID
            
        except Exception as e:
            logger.error(f"Audit logging error: {e}")
            return 0
    
    async def _process_audit_entry(self, audit_data: Dict[str, Any]):
        """Process individual audit entry"""
        
        try:
            with get_db_session() as db:
                # Create audit log record
                audit_log = AuditLog(
                    action=audit_data["action"],
                    user_id=audit_data["user_id"],
                    ip_address=audit_data["ip_address"],
                    user_agent=audit_data["user_agent"],
                    resource_type=audit_data["resource_type"],
                    resource_id=audit_data["resource_id"],
                    details=audit_data["details"],
                    severity=audit_data["severity"],
                    category=audit_data["category"],
                    session_id=audit_data["session_id"],
                    timestamp=audit_data["timestamp"],
                    risk_score=audit_data["risk_score"],
                    is_suspicious=audit_data["is_suspicious"],
                    alert_triggered=audit_data["alert_triggered"]
                )
                
                db.add(audit_log)
                db.commit()
                db.refresh(audit_log)
                
                # Trigger alerts if necessary
                if audit_data["is_suspicious"] or audit_data["risk_score"] > 80:
                    await self._trigger_security_alert(audit_log)
                
                logger.debug(f"Audit log {audit_log.id} processed successfully")
                
        except Exception as e:
            logger.error(f"Process audit entry error: {e}")
    
    async def _check_suspicious_activity(self, audit_data: Dict[str, Any]) -> bool:
        """Check if activity is suspicious"""
        
        try:
            # Check against suspicious patterns
            for pattern_name, pattern_config in self.suspicious_patterns.items():
                if self._matches_pattern(audit_data, pattern_config):
                    logger.warning(f"Suspicious activity detected: {pattern_name}")
                    return True
            
            # Check for rapid repeated actions
            if await self._check_rapid_actions(audit_data):
                return True
            
            # Check for unusual IP activity
            if await self._check_unusual_ip_activity(audit_data):
                return True
            
            # Check for privilege escalation attempts
            if self._check_privilege_escalation(audit_data):
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Suspicious activity check error: {e}")
            return False
    
    def _matches_pattern(self, audit_data: Dict[str, Any], pattern_config: Dict[str, Any]) -> bool:
        """Check if audit data matches suspicious pattern"""
        
        try:
            # Check action pattern
            if "actions" in pattern_config:
                if audit_data["action"] not in pattern_config["actions"]:
                    return False
            
            # Check severity
            if "min_severity" in pattern_config:
                severity_levels = {"info": 1, "warning": 2, "error": 3, "critical": 4}
                if severity_levels.get(audit_data["severity"], 1) < severity_levels.get(pattern_config["min_severity"], 1):
                    return False
            
            # Check details pattern
            if "details_pattern" in pattern_config:
                details = audit_data.get("details", {})
                for key, expected_value in pattern_config["details_pattern"].items():
                    if key not in details or details[key] != expected_value:
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Pattern matching error: {e}")
            return False
    
    async def _check_rapid_actions(self, audit_data: Dict[str, Any]) -> bool:
        """Check for rapid repeated actions"""
        
        try:
            if not audit_data["user_id"]:
                return False
            
            # Check for repeated actions in last 5 minutes
            cache_key = f"rapid_actions:{audit_data['user_id']}:{audit_data['action']}"
            current_count = await cache_service.get(cache_key, 0)
            
            if current_count >= 10:  # More than 10 actions in 5 minutes
                return True
            
            # Increment counter
            await cache_service.set(cache_key, current_count + 1, ttl=300)
            
            return False
            
        except Exception as e:
            logger.error(f"Rapid actions check error: {e}")
            return False
    
    async def _check_unusual_ip_activity(self, audit_data: Dict[str, Any]) -> bool:
        """Check for unusual IP activity"""
        
        try:
            if not audit_data["ip_address"] or not audit_data["user_id"]:
                return False
            
            # Get user's recent IP addresses
            cache_key = f"user_ips:{audit_data['user_id']}"
            recent_ips = await cache_service.get(cache_key, [])
            
            # If new IP and user has been active from other IPs recently
            if (audit_data["ip_address"] not in recent_ips and 
                len(recent_ips) > 0 and 
                len(recent_ips) < 5):  # Not too many IPs (could be legitimate)
                
                # Add current IP to recent IPs
                recent_ips.append(audit_data["ip_address"])
                if len(recent_ips) > 5:
                    recent_ips = recent_ips[-5:]  # Keep only last 5 IPs
                
                await cache_service.set(cache_key, recent_ips, ttl=86400)  # 24 hours
                
                return True
            
            # Update recent IPs
            if audit_data["ip_address"] not in recent_ips:
                recent_ips.append(audit_data["ip_address"])
                if len(recent_ips) > 5:
                    recent_ips = recent_ips[-5:]
                await cache_service.set(cache_key, recent_ips, ttl=86400)
            
            return False
            
        except Exception as e:
            logger.error(f"Unusual IP activity check error: {e}")
            return False
    
    def _check_privilege_escalation(self, audit_data: Dict[str, Any]) -> bool:
        """Check for privilege escalation attempts"""
        
        try:
            escalation_actions = [
                "user_role_changed",
                "user_permissions_modified",
                "admin_access_attempted",
                "system_config_modified"
            ]
            
            return audit_data["action"] in escalation_actions
            
        except Exception as e:
            logger.error(f"Privilege escalation check error: {e}")
            return False
    
    def _calculate_risk_score(
        self, 
        action: str, 
        details: Optional[Dict[str, Any]], 
        ip_address: Optional[str]
    ) -> int:
        """Calculate risk score for action"""
        
        try:
            risk_score = 0
            
            # Base risk by action type
            action_risks = {
                "login_failed": 20,
                "login_success": 5,
                "logout": 0,
                "password_changed": 15,
                "user_created": 30,
                "user_deleted": 50,
                "role_changed": 40,
                "query_executed": 10,
                "query_failed": 25,
                "server_added": 35,
                "server_deleted": 60,
                "config_changed": 45,
                "admin_access": 25
            }
            
            risk_score += action_risks.get(action, 10)
            
            # Risk based on details
            if details:
                if details.get("failed_attempts", 0) > 3:
                    risk_score += 30
                
                if details.get("privilege_escalation"):
                    risk_score += 40
                
                if details.get("system_access"):
                    risk_score += 20
                
                if details.get("data_modification"):
                    risk_score += 15
            
            # Risk based on IP (simplified check)
            if ip_address:
                # Check if IP is from known suspicious ranges
                suspicious_ranges = ["10.0.0.", "192.168.", "172.16."]
                if not any(ip_address.startswith(range_) for range_ in suspicious_ranges):
                    risk_score += 10  # External IP
            
            return min(risk_score, 100)  # Cap at 100
            
        except Exception as e:
            logger.error(f"Risk score calculation error: {e}")
            return 50  # Default medium risk
    
    async def _trigger_security_alert(self, audit_log: AuditLog):
        """Trigger security alert for suspicious activity"""
        
        try:
            # Mark alert as triggered
            audit_log.alert_triggered = True
            
            # Send notification
            alert_message = f"""
            🚨 Security Alert Detected
            
            Action: {audit_log.action}
            User: {audit_log.user.username if audit_log.user else 'Unknown'}
            IP Address: {audit_log.ip_address}
            Risk Score: {audit_log.risk_score}
            Timestamp: {audit_log.timestamp}
            
            Details: {json.dumps(audit_log.details, indent=2)}
            """
            
            await notification_service.send_notification(
                notification_type="security_alert",
                recipients=["admin@company.com"],  # Configure admin emails
                subject=f"Security Alert: {audit_log.action}",
                message=alert_message,
                priority="high"
            )
            
            self.stats["alerts_triggered"] += 1
            
            logger.warning(f"Security alert triggered for audit log {audit_log.id}")
            
        except Exception as e:
            logger.error(f"Security alert trigger error: {e}")
    
    def _load_suspicious_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load suspicious activity patterns"""
        
        return {
            "repeated_login_failures": {
                "actions": ["login_failed"],
                "min_severity": "warning",
                "description": "Multiple login failures"
            },
            "privilege_escalation": {
                "actions": ["user_role_changed", "admin_access_attempted"],
                "min_severity": "warning",
                "description": "Privilege escalation attempt"
            },
            "data_exfiltration": {
                "actions": ["query_executed"],
                "details_pattern": {"large_result_set": True},
                "min_severity": "info",
                "description": "Large data query execution"
            },
            "system_modification": {
                "actions": ["config_changed", "server_deleted"],
                "min_severity": "warning",
                "description": "Critical system modification"
            },
            "after_hours_activity": {
                "actions": ["query_executed", "admin_access"],
                "description": "Activity outside business hours"
            }
        }
    
    async def _cleanup_old_logs(self):
        """Cleanup old audit logs periodically"""
        
        while True:
            try:
                await asyncio.sleep(86400)  # Run daily
                
                if settings.AUDIT_RETENTION_DAYS > 0:
                    cutoff_date = datetime.utcnow() - timedelta(days=settings.AUDIT_RETENTION_DAYS)
                    
                    with get_db_session() as db:
                        deleted_count = db.query(AuditLog).filter(
                            AuditLog.timestamp < cutoff_date
                        ).delete()
                        
                        db.commit()
                        
                        if deleted_count > 0:
                            logger.info(f"Cleaned up {deleted_count} old audit logs")
                
            except Exception as e:
                logger.error(f"Audit cleanup error: {e}")
    
    async def _audit_worker(self):
        """Background worker for audit processing"""
        
        while True:
            try:
                # Get audit data from queue
                audit_data = await self.audit_queue.get()
                
                # Process audit entry
                await self._process_audit_entry(audit_data)
                
                # Mark task as done
                self.audit_queue.task_done()
                
            except Exception as e:
                logger.error(f"Audit worker error: {e}")
                await asyncio.sleep(1)
    
    async def health_check(self) -> Dict[str, Any]:
        """Service health check"""
        
        try:
            queue_size = self.audit_queue.qsize()
            
            with get_db_session() as db:
                total_logs = db.query(AuditLog).count()
                recent_logs = db.query(AuditLog).filter(
                    AuditLog.timestamp > datetime.utcnow() - timedelta(hours=24)
                ).count()
            
            return {
                "status": "healthy",
                "queue_size": queue_size,
                "total_logs": total_logs,
                "recent_logs_24h": recent_logs,
                "patterns_loaded": len(self.suspicious_patterns),
                "stats": self.stats,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get audit metrics"""
        
        return {
            "stats": self.stats,
            "patterns": list(self.suspicious_patterns.keys()),
            "queue_size": self.audit_queue.qsize(),
            "retention_days": settings.AUDIT_RETENTION_DAYS,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def cleanup(self):
        """Cleanup service resources"""
        
        # Wait for queue to empty
        await self.audit_queue.join()
        
        logger.info("✅ Audit Service cleanup completed")


# Global audit service instance
audit_service = AuditService()

# Convenience function
async def log_security_event(
    event_type: str,
    user_id: Optional[int] = None,
    ip_address: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> int:
    """Log security event"""
    return await audit_service.log_security_event(event_type, user_id, ip_address, details)