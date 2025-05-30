"""
Complete Notification Service - Final Version
Created: 2025-05-29 14:27:08 UTC by Teeksss
"""

import logging
import asyncio
import smtplib
import ssl
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import json
import aiohttp
import jinja2

from app.core.config import settings
from app.core.database import get_db_session
from app.models.notification import (
    NotificationDelivery, NotificationRule, NotificationTemplate,
    NotificationStatus, NotificationChannel, NotificationPriority
)
from app.services.cache import cache_service

logger = logging.getLogger(__name__)


class NotificationService:
    """Complete Notification Service"""
    
    def __init__(self):
        self.email_config = self._load_email_config()
        self.webhook_config = self._load_webhook_config()
        self.templates = {}
        self.delivery_queue = asyncio.Queue()
        self.stats = {
            "total_sent": 0,
            "total_failed": 0,
            "email_sent": 0,
            "email_failed": 0,
            "webhook_sent": 0,
            "webhook_failed": 0,
            "slack_sent": 0,
            "slack_failed": 0
        }
        
    async def initialize(self):
        """Initialize notification service"""
        try:
            # Load notification templates
            await self._load_templates()
            
            # Start delivery worker
            asyncio.create_task(self._delivery_worker())
            
            logger.info("✅ Notification Service initialized")
            
        except Exception as e:
            logger.error(f"❌ Notification Service initialization failed: {e}")
            raise
    
    async def send_notification(
        self,
        notification_type: str,
        recipients: List[str],
        subject: str,
        message: str,
        channels: List[NotificationChannel] = None,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        template_name: str = None,
        template_data: Dict[str, Any] = None,
        attachments: List[Dict[str, Any]] = None,
        metadata: Dict[str, Any] = None
    ) -> List[int]:
        """Send notification through multiple channels"""
        
        try:
            if channels is None:
                channels = [NotificationChannel.EMAIL]
            
            delivery_ids = []
            
            for channel in channels:
                # Create delivery record
                delivery_id = await self._create_delivery_record(
                    notification_type=notification_type,
                    channel=channel,
                    recipients=recipients,
                    subject=subject,
                    message=message,
                    priority=priority,
                    template_name=template_name,
                    template_data=template_data,
                    attachments=attachments,
                    metadata=metadata
                )
                
                if delivery_id:
                    delivery_ids.append(delivery_id)
                    
                    # Queue for delivery
                    await self.delivery_queue.put({
                        "delivery_id": delivery_id,
                        "channel": channel
                    })
            
            return delivery_ids
            
        except Exception as e:
            logger.error(f"Send notification error: {e}")
            return []
    
    async def send_email(
        self,
        recipients: List[str],
        subject: str,
        message: str,
        html_message: str = None,
        template_name: str = None,
        template_data: Dict[str, Any] = None,
        attachments: List[Dict[str, Any]] = None
    ) -> bool:
        """Send email notification"""
        
        try:
            if not settings.EMAILS_ENABLED:
                logger.warning("Email notifications are disabled")
                return False
            
            # Render template if provided
            if template_name and template_data:
                message, html_message = await self._render_email_template(
                    template_name, template_data
                )
            
            # Create email message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_config['from_address']
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = subject
            
            # Add text part
            text_part = MIMEText(message, 'plain', 'utf-8')
            msg.attach(text_part)
            
            # Add HTML part if provided
            if html_message:
                html_part = MIMEText(html_message, 'html', 'utf-8')
                msg.attach(html_part)
            
            # Add attachments
            if attachments:
                for attachment in attachments:
                    await self._add_attachment(msg, attachment)
            
            # Send email
            success = await self._send_smtp_email(msg, recipients)
            
            if success:
                self.stats["email_sent"] += 1
                self.stats["total_sent"] += 1
            else:
                self.stats["email_failed"] += 1
                self.stats["total_failed"] += 1
            
            return success
            
        except Exception as e:
            logger.error(f"Email sending error: {e}")
            self.stats["email_failed"] += 1
            self.stats["total_failed"] += 1
            return False
    
    async def send_webhook(
        self,
        webhook_url: str,
        payload: Dict[str, Any],
        headers: Dict[str, str] = None,
        timeout: int = 30
    ) -> bool:
        """Send webhook notification"""
        
        try:
            if headers is None:
                headers = {'Content-Type': 'application/json'}
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                async with session.post(
                    webhook_url,
                    json=payload,
                    headers=headers
                ) as response:
                    success = response.status < 400
                    
                    if success:
                        self.stats["webhook_sent"] += 1
                        self.stats["total_sent"] += 1
                        logger.info(f"Webhook sent successfully to {webhook_url}")
                    else:
                        self.stats["webhook_failed"] += 1
                        self.stats["total_failed"] += 1
                        logger.error(f"Webhook failed: {response.status} - {await response.text()}")
                    
                    return success
                    
        except Exception as e:
            logger.error(f"Webhook sending error: {e}")
            self.stats["webhook_failed"] += 1
            self.stats["total_failed"] += 1
            return False
    
    async def send_slack_notification(
        self,
        message: str,
        channel: str = None,
        username: str = None,
        icon_emoji: str = None,
        attachments: List[Dict[str, Any]] = None
    ) -> bool:
        """Send Slack notification"""
        
        try:
            if not settings.SLACK_WEBHOOK_URL:
                logger.warning("Slack webhook URL not configured")
                return False
            
            payload = {
                "text": message,
                "username": username or "Enterprise SQL Proxy",
                "icon_emoji": icon_emoji or ":robot_face:"
            }
            
            if channel:
                payload["channel"] = channel
            
            if attachments:
                payload["attachments"] = attachments
            
            success = await self.send_webhook(settings.SLACK_WEBHOOK_URL, payload)
            
            if success:
                self.stats["slack_sent"] += 1
            else:
                self.stats["slack_failed"] += 1
            
            return success
            
        except Exception as e:
            logger.error(f"Slack notification error: {e}")
            self.stats["slack_failed"] += 1
            return False
    
    async def send_teams_notification(
        self,
        title: str,
        message: str,
        color: str = "0078D4",
        sections: List[Dict[str, Any]] = None
    ) -> bool:
        """Send Microsoft Teams notification"""
        
        try:
            if not settings.TEAMS_WEBHOOK_URL:
                logger.warning("Teams webhook URL not configured")
                return False
            
            payload = {
                "@type": "MessageCard",
                "@context": "http://schema.org/extensions",
                "themeColor": color,
                "title": title,
                "text": message
            }
            
            if sections:
                payload["sections"] = sections
            
            return await self.send_webhook(settings.TEAMS_WEBHOOK_URL, payload)
            
        except Exception as e:
            logger.error(f"Teams notification error: {e}")
            return False
    
    async def _delivery_worker(self):
        """Background worker for notification delivery"""
        
        while True:
            try:
                # Get delivery task from queue
                task = await self.delivery_queue.get()
                
                # Process delivery
                await self._process_delivery(task["delivery_id"], task["channel"])
                
                # Mark task as done
                self.delivery_queue.task_done()
                
            except Exception as e:
                logger.error(f"Delivery worker error: {e}")
                await asyncio.sleep(1)
    
    async def _process_delivery(self, delivery_id: int, channel: NotificationChannel):
        """Process individual notification delivery"""
        
        try:
            with get_db_session() as db:
                # Get delivery record
                delivery = db.query(NotificationDelivery).filter(
                    NotificationDelivery.id == delivery_id
                ).first()
                
                if not delivery:
                    logger.error(f"Delivery record {delivery_id} not found")
                    return
                
                # Update status to sending
                delivery.status = NotificationStatus.SENDING
                delivery.sent_at = datetime.utcnow()
                db.commit()
                
                # Parse recipients
                recipients = json.loads(delivery.recipients) if isinstance(delivery.recipients, str) else [delivery.recipients]
                
                # Send based on channel
                success = False
                
                if channel == NotificationChannel.EMAIL:
                    success = await self.send_email(
                        recipients=recipients,
                        subject=delivery.subject,
                        message=delivery.message,
                        template_name=delivery.template_name,
                        template_data=json.loads(delivery.template_data) if delivery.template_data else None,
                        attachments=json.loads(delivery.attachments) if delivery.attachments else None
                    )
                
                elif channel == NotificationChannel.WEBHOOK:
                    webhook_url = recipients[0] if recipients else None
                    if webhook_url:
                        payload = {
                            "subject": delivery.subject,
                            "message": delivery.message,
                            "type": delivery.notification_type,
                            "priority": delivery.priority.value,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                        success = await self.send_webhook(webhook_url, payload)
                
                elif channel == NotificationChannel.SLACK:
                    success = await self.send_slack_notification(
                        message=f"*{delivery.subject}*\n{delivery.message}"
                    )
                
                elif channel == NotificationChannel.TEAMS:
                    success = await self.send_teams_notification(
                        title=delivery.subject,
                        message=delivery.message
                    )
                
                # Update delivery status
                delivery.status = NotificationStatus.SENT if success else NotificationStatus.FAILED
                delivery.delivered_at = datetime.utcnow() if success else None
                
                if not success:
                    delivery.error_message = "Delivery failed"
                
                db.commit()
                
                logger.info(f"Delivery {delivery_id} {'succeeded' if success else 'failed'}")
                
        except Exception as e:
            logger.error(f"Process delivery error: {e}")
            
            # Update delivery as failed
            try:
                with get_db_session() as db:
                    delivery = db.query(NotificationDelivery).filter(
                        NotificationDelivery.id == delivery_id
                    ).first()
                    
                    if delivery:
                        delivery.status = NotificationStatus.FAILED
                        delivery.error_message = str(e)
                        db.commit()
            except:
                pass
    
    async def _create_delivery_record(
        self,
        notification_type: str,
        channel: NotificationChannel,
        recipients: List[str],
        subject: str,
        message: str,
        priority: NotificationPriority,
        template_name: str = None,
        template_data: Dict[str, Any] = None,
        attachments: List[Dict[str, Any]] = None,
        metadata: Dict[str, Any] = None
    ) -> Optional[int]:
        """Create notification delivery record"""
        
        try:
            with get_db_session() as db:
                delivery = NotificationDelivery(
                    notification_type=notification_type,
                    channel=channel,
                    priority=priority,
                    recipients=json.dumps(recipients),
                    subject=subject,
                    message=message,
                    template_name=template_name,
                    template_data=json.dumps(template_data) if template_data else None,
                    attachments=json.dumps(attachments) if attachments else None,
                    metadata=json.dumps(metadata) if metadata else None,
                    status=NotificationStatus.PENDING
                )
                
                db.add(delivery)
                db.commit()
                db.refresh(delivery)
                
                return delivery.id
                
        except Exception as e:
            logger.error(f"Create delivery record error: {e}")
            return None
    
    async def _send_smtp_email(self, msg: MIMEMultipart, recipients: List[str]) -> bool:
        """Send email via SMTP"""
        
        try:
            # Create SMTP connection
            if self.email_config['use_tls']:
                context = ssl.create_default_context()
                server = smtplib.SMTP(
                    self.email_config['host'], 
                    self.email_config['port']
                )
                server.starttls(context=context)
            else:
                server = smtplib.SMTP_SSL(
                    self.email_config['host'], 
                    self.email_config['port']
                )
            
            # Login if credentials provided
            if self.email_config['username'] and self.email_config['password']:
                server.login(
                    self.email_config['username'], 
                    self.email_config['password']
                )
            
            # Send email
            server.send_message(msg, to_addrs=recipients)
            server.quit()
            
            logger.info(f"Email sent successfully to {recipients}")
            return True
            
        except Exception as e:
            logger.error(f"SMTP send error: {e}")
            return False
    
    async def _render_email_template(
        self, 
        template_name: str, 
        data: Dict[str, Any]
    ) -> tuple[str, str]:
        """Render email template"""
        
        try:
            template = self.templates.get(template_name)
            if not template:
                logger.warning(f"Template {template_name} not found")
                return data.get('message', ''), data.get('html_message', '')
            
            # Render text template
            text_template = jinja2.Template(template.get('text', ''))
            text_content = text_template.render(**data)
            
            # Render HTML template
            html_template = jinja2.Template(template.get('html', ''))
            html_content = html_template.render(**data)
            
            return text_content, html_content
            
        except Exception as e:
            logger.error(f"Template rendering error: {e}")
            return data.get('message', ''), data.get('html_message', '')
    
    async def _add_attachment(self, msg: MIMEMultipart, attachment: Dict[str, Any]):
        """Add attachment to email"""
        
        try:
            filename = attachment.get('filename')
            content = attachment.get('content')
            content_type = attachment.get('content_type', 'application/octet-stream')
            
            if not filename or not content:
                return
            
            part = MIMEBase(*content_type.split('/'))
            part.set_payload(content)
            encoders.encode_base64(part)
            
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {filename}'
            )
            
            msg.attach(part)
            
        except Exception as e:
            logger.error(f"Add attachment error: {e}")
    
    def _load_email_config(self) -> Dict[str, Any]:
        """Load email configuration"""
        
        return {
            'host': settings.SMTP_HOST,
            'port': settings.SMTP_PORT,
            'username': settings.SMTP_USER,
            'password': settings.SMTP_PASSWORD,
            'from_address': settings.SMTP_FROM_ADDRESS,
            'from_name': getattr(settings, 'SMTP_FROM_NAME', 'Enterprise SQL Proxy'),
            'use_tls': settings.SMTP_TLS
        }
    
    def _load_webhook_config(self) -> Dict[str, Any]:
        """Load webhook configuration"""
        
        return {
            'slack_url': settings.SLACK_WEBHOOK_URL,
            'teams_url': getattr(settings, 'TEAMS_WEBHOOK_URL', None),
            'timeout': 30
        }
    
    async def _load_templates(self):
        """Load notification templates"""
        
        try:
            with get_db_session() as db:
                templates = db.query(NotificationTemplate).filter(
                    NotificationTemplate.is_active == True
                ).all()
                
                for template in templates:
                    self.templates[template.name] = {
                        'text': template.text_template,
                        'html': template.html_template,
                        'subject': template.subject_template
                    }
                
                logger.info(f"Loaded {len(self.templates)} notification templates")
                
        except Exception as e:
            logger.error(f"Template loading error: {e}")
    
    async def get_delivery_status(self, delivery_id: int) -> Dict[str, Any]:
        """Get delivery status"""
        
        try:
            with get_db_session() as db:
                delivery = db.query(NotificationDelivery).filter(
                    NotificationDelivery.id == delivery_id
                ).first()
                
                if not delivery:
                    return {"error": "Delivery not found"}
                
                return {
                    "id": delivery.id,
                    "type": delivery.notification_type,
                    "channel": delivery.channel.value,
                    "status": delivery.status.value,
                    "priority": delivery.priority.value,
                    "created_at": delivery.created_at.isoformat(),
                    "sent_at": delivery.sent_at.isoformat() if delivery.sent_at else None,
                    "delivered_at": delivery.delivered_at.isoformat() if delivery.delivered_at else None,
                    "error_message": delivery.error_message
                }
                
        except Exception as e:
            return {"error": str(e)}
    
    async def health_check(self) -> Dict[str, Any]:
        """Service health check"""
        
        try:
            # Test email configuration
            email_config_valid = bool(
                self.email_config['host'] and 
                self.email_config['from_address']
            ) if settings.EMAILS_ENABLED else True
            
            # Test webhook configuration
            webhook_config_valid = bool(
                settings.SLACK_WEBHOOK_URL or 
                getattr(settings, 'TEAMS_WEBHOOK_URL', None)
            )
            
            return {
                "status": "healthy",
                "email_enabled": settings.EMAILS_ENABLED,
                "email_config_valid": email_config_valid,
                "webhook_config_valid": webhook_config_valid,
                "templates_loaded": len(self.templates),
                "queue_size": self.delivery_queue.qsize(),
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
        """Get notification metrics"""
        
        try:
            with get_db_session() as db:
                # Get delivery statistics
                total_deliveries = db.query(NotificationDelivery).count()
                
                sent_deliveries = db.query(NotificationDelivery).filter(
                    NotificationDelivery.status == NotificationStatus.SENT
                ).count()
                
                failed_deliveries = db.query(NotificationDelivery).filter(
                    NotificationDelivery.status == NotificationStatus.FAILED
                ).count()
                
                pending_deliveries = db.query(NotificationDelivery).filter(
                    NotificationDelivery.status == NotificationStatus.PENDING
                ).count()
            
            return {
                "stats": self.stats,
                "database_stats": {
                    "total_deliveries": total_deliveries,
                    "sent_deliveries": sent_deliveries,
                    "failed_deliveries": failed_deliveries,
                    "pending_deliveries": pending_deliveries,
                    "success_rate": (sent_deliveries / total_deliveries * 100) if total_deliveries > 0 else 0
                },
                "configuration": {
                    "email_enabled": settings.EMAILS_ENABLED,
                    "slack_enabled": bool(settings.SLACK_WEBHOOK_URL),
                    "teams_enabled": bool(getattr(settings, 'TEAMS_WEBHOOK_URL', None)),
                    "templates_loaded": len(self.templates)
                },
                "queue_size": self.delivery_queue.qsize(),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def cleanup(self):
        """Cleanup service resources"""
        
        # Wait for queue to empty
        await self.delivery_queue.join()
        
        logger.info("✅ Notification Service cleanup completed")


# Global notification service instance
notification_service = NotificationService()

# Convenience functions
async def send_notification(
    notification_type: str,
    recipients: List[str],
    subject: str,
    message: str,
    channels: List[NotificationChannel] = None,
    priority: NotificationPriority = NotificationPriority.NORMAL
) -> List[int]:
    """Send notification"""
    return await notification_service.send_notification(
        notification_type, recipients, subject, message, channels, priority
    )

async def send_email(
    recipients: List[str],
    subject: str,
    message: str,
    html_message: str = None
) -> bool:
    """Send email"""
    return await notification_service.send_email(
        recipients, subject, message, html_message
    )

async def send_slack_notification(message: str) -> bool:
    """Send Slack notification"""
    return await notification_service.send_slack_notification(message)