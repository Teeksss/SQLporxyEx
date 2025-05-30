import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.audit import AuditLog, SecurityEvent, ChangeLog
from app.models.user import User

logger = logging.getLogger(__name__)

class AuditService:
    """Service for comprehensive audit logging and security event tracking"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def log_action(
        self,
        user_id: int,
        action: str,
        resource_type: str,
        status: str = "success",
        resource_id: str = None,
        ip_address: str = None,
        user_agent: str = None,
        session_id: str = None,
        details: Dict[str, Any] = None,
        old_values: Dict[str, Any] = None,
        new_values: Dict[str, Any] = None,
        duration_ms: int = None
    ) -> bool:
        """Log user action for audit trail"""
        try:
            # Get user info
            user = self.db.query(User).filter(User.id == user_id).first()
            username = user.username if user else "unknown"
            user_role = user.role.value if user else "unknown"
            
            # Create audit log entry
            audit_log = AuditLog(
                user_id=user_id,
                username=username,
                user_role=user_role,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                ip_address=ip_address,
                user_agent=user_agent,
                session_id=session_id,
                status=status,
                duration_ms=duration_ms
            )
            
            # Set details
            if details:
                audit_log.set_details(details)
            
            if old_values:
                audit_log.old_values = json.dumps(old_values)
            
            if new_values:
                audit_log.new_values = json.dumps(new_values)
            
            self.db.add(audit_log)
            self.db.commit()
            
            logger.info(f"Action logged: {action} by {username} - {status}")
            return True
            
        except Exception as e:
            logger.error(f"Audit logging failed: {e}")
            self.db.rollback()
            return False
    
    async def log_security_event(
        self,
        event_type: str,
        severity: str,
        description: str,
        source_ip: str = None,
        source_user_id: int = None,
        source_username: str = None,
        details: Dict[str, Any] = None,
        detection_method: str = "system",
        rule_name: str = None
    ) -> bool:
        """Log security event"""
        try:
            security_event = SecurityEvent(
                event_type=event_type,
                severity=severity,
                description=description,
                source_ip=source_ip,
                source_user_id=source_user_id,
                source_username=source_username,
                detection_method=detection_method,
                rule_name=rule_name
            )
            
            if details:
                security_event.details = json.dumps(details)
            
            self.db.add(security_event)
            self.db.commit()
            
            logger.warning(f"Security event: {event_type} - {severity} - {description}")
            return True
            
        except Exception as e:
            logger.error(f"Security event logging failed: {e}")
            self.db.rollback()
            return False
    
    async def log_data_change(
        self,
        table_name: str,
        record_id: str,
        operation: str,
        old_values: Dict[str, Any] = None,
        new_values: Dict[str, Any] = None,
        changed_by: str = "system",
        change_reason: str = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> bool:
        """Log data changes for audit trail"""
        try:
            # Determine changed fields
            changed_fields = []
            if old_values and new_values:
                for key in new_values.keys():
                    if key in old_values and old_values[key] != new_values[key]:
                        changed_fields.append(key)
            elif new_values:
                changed_fields = list(new_values.keys())
            
            change_log = ChangeLog(
                table_name=table_name,
                record_id=record_id,
                operation=operation,
                old_values=json.dumps(old_values) if old_values else None,
                new_values=json.dumps(new_values) if new_values else None,
                changed_fields=json.dumps(changed_fields),
                changed_by=changed_by,
                change_reason=change_reason,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            self.db.add(change_log)
            self.db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Data change logging failed: {e}")
            self.db.rollback()
            return False
    
    async def get_audit_logs(
        self,
        user_id: int = None,
        action: str = None,
        resource_type: str = None,
        status: str = None,
        start_date: datetime = None,
        end_date: datetime = None,
        ip_address: str = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get audit logs with filtering"""
        try:
            query = self.db.query(AuditLog)
            
            # Apply filters
            if user_id:
                query = query.filter(AuditLog.user_id == user_id)
            
            if action:
                query = query.filter(AuditLog.action == action)
            
            if resource_type:
                query = query.filter(AuditLog.resource_type == resource_type)
            
            if status:
                query = query.filter(AuditLog.status == status)
            
            if start_date:
                query = query.filter(AuditLog.created_at >= start_date)
            
            if end_date:
                query = query.filter(AuditLog.created_at <= end_date)
            
            if ip_address:
                query = query.filter(AuditLog.ip_address == ip_address)
            
            # Order by creation time (newest first)
            query = query.order_by(AuditLog.created_at.desc())
            
            # Apply pagination
            logs = query.offset(offset).limit(limit).all()
            
            # Convert to dictionaries
            result = []
            for log in logs:
                result.append({
                    "id": log.id,
                    "user_id": log.user_id,
                    "username": log.username,
                    "user_role": log.user_role,
                    "action": log.action,
                    "resource_type": log.resource_type,
                    "resource_id": log.resource_id,
                    "status": log.status,
                    "ip_address": log.ip_address,
                    "user_agent": log.user_agent,
                    "duration_ms": log.duration_ms,
                    "details": log.get_details(),
                    "created_at": log.created_at.isoformat()
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Audit log retrieval failed: {e}")
            return []
    
    async def get_security_events(
        self,
        event_type: str = None,
        severity: str = None,
        source_ip: str = None,
        start_date: datetime = None,
        end_date: datetime = None,
        is_resolved: bool = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get security events with filtering"""
        try:
            query = self.db.query(SecurityEvent)
            
            # Apply filters
            if event_type:
                query = query.filter(SecurityEvent.event_type == event_type)
            
            if severity:
                query = query.filter(SecurityEvent.severity == severity)
            
            if source_ip:
                query = query.filter(SecurityEvent.source_ip == source_ip)
            
            if start_date:
                query = query.filter(SecurityEvent.occurred_at >= start_date)
            
            if end_date:
                query = query.filter(SecurityEvent.occurred_at <= end_date)
            
            if is_resolved is not None:
                query = query.filter(SecurityEvent.is_resolved == is_resolved)
            
            # Order by occurrence time (newest first)
            events = query.order_by(SecurityEvent.occurred_at.desc()).limit(limit).all()
            
            # Convert to dictionaries
            result = []
            for event in events:
                result.append({
                    "id": event.id,
                    "event_type": event.event_type,
                    "severity": event.severity,
                    "description": event.description,
                    "source_ip": event.source_ip,
                    "source_username": event.source_username,
                    "detection_method": event.detection_method,
                    "rule_name": event.rule_name,
                    "is_resolved": event.is_resolved,
                    "resolved_by": event.resolved_by,
                    "occurred_at": event.occurred_at.isoformat(),
                    "resolved_at": event.resolved_at.isoformat() if event.resolved_at else None
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Security event retrieval failed: {e}")
            return []
    
    async def get_audit_statistics(
        self, 
        days: int = 30
    ) -> Dict[str, Any]:
        """Get audit statistics for dashboard"""
        try:
            since_date = datetime.utcnow() - timedelta(days=days)
            
            # Total actions
            total_actions = self.db.query(AuditLog).filter(
                AuditLog.created_at >= since_date
            ).count()
            
            # Actions by status
            successful_actions = self.db.query(AuditLog).filter(
                AuditLog.created_at >= since_date,
                AuditLog.status == "success"
            ).count()
            
            failed_actions = self.db.query(AuditLog).filter(
                AuditLog.created_at >= since_date,
                AuditLog.status.in_(["error", "failed"])
            ).count()
            
            blocked_actions = self.db.query(AuditLog).filter(
                AuditLog.created_at >= since_date,
                AuditLog.status == "blocked"
            ).count()
            
            # Security events
            security_events = self.db.query(SecurityEvent).filter(
                SecurityEvent.occurred_at >= since_date
            ).count()
            
            critical_events = self.db.query(SecurityEvent).filter(
                SecurityEvent.occurred_at >= since_date,
                SecurityEvent.severity == "critical"
            ).count()
            
            unresolved_events = self.db.query(SecurityEvent).filter(
                SecurityEvent.occurred_at >= since_date,
                SecurityEvent.is_resolved == False
            ).count()
            
            # Top actions
            from sqlalchemy import func
            top_actions = self.db.query(
                AuditLog.action,
                func.count(AuditLog.id).label('count')
            ).filter(
                AuditLog.created_at >= since_date
            ).group_by(AuditLog.action).order_by(
                func.count(AuditLog.id).desc()
            ).limit(10).all()
            
            # Top users by activity
            top_users = self.db.query(
                AuditLog.username,
                func.count(AuditLog.id).label('count')
            ).filter(
                AuditLog.created_at >= since_date
            ).group_by(AuditLog.username).order_by(
                func.count(AuditLog.id).desc()
            ).limit(10).all()
            
            return {
                "period_days": days,
                "total_actions": total_actions,
                "successful_actions": successful_actions,
                "failed_actions": failed_actions,
                "blocked_actions": blocked_actions,
                "success_rate": (successful_actions / total_actions * 100) if total_actions > 0 else 0,
                "security_events": security_events,
                "critical_events": critical_events,
                "unresolved_events": unresolved_events,
                "top_actions": [{"action": action, "count": count} for action, count in top_actions],
                "top_users": [{"username": username, "count": count} for username, count in top_users]
            }
            
        except Exception as e:
            logger.error(f"Audit statistics generation failed: {e}")
            return {"error": str(e)}
    
    async def resolve_security_event(
        self,
        event_id: int,
        resolved_by: str,
        resolution_notes: str = None
    ) -> bool:
        """Mark security event as resolved"""
        try:
            event = self.db.query(SecurityEvent).filter(
                SecurityEvent.id == event_id
            ).first()
            
            if not event:
                return False
            
            event.is_resolved = True
            event.resolved_by = resolved_by
            event.resolved_at = datetime.utcnow()
            
            # Add resolution notes to actions_taken
            actions = []
            if event.actions_taken:
                try:
                    actions = json.loads(event.actions_taken)
                except json.JSONDecodeError:
                    actions = []
            
            actions.append({
                "action": "resolved",
                "by": resolved_by,
                "timestamp": datetime.utcnow().isoformat(),
                "notes": resolution_notes
            })
            
            event.actions_taken = json.dumps(actions)
            
            self.db.commit()
            
            logger.info(f"Security event {event_id} resolved by {resolved_by}")
            return True
            
        except Exception as e:
            logger.error(f"Security event resolution failed: {e}")
            self.db.rollback()
            return False