"""
Alerting service package.

Provides comprehensive alerting functionality including:
- Alert models and enums
- Notification handlers
- Correlation and escalation
- Main alerting service
"""

from .models import AlertSeverity, AlertStatus, NotificationChannel, AlertRule, Alert
from .handlers import NotificationChannelHandler, EmailNotificationHandler, SlackNotificationHandler, WebhookNotificationHandler
from .correlation import AlertCorrelationEngine
from .escalation import EscalationManager
from .service import AlertingService

__all__ = [
    'AlertSeverity', 'AlertStatus', 'NotificationChannel', 'AlertRule', 'Alert',
    'NotificationChannelHandler', 'EmailNotificationHandler', 'SlackNotificationHandler', 'WebhookNotificationHandler',
    'AlertCorrelationEngine', 'EscalationManager', 'AlertingService'
]