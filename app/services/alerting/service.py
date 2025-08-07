"""
Main alerting service that orchestrates all alerting components.
"""

import json
import logging
import threading
import time
import uuid
from collections import deque
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from flask import Flask, current_app

from app.extensions import get_redis_client
from .models import Alert, AlertRule, AlertSeverity, AlertStatus, NotificationChannel
from .handlers import NOTIFICATION_HANDLERS
from .correlation import AlertCorrelationEngine
from .escalation import EscalationManager

logger = logging.getLogger(__name__)


class AlertingService:
    """Main alerting service that orchestrates all alerting components."""
    
    def __init__(self, app: Flask = None):
        self.app = app
        self.alert_rules = {}
        self.active_alerts = {}
        self.alert_history = deque(maxlen=10000)
        self.notification_handlers = NOTIFICATION_HANDLERS.copy()
        self.correlation_engine = AlertCorrelationEngine()
        self.escalation_manager = EscalationManager()
        self.lock = threading.Lock()
        self.background_workers = []
        self.shutdown_event = threading.Event()
        
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize alerting service with Flask app."""
        self.app = app
        
        # Load configuration
        self._load_configuration()
        
        # Start background workers
        self._start_background_workers()
        
        # Store reference in app
        app.alerting_service = self
        logger.info("Alerting service initialized")
    
    def add_alert_rule(self, rule: AlertRule):
        """Add an alert rule."""
        with self.lock:
            self.alert_rules[rule.id] = rule
            logger.info(f"Added alert rule: {rule.name}")
    
    def remove_alert_rule(self, rule_id: str) -> bool:
        """Remove an alert rule."""
        with self.lock:
            if rule_id in self.alert_rules:
                rule = self.alert_rules.pop(rule_id)
                logger.info(f"Removed alert rule: {rule.name}")
                return True
            return False
    
    def get_alert_rules(self) -> List[AlertRule]:
        """Get all alert rules."""
        with self.lock:
            return list(self.alert_rules.values())
    
    def evaluate_metric(self, metric_name: str, value: float, timestamp: Optional[datetime] = None, tags: Optional[Dict[str, str]] = None):
        """Evaluate a metric against all relevant alert rules."""
        if timestamp is None:
            timestamp = datetime.now()
        if tags is None:
            tags = {}
        
        triggered_alerts = []
        
        with self.lock:
            for rule in self.alert_rules.values():
                if not rule.enabled or rule.metric_name != metric_name:
                    continue
                
                # Check if rule condition is met
                if rule.evaluate(value):
                    alert = self._create_alert(rule, value, timestamp, tags)
                    if alert:
                        triggered_alerts.append(alert)
        
        # Process triggered alerts
        for alert in triggered_alerts:
            self._process_alert(alert)
        
        return triggered_alerts
    
    def get_active_alerts(self, severity: Optional[AlertSeverity] = None, tags: Optional[Dict[str, str]] = None) -> List[Alert]:
        """Get active alerts with optional filtering."""
        with self.lock:
            alerts = list(self.active_alerts.values())
        
        # Apply filters
        if severity:
            alerts = [alert for alert in alerts if alert.severity == severity]
        
        if tags:
            alerts = [alert for alert in alerts if all(
                alert.tags.get(k) == v for k, v in tags.items()
            )]
        
        # Filter out suppressed alerts
        alerts = [alert for alert in alerts if not alert.is_suppressed()]
        
        return alerts
    
    def acknowledge_alert(self, alert_id: str, user: str) -> bool:
        """Acknowledge an alert."""
        with self.lock:
            if alert_id in self.active_alerts:
                alert = self.active_alerts[alert_id]
                alert.acknowledge(user)
                self.escalation_manager.stop_escalation(alert_id)
                logger.info(f"Alert {alert_id} acknowledged by {user}")
                return True
            return False
    
    def resolve_alert(self, alert_id: str, user: Optional[str] = None) -> bool:
        """Resolve an alert."""
        with self.lock:
            if alert_id in self.active_alerts:
                alert = self.active_alerts.pop(alert_id)
                alert.resolve(user)
                self.alert_history.append(alert)
                self.escalation_manager.stop_escalation(alert_id)
                logger.info(f"Alert {alert_id} resolved by {user or 'system'}")
                return True
            return False
    
    def suppress_alert(self, alert_id: str, duration_minutes: int, user: str) -> bool:
        """Suppress an alert for a specified duration."""
        with self.lock:
            if alert_id in self.active_alerts:
                alert = self.active_alerts[alert_id]
                until = datetime.now() + timedelta(minutes=duration_minutes)
                alert.suppress(until, user)
                self.escalation_manager.stop_escalation(alert_id)
                logger.info(f"Alert {alert_id} suppressed by {user} for {duration_minutes} minutes")
                return True
            return False
    
    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """Get alert history."""
        return list(self.alert_history)[-limit:]
    
    def _create_alert(self, rule: AlertRule, value: float, timestamp: datetime, tags: Dict[str, str]) -> Optional[Alert]:
        """Create a new alert from a triggered rule."""
        # Check for existing active alert with same rule
        existing_alert = None
        for alert in self.active_alerts.values():
            if (alert.rule_id == rule.id and 
                alert.is_active() and 
                not alert.is_suppressed()):
                existing_alert = alert
                break
        
        if existing_alert:
            # Update existing alert
            existing_alert.metric_value = value
            existing_alert.updated_at = timestamp
            existing_alert.notification_count += 1
            return None  # Don't create duplicate
        
        # Create new alert
        alert = Alert(
            id=str(uuid.uuid4()),
            rule_id=rule.id,
            rule_name=rule.name,
            severity=rule.severity,
            status=AlertStatus.ACTIVE,
            message=f"{rule.name}: {rule.metric_name} = {value} {rule.condition} {rule.threshold}",
            description=rule.description,
            metric_name=rule.metric_name,
            metric_value=value,
            threshold=rule.threshold,
            condition=rule.condition,
            tags={**rule.tags, **tags},
            created_at=timestamp
        )
        
        return alert
    
    def _process_alert(self, alert: Alert):
        """Process a new alert."""
        with self.lock:
            self.active_alerts[alert.id] = alert
        
        # Correlation
        correlation_group = self.correlation_engine.correlate_alert(alert)
        
        # Send notifications
        rule = self.alert_rules.get(alert.rule_id)
        if rule:
            self._send_notifications(alert, rule)
        
        # Start escalation if configured
        if rule and rule.escalation_rules:
            for escalation_rule in rule.escalation_rules:
                policy_id = escalation_rule.get('policy_id')
                if policy_id:
                    self.escalation_manager.start_escalation(alert, policy_id)
        
        logger.info(f"Processed new alert: {alert.id} ({alert.rule_name})")
    
    def _send_notifications(self, alert: Alert, rule: AlertRule):
        """Send notifications for an alert."""
        for channel in rule.notification_channels:
            try:
                handler = self.notification_handlers.get(channel.value)
                if handler:
                    # Get channel configuration
                    config = self._get_notification_config(channel)
                    success = handler.send_notification(alert, config)
                    
                    if success:
                        alert.notification_count += 1
                        logger.debug(f"Notification sent via {channel.value} for alert {alert.id}")
                    else:
                        logger.warning(f"Failed to send notification via {channel.value} for alert {alert.id}")
                else:
                    logger.warning(f"No handler found for notification channel: {channel.value}")
            except Exception as e:
                logger.error(f"Error sending notification via {channel.value}: {e}")
    
    def _get_notification_config(self, channel: NotificationChannel) -> Dict[str, Any]:
        """Get configuration for a notification channel."""
        if self.app:
            return self.app.config.get(f'ALERTING_{channel.value.upper()}', {})
        return {}
    
    def _load_configuration(self):
        """Load alerting configuration."""
        self._load_default_alert_rules()
        self._load_escalation_policies()
        self._load_correlation_rules()
    
    def _load_default_alert_rules(self):
        """Load default alert rules."""
        default_rules = [
            AlertRule(
                id="high_response_time",
                name="High Response Time",
                description="Average response time is above threshold",
                metric_name="request.duration.avg",
                condition=">=",
                threshold=5.0,
                severity=AlertSeverity.HIGH,
                evaluation_period=300,
                notification_channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK],
                escalation_rules=[],
                tags={"category": "performance"}
            ),
            AlertRule(
                id="high_error_rate",
                name="High Error Rate",
                description="Error rate is above threshold",
                metric_name="request.error.rate",
                condition=">=",
                threshold=5.0,
                severity=AlertSeverity.CRITICAL,
                evaluation_period=300,
                notification_channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK, NotificationChannel.WEBHOOK],
                escalation_rules=[{"policy_id": "critical_escalation"}],
                tags={"category": "reliability"}
            ),
            AlertRule(
                id="high_cpu_usage",
                name="High CPU Usage",
                description="CPU usage is above threshold",
                metric_name="system.cpu.usage",
                condition=">=",
                threshold=80.0,
                severity=AlertSeverity.MEDIUM,
                evaluation_period=600,
                notification_channels=[NotificationChannel.EMAIL],
                escalation_rules=[],
                tags={"category": "infrastructure"}
            )
        ]
        
        for rule in default_rules:
            self.add_alert_rule(rule)
    
    def _load_escalation_policies(self):
        """Load escalation policies."""
        policies = {
            "critical_escalation": {
                "levels": [
                    {
                        "delay_minutes": 5,
                        "actions": [
                            {"type": "notify", "recipients": ["oncall@company.com"], "channels": ["email", "slack"]}
                        ]
                    },
                    {
                        "delay_minutes": 15,
                        "actions": [
                            {"type": "page", "on_call_group": "engineering", "method": "sms"},
                            {"type": "create_ticket", "system": "jira", "priority": "high"}
                        ]
                    },
                    {
                        "delay_minutes": 30,
                        "actions": [
                            {"type": "notify", "recipients": ["management@company.com"], "channels": ["email"]},
                            {"type": "webhook", "url": "https://hooks.company.com/escalation"}
                        ]
                    }
                ]
            }
        }
        
        for policy_id, policy in policies.items():
            self.escalation_manager.add_escalation_policy(policy_id, policy)
    
    def _load_correlation_rules(self):
        """Load correlation rules."""
        correlation_rules = [
            {
                "name": "Performance Issues",
                "tags": {"category": "performance"},
                "group_by": ["metric_name", "severity"]
            },
            {
                "name": "Infrastructure Alerts",
                "tags": {"category": "infrastructure"},
                "group_by": ["severity"]
            }
        ]
        
        for rule in correlation_rules:
            self.correlation_engine.add_correlation_rule(rule)
    
    def _start_background_workers(self):
        """Start background worker threads."""
        # Escalation processor
        escalation_worker = threading.Thread(target=self._escalation_worker, daemon=True)
        escalation_worker.start()
        self.background_workers.append(escalation_worker)
        
        # Cleanup worker
        cleanup_worker = threading.Thread(target=self._cleanup_worker, daemon=True)
        cleanup_worker.start()
        self.background_workers.append(cleanup_worker)
        
        logger.info("Started background workers")
    
    def _escalation_worker(self):
        """Background worker for processing escalations."""
        while not self.shutdown_event.is_set():
            try:
                escalations = self.escalation_manager.check_escalations()
                for escalation_data in escalations:
                    self.escalation_manager.process_escalation(escalation_data)
                
                time.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Error in escalation worker: {e}")
                time.sleep(60)  # Wait longer on error
    
    def _cleanup_worker(self):
        """Background worker for cleanup tasks."""
        while not self.shutdown_event.is_set():
            try:
                # Clean up resolved alerts from correlation groups
                self.correlation_engine.cleanup_resolved_alerts()
                
                # Clean up completed escalations
                self.escalation_manager.cleanup_completed_escalations()
                
                # Clean up old alert history
                self._cleanup_alert_history()
                
                time.sleep(300)  # Cleanup every 5 minutes
            except Exception as e:
                logger.error(f"Error in cleanup worker: {e}")
                time.sleep(600)  # Wait longer on error
    
    def _cleanup_alert_history(self):
        """Clean up old alert history."""
        if len(self.alert_history) >= self.alert_history.maxlen:
            logger.debug("Alert history at capacity, oldest entries will be automatically removed")
    
    def shutdown(self):
        """Shutdown the alerting service."""
        logger.info("Shutting down alerting service")
        self.shutdown_event.set()
        
        # Wait for background workers to finish
        for worker in self.background_workers:
            worker.join(timeout=5)
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Get alerting service statistics."""
        with self.lock:
            active_alerts_by_severity = {}
            for alert in self.active_alerts.values():
                severity = alert.severity.value
                active_alerts_by_severity[severity] = active_alerts_by_severity.get(severity, 0) + 1
        
        stats = {
            'alert_rules': len(self.alert_rules),
            'active_alerts': len(self.active_alerts),
            'active_alerts_by_severity': active_alerts_by_severity,
            'alert_history_count': len(self.alert_history),
            'notification_handlers': len(self.notification_handlers)
        }
        
        # Add correlation stats
        stats.update(self.correlation_engine.get_correlation_stats())
        
        # Add escalation stats
        stats.update(self.escalation_manager.get_escalation_stats())
        
        return stats