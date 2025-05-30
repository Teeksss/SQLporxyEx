import smtplib
import requests
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy.orm import Session

from app.models.notification import (
    NotificationRule, NotificationDelivery, EmailTemplate, 
    WebhookEndpoint, NotificationType, NotificationChannel
)
from app.services.config_service import ConfigService
from app.core.security import decrypt_sensitive_data

logger = logging.getLogger(__name__)

class NotificationService:
    """Service for sending notifications via multiple channels"""
    
    def __init__(self, db: Session):
        self.db = db
        self.config_service = ConfigService(db)
    
    async def send_notification(
        self,
        notification_type: NotificationType,
        context: Dict[str, Any],
        recipients: List[str] = None,
        force_send: bool = False
    ) -> Dict[str, Any]:
        """Send notification based on type and context"""
        try:
            # Get applicable notification rules
            rules = self.db.query(NotificationRule).filter(
                NotificationRule.notification_type == notification_type,
                NotificationRule.is_active == True
            ).all()
            
            if not rules:
                logger.info(f"No notification rules found for type: {notification_type.value}")
                return {"success": True, "message": "No rules configured"}
            
            results = []
            
            for rule in rules:
                # Check cooldown period
                if not force_send and await self._is_in_cooldown(rule, context):
                    continue
                
                # Check trigger conditions
                if not await self._check_trigger_conditions(rule, context):
                    continue
                
                # Send notification via configured channels
                rule_result = await self._send_via_rule(rule, context, recipients)
                results.append(rule_result)
            
            return {
                "success": True,
                "rules_processed": len(results),
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Notification sending failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_email(
        self,
        recipients: List[str],
        subject: str,
        body: str,
        html_body: str = None
    ) -> Dict[str, Any]:
        """Send email notification"""
        try:
            # Get SMTP configuration
            smtp_enabled = await self.config_service.get_config("email_notifications_enabled", False)
            if not smtp_enabled:
                return {"success": False, "error": "Email notifications disabled"}
            
            smtp_server = await self.config_service.get_config("smtp_server")
            smtp_port = await self.config_service.get_config("smtp_port", 587)
            smtp_username = await self.config_service.get_config("smtp_username")
            smtp_password = await self.config_service.get_config("smtp_password")
            
            if not all([smtp_server, smtp_username, smtp_password]):
                return {"success": False, "error": "SMTP configuration incomplete"}
            
            # Decrypt password
            smtp_password = decrypt_sensitive_data(smtp_password)
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = smtp_username
            msg['To'] = ', '.join(recipients)
            
            # Add text part
            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)
            
            # Add HTML part if provided
            if html_body:
                html_part = MIMEText(html_body, 'html')
                msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent to {len(recipients)} recipients")
            return {
                "success": True,
                "recipients_count": len(recipients)
            }
            
        except Exception as e:
            logger.error(f"Email sending failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_webhook(
        self,
        webhook_id: int,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send webhook notification"""
        try:
            webhook = self.db.query(WebhookEndpoint).filter(
                WebhookEndpoint.id == webhook_id,
                WebhookEndpoint.is_active == True
            ).first()
            
            if not webhook:
                return {"success": False, "error": "Webhook not found"}
            
            # Prepare headers
            headers = {"Content-Type": "application/json"}
            if webhook.headers:
                try:
                    custom_headers = json.loads(webhook.headers)
                    headers.update(custom_headers)
                except json.JSONDecodeError:
                    pass
            
            # Add authentication
            if webhook.auth_type == "bearer" and webhook.auth_token:
                token = decrypt_sensitive_data(webhook.auth_token)
                headers["Authorization"] = f"Bearer {token}"
            elif webhook.auth_type == "api_key" and webhook.api_key_header and webhook.api_key_value:
                key_value = decrypt_sensitive_data(webhook.api_key_value)
                headers[webhook.api_key_header] = key_value
            
            # Prepare payload
            if webhook.payload_template:
                try:
                    template = json.loads(webhook.payload_template)
                    # Simple template variable replacement
                    payload_str = json.dumps(template)
                    for key, value in payload.items():
                        payload_str = payload_str.replace(f"{{{key}}}", str(value))
                    final_payload = json.loads(payload_str)
                except json.JSONDecodeError:
                    final_payload = payload
            else:
                final_payload = payload
            
            # Send webhook
            auth = None
            if webhook.auth_type == "basic" and webhook.auth_username and webhook.auth_password:
                username = webhook.auth_username
                password = decrypt_sensitive_data(webhook.auth_password)
                auth = (username, password)
            
            response = requests.request(
                method=webhook.method,
                url=webhook.url,
                json=final_payload,
                headers=headers,
                auth=auth,
                timeout=webhook.timeout_seconds,
                verify=webhook.verify_ssl
            )
            
            response.raise_for_status()
            
            # Update webhook status
            webhook.last_test_at = datetime.utcnow()
            webhook.last_test_status = "success"
            self.db.commit()
            
            logger.info(f"Webhook sent successfully to {webhook.url}")
            return {
                "success": True,
                "status_code": response.status_code,
                "response": response.text[:500]  # Truncate response
            }
            
        except Exception as e:
            logger.error(f"Webhook sending failed: {e}")
            
            # Update webhook status
            if 'webhook' in locals():
                webhook.last_test_at = datetime.utcnow()
                webhook.last_test_status = "failed"
                self.db.commit()
            
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_webhook(self, webhook_id: int) -> Dict[str, Any]:
        """Test webhook endpoint"""
        test_payload = {
            "test": True,
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Test notification from SQL Proxy System"
        }
        
        return await self.send_webhook(webhook_id, test_payload)
    
    async def create_notification_rule(
        self,
        name: str,
        notification_type: NotificationType,
        channels: List[NotificationChannel],
        recipients: Dict[str, List[str]],
        message_template: str,
        subject_template: str = None,
        trigger_conditions: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Create new notification rule"""
        try:
            rule = NotificationRule(
                name=name,
                notification_type=notification_type,
                channels=json.dumps([channel.value for channel in channels]),
                recipients=json.dumps(recipients),
                message_template=message_template,
                subject_template=subject_template,
                trigger_conditions=json.dumps(trigger_conditions or {}),
                created_by="system"
            )
            
            self.db.add(rule)
            self.db.commit()
            
            return {
                "success": True,
                "rule_id": rule.id
            }
            
        except Exception as e:
            logger.error(f"Notification rule creation failed: {e}")
            self.db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _send_via_rule(
        self,
        rule: NotificationRule,
        context: Dict[str, Any],
        override_recipients: List[str] = None
    ) -> Dict[str, Any]:
        """Send notification via specific rule"""
        try:
            channels = json.loads(rule.channels)
            recipients = json.loads(rule.recipients) if not override_recipients else {
                "email": override_recipients
            }
            
            # Render message from template
            message = await self._render_template(rule.message_template, context)
            subject = await self._render_template(rule.subject_template or "Notification", context)
            
            results = []
            
            for channel in channels:
                if channel == "email" and "email" in recipients:
                    result = await self.send_email(
                        recipients["email"],
                        subject,
                        message
                    )
                    results.append({"channel": "email", **result})
                
                elif channel == "webhook" and "webhook" in recipients:
                    for webhook_id in recipients["webhook"]:
                        result = await self.send_webhook(
                            int(webhook_id),
                            {
                                "subject": subject,
                                "message": message,
                                "context": context
                            }
                        )
                        results.append({"channel": "webhook", "webhook_id": webhook_id, **result})
            
            # Record delivery attempts
            for result in results:
                delivery = NotificationDelivery(
                    rule_id=rule.id,
                    channel=NotificationChannel(result["channel"]),
                    recipient=str(result.get("webhook_id", "email")),
                    subject=subject,
                    message=message,
                    status="sent" if result["success"] else "failed",
                    response_message=result.get("error", "Success")
                )
                self.db.add(delivery)
            
            self.db.commit()
            
            return {
                "rule_name": rule.name,
                "success": all(r["success"] for r in results),
                "channels_sent": len([r for r in results if r["success"]]),
                "total_channels": len(results),
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Rule notification sending failed: {e}")
            return {
                "rule_name": rule.name,
                "success": False,
                "error": str(e)
            }
    
    async def _render_template(self, template: str, context: Dict[str, Any]) -> str:
        """Render message template with context variables"""
        try:
            # Simple template rendering - replace {variable} with values
            rendered = template
            for key, value in context.items():
                placeholder = f"{{{key}}}"
                rendered = rendered.replace(placeholder, str(value))
            
            # Add common variables
            rendered = rendered.replace("{timestamp}", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"))
            rendered = rendered.replace("{system_name}", "Enterprise SQL Proxy System")
            
            return rendered
            
        except Exception as e:
            logger.error(f"Template rendering failed: {e}")
            return template
    
    async def _check_trigger_conditions(
        self,
        rule: NotificationRule,
        context: Dict[str, Any]
    ) -> bool:
        """Check if trigger conditions are met"""
        try:
            if not rule.trigger_conditions:
                return True
            
            conditions = json.loads(rule.trigger_conditions)
            
            # Simple condition checking
            for key, expected_value in conditions.items():
                if key not in context:
                    return False
                
                if context[key] != expected_value:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Trigger condition check failed: {e}")
            return False
    
    async def _is_in_cooldown(
        self,
        rule: NotificationRule,
        context: Dict[str, Any]
    ) -> bool:
        """Check if rule is in cooldown period"""
        try:
            if not rule.cooldown_minutes:
                return False
            
            cooldown_time = datetime.utcnow() - timedelta(minutes=rule.cooldown_minutes)
            
            recent_delivery = self.db.query(NotificationDelivery).filter(
                NotificationDelivery.rule_id == rule.id,
                NotificationDelivery.created_at >= cooldown_time,
                NotificationDelivery.status == "sent"
            ).first()
            
            return recent_delivery is not None
            
        except Exception as e:
            logger.error(f"Cooldown check failed: {e}")
            return False