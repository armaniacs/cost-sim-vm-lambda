"""
Notification handlers for different channels.
"""

import json
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Any, Dict

import requests
from jinja2 import Template

from .models import Alert

logger = logging.getLogger(__name__)


class NotificationChannelHandler:
    """Base class for notification channel handlers."""
    
    def send_notification(self, alert: Alert, config: Dict[str, Any]) -> bool:
        """Send notification for an alert."""
        # Default implementation - subclasses should override
        logger.info(f"Sending notification for alert: {alert.rule_name}")
        return True


class EmailNotificationHandler(NotificationChannelHandler):
    """Email notification handler."""
    
    def __init__(self):
        self.template = Template("""
        <html>
        <body>
            <h2>{{ alert.severity.value|upper }} Alert: {{ alert.rule_name }}</h2>
            <p><strong>Message:</strong> {{ alert.message }}</p>
            <p><strong>Description:</strong> {{ alert.description }}</p>
            <p><strong>Current Value:</strong> {{ alert.metric_value }}</p>
            <p><strong>Threshold:</strong> {{ alert.condition }} {{ alert.threshold }}</p>
            <p><strong>Time:</strong> {{ alert.created_at }}</p>
            <p><strong>Status:</strong> {{ alert.status.value }}</p>
            
            {% if alert.tags %}
            <h3>Tags:</h3>
            <ul>
            {% for key, value in alert.tags.items() %}
                <li>{{ key }}: {{ value }}</li>
            {% endfor %}
            </ul>
            {% endif %}
        </body>
        </html>
        """)
    
    def send_notification(self, alert: Alert, config: Dict[str, Any]) -> bool:
        """Send email notification."""
        try:
            smtp_server = config.get('smtp_server', 'localhost')
            smtp_port = config.get('smtp_port', 587)
            username = config.get('username')
            password = config.get('password')
            from_email = config.get('from_email')
            to_emails = config.get('to_emails', [])
            
            if not to_emails:
                logger.warning("No recipient emails configured")
                return False
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = f"[{alert.severity.value.upper()}] {alert.rule_name}"
            
            # Add body
            body = self.template.render(alert=alert)
            msg.attach(MIMEText(body, 'html'))
            
            # Send email
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            if username and password:
                server.login(username, password)
            
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email notification sent for alert {alert.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            return False


class SlackNotificationHandler(NotificationChannelHandler):
    """Slack notification handler."""
    
    def send_notification(self, alert: Alert, config: Dict[str, Any]) -> bool:
        """Send Slack notification."""
        try:
            webhook_url = config.get('webhook_url')
            if not webhook_url:
                logger.warning("No Slack webhook URL configured")
                return False
            
            # Create Slack message
            color_map = {
                'low': '#36a64f',      # Green
                'medium': '#ff9500',   # Orange  
                'high': '#ff4444',     # Red
                'critical': '#800080'  # Purple
            }
            
            color = color_map.get(alert.severity.value, '#808080')
            
            payload = {
                "username": "Cost Management Alert",
                "icon_emoji": ":warning:",
                "attachments": [
                    {
                        "color": color,
                        "title": f"{alert.severity.value.upper()} Alert: {alert.rule_name}",
                        "fields": [
                            {
                                "title": "Message",
                                "value": alert.message,
                                "short": False
                            },
                            {
                                "title": "Current Value",
                                "value": str(alert.metric_value),
                                "short": True
                            },
                            {
                                "title": "Threshold",
                                "value": f"{alert.condition} {alert.threshold}",
                                "short": True
                            },
                            {
                                "title": "Status",
                                "value": alert.status.value,
                                "short": True
                            },
                            {
                                "title": "Time",
                                "value": alert.created_at.strftime('%Y-%m-%d %H:%M:%S UTC'),
                                "short": True
                            }
                        ],
                        "footer": "Cost Management Platform",
                        "ts": int(alert.created_at.timestamp())
                    }
                ]
            }
            
            # Add tags if present
            if alert.tags:
                tag_text = ", ".join([f"{k}:{v}" for k, v in alert.tags.items()])
                payload["attachments"][0]["fields"].append({
                    "title": "Tags",
                    "value": tag_text,
                    "short": False
                })
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
            logger.info(f"Slack notification sent for alert {alert.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return False


class WebhookNotificationHandler(NotificationChannelHandler):
    """Generic webhook notification handler."""
    
    def send_notification(self, alert: Alert, config: Dict[str, Any]) -> bool:
        """Send webhook notification."""
        try:
            webhook_url = config.get('url')
            if not webhook_url:
                logger.warning("No webhook URL configured")
                return False
            
            headers = config.get('headers', {})
            headers.setdefault('Content-Type', 'application/json')
            
            # Create payload
            payload = {
                "alert": alert.to_dict(),
                "timestamp": alert.created_at.isoformat(),
                "event_type": "alert_triggered"
            }
            
            # Add custom fields if configured
            custom_payload = config.get('custom_payload', {})
            payload.update(custom_payload)
            
            response = requests.post(
                webhook_url, 
                json=payload, 
                headers=headers,
                timeout=config.get('timeout', 10)
            )
            response.raise_for_status()
            
            logger.info(f"Webhook notification sent for alert {alert.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send webhook notification: {e}")
            return False


# Handler registry
NOTIFICATION_HANDLERS = {
    'email': EmailNotificationHandler(),
    'slack': SlackNotificationHandler(), 
    'webhook': WebhookNotificationHandler()
}