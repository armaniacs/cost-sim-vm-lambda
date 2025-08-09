"""
Alerting service package.

Provides comprehensive alerting functionality including:
- Alert models and enums
- Notification handlers
- Correlation and escalation
- Main alerting service
"""

from .correlation import AlertCorrelationEngine
from .escalation import EscalationManager
from .handlers import (
    EmailNotificationHandler,
    NotificationChannelHandler,
    SlackNotificationHandler,
    WebhookNotificationHandler,
)
from .models import Alert, AlertRule, AlertSeverity, AlertStatus, NotificationChannel
from .service import AlertingService

__all__ = [
    "AlertSeverity",
    "AlertStatus",
    "NotificationChannel",
    "AlertRule",
    "Alert",
    "NotificationChannelHandler",
    "EmailNotificationHandler",
    "SlackNotificationHandler",
    "WebhookNotificationHandler",
    "AlertCorrelationEngine",
    "EscalationManager",
    "AlertingService",
]
