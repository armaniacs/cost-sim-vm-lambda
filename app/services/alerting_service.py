"""
Comprehensive Alerting Service for Enterprise Cost Management Platform.

This service provides:
- Real-time alert generation based on metrics and logs
- Alert routing and escalation policies
- Multiple notification channels (email, Slack, webhook)
- Alert correlation and deduplication
- Alert history and management
- Integration with APM and logging systems
"""

import logging
import smtplib
import threading
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import Enum
from typing import Any, Dict, List, Optional

import requests
from flask import Flask
from jinja2 import Template

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """Alert status values."""

    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


class NotificationChannel(Enum):
    """Notification channel types."""

    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    SMS = "sms"


@dataclass
class AlertRule:
    """Defines an alert rule."""

    id: str
    name: str
    description: str
    metric_name: str
    condition: str  # e.g., ">=", "<=", "==", "!="
    threshold: float
    severity: AlertSeverity
    evaluation_period: int  # seconds
    notification_channels: List[NotificationChannel]
    escalation_rules: List[Dict[str, Any]]
    tags: Dict[str, str]
    enabled: bool = True

    def evaluate(self, value: float) -> bool:
        """Evaluate if the rule condition is met."""
        if self.condition == ">=":
            return value >= self.threshold
        elif self.condition == "<=":
            return value <= self.threshold
        elif self.condition == "==":
            return value == self.threshold
        elif self.condition == "!=":
            return value != self.threshold
        elif self.condition == ">":
            return value > self.threshold
        elif self.condition == "<":
            return value < self.threshold
        else:
            return False


@dataclass
class Alert:
    """Represents an active alert."""

    id: str
    rule_id: str
    name: str
    description: str
    severity: AlertSeverity
    status: AlertStatus
    value: float
    threshold: float
    condition: str
    created_at: datetime
    updated_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    tags: Dict[str, str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = {}
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary."""
        return {
            "id": self.id,
            "rule_id": self.rule_id,
            "name": self.name,
            "description": self.description,
            "severity": self.severity.value,
            "status": self.status.value,
            "value": self.value,
            "threshold": self.threshold,
            "condition": self.condition,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "acknowledged_at": (
                self.acknowledged_at.isoformat() if self.acknowledged_at else None
            ),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "tags": self.tags,
            "metadata": self.metadata,
        }


class NotificationChannelHandler:
    """Base class for notification channel handlers."""

    def send_notification(self, alert: Alert, config: Dict[str, Any]) -> bool:
        """Send notification for an alert."""
        # Default implementation - subclasses should override
        print(f"Sending notification for alert: {alert.name}")
        return True


class EmailNotificationHandler(NotificationChannelHandler):
    """Email notification handler."""

    def __init__(self):
        self.template = Template(
            """
        <html>
        <body>
            <h2>{{ alert.severity.value|upper }} Alert: {{ alert.name }}</h2>
            <p><strong>Description:</strong> {{ alert.description }}</p>
            <p><strong>Current Value:</strong> {{ alert.value }}</p>
            <p><strong>Threshold:</strong> {{ alert.condition }}
                {{ alert.threshold }}</p>
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

            {% if alert.metadata %}
            <h3>Additional Information:</h3>
            <ul>
            {% for key, value in alert.metadata.items() %}
                <li>{{ key }}: {{ value }}</li>
            {% endfor %}
            </ul>
            {% endif %}
        </body>
        </html>
        """
        )

    def send_notification(self, alert: Alert, config: Dict[str, Any]) -> bool:
        """Send email notification."""
        try:
            smtp_server = config.get("smtp_server", "localhost")
            smtp_port = config.get("smtp_port", 587)
            username = config.get("username")
            password = config.get("password")
            from_email = config.get("from_email")
            to_emails = config.get("to_emails", [])

            if not to_emails:
                return False

            # Create message
            msg = MIMEMultipart()
            msg["From"] = from_email
            msg["To"] = ", ".join(to_emails)
            msg["Subject"] = f"[{alert.severity.value.upper()}] {alert.name}"

            # Add body
            body = self.template.render(alert=alert)
            msg.attach(MIMEText(body, "html"))

            # Send email
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            if username and password:
                server.login(username, password)

            server.send_message(msg)
            server.quit()

            return True

        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            return False


class SlackNotificationHandler(NotificationChannelHandler):
    """Slack notification handler."""

    def send_notification(self, alert: Alert, config: Dict[str, Any]) -> bool:
        """Send Slack notification."""
        try:
            webhook_url = config.get("webhook_url")
            if not webhook_url:
                return False

            # Color based on severity
            color_map = {
                AlertSeverity.LOW: "#36a64f",
                AlertSeverity.MEDIUM: "#ff9500",
                AlertSeverity.HIGH: "#ff0000",
                AlertSeverity.CRITICAL: "#8b0000",
            }

            # Create Slack message
            payload = {
                "text": f"Alert: {alert.name}",
                "attachments": [
                    {
                        "color": color_map.get(alert.severity, "#36a64f"),
                        "fields": [
                            {
                                "title": "Severity",
                                "value": alert.severity.value.upper(),
                                "short": True,
                            },
                            {
                                "title": "Status",
                                "value": alert.status.value,
                                "short": True,
                            },
                            {
                                "title": "Value",
                                "value": (
                                    f"{alert.value} {alert.condition} {alert.threshold}"
                                ),
                                "short": True,
                            },
                            {
                                "title": "Time",
                                "value": alert.created_at.isoformat(),
                                "short": True,
                            },
                        ],
                        "text": alert.description,
                    }
                ],
            }

            # Send request
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()

            return True

        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return False


class WebhookNotificationHandler(NotificationChannelHandler):
    """Webhook notification handler."""

    def send_notification(self, alert: Alert, config: Dict[str, Any]) -> bool:
        """Send webhook notification."""
        try:
            url = config.get("url")
            if not url:
                return False

            headers = config.get("headers", {})
            method = config.get("method", "POST")

            # Create payload
            payload = {
                "alert": alert.to_dict(),
                "timestamp": datetime.utcnow().isoformat(),
                "event": "alert_triggered",
            }

            # Send request
            if method.upper() == "POST":
                response = requests.post(url, json=payload, headers=headers, timeout=10)
            elif method.upper() == "PUT":
                response = requests.put(url, json=payload, headers=headers, timeout=10)
            else:
                response = requests.get(
                    url, params=payload, headers=headers, timeout=10
                )

            response.raise_for_status()
            return True

        except Exception as e:
            logger.error(f"Failed to send webhook notification: {e}")
            return False


class AlertCorrelationEngine:
    """Engine for correlating and deduplicating alerts."""

    def __init__(self):
        self.correlation_rules = []
        self.alert_groups = defaultdict(list)
        self.lock = threading.Lock()

    def add_correlation_rule(self, rule: Dict[str, Any]):
        """Add a correlation rule."""
        with self.lock:
            self.correlation_rules.append(rule)

    def correlate_alert(self, alert: Alert) -> Optional[str]:
        """Correlate an alert with existing alerts."""
        with self.lock:
            for rule in self.correlation_rules:
                if self._matches_correlation_rule(alert, rule):
                    group_key = self._generate_group_key(alert, rule)
                    self.alert_groups[group_key].append(alert)
                    return group_key

        return None

    def _matches_correlation_rule(self, alert: Alert, rule: Dict[str, Any]) -> bool:
        """Check if alert matches a correlation rule."""
        if "tags" in rule:
            for key, value in rule["tags"].items():
                if alert.tags.get(key) != value:
                    return False

        if "severity" in rule:
            if alert.severity != AlertSeverity(rule["severity"]):
                return False

        if "name_pattern" in rule:
            import re

            if not re.match(rule["name_pattern"], alert.name):
                return False

        return True

    def _generate_group_key(self, alert: Alert, rule: Dict[str, Any]) -> str:
        """Generate a group key for correlated alerts."""
        key_parts = []

        if "group_by" in rule:
            for field in rule["group_by"]:
                if field == "tags":
                    key_parts.append(str(sorted(alert.tags.items())))
                elif field == "severity":
                    key_parts.append(alert.severity.value)
                elif field == "name":
                    key_parts.append(alert.name)

        return ":".join(key_parts)


class EscalationManager:
    """Manages alert escalation policies."""

    def __init__(self):
        self.escalation_policies = {}
        self.active_escalations = {}
        self.lock = threading.Lock()

    def add_escalation_policy(self, policy_id: str, policy: Dict[str, Any]):
        """Add an escalation policy."""
        with self.lock:
            self.escalation_policies[policy_id] = policy

    def start_escalation(self, alert: Alert, policy_id: str):
        """Start escalation for an alert."""
        with self.lock:
            if policy_id not in self.escalation_policies:
                return

            policy = self.escalation_policies[policy_id]
            escalation_data = {
                "alert": alert,
                "policy": policy,
                "current_level": 0,
                "started_at": datetime.utcnow(),
                "next_escalation_at": datetime.utcnow()
                + timedelta(minutes=policy["levels"][0]["delay_minutes"]),
            }

            self.active_escalations[alert.id] = escalation_data

    def check_escalations(self) -> List[Dict[str, Any]]:
        """Check for alerts that need escalation."""
        escalations_to_process = []

        with self.lock:
            current_time = datetime.utcnow()

            for alert_id, escalation_data in self.active_escalations.items():
                if current_time >= escalation_data["next_escalation_at"]:
                    escalations_to_process.append(escalation_data)

        return escalations_to_process

    def process_escalation(self, escalation_data: Dict[str, Any]):
        """Process an escalation step."""
        escalation_data["alert"]
        policy = escalation_data["policy"]
        current_level = escalation_data["current_level"]

        if current_level >= len(policy["levels"]):
            return

        level_config = policy["levels"][current_level]

        # Process escalation actions
        for action in level_config.get("actions", []):
            if action["type"] == "notify":
                # Send notification to escalated recipients
                pass
            elif action["type"] == "create_ticket":
                # Create support ticket
                pass
            elif action["type"] == "page":
                # Page on-call person
                pass

        # Schedule next escalation
        escalation_data["current_level"] += 1
        if escalation_data["current_level"] < len(policy["levels"]):
            next_level = policy["levels"][escalation_data["current_level"]]
            escalation_data["next_escalation_at"] = datetime.utcnow() + timedelta(
                minutes=next_level["delay_minutes"]
            )

    def stop_escalation(self, alert_id: str):
        """Stop escalation for an alert."""
        with self.lock:
            if alert_id in self.active_escalations:
                del self.active_escalations[alert_id]


class AlertingService:
    """Main alerting service that orchestrates all alerting components."""

    def __init__(self, app: Flask = None):
        self.app = app
        self.alert_rules = {}
        self.active_alerts = {}
        self.alert_history = deque(maxlen=10000)
        self.notification_handlers = {
            NotificationChannel.EMAIL: EmailNotificationHandler(),
            NotificationChannel.SLACK: SlackNotificationHandler(),
            NotificationChannel.WEBHOOK: WebhookNotificationHandler(),
        }
        self.correlation_engine = AlertCorrelationEngine()
        self.escalation_manager = EscalationManager()
        self.lock = threading.Lock()

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

    def _load_configuration(self):
        """Load alerting configuration."""
        # Load default alert rules
        self._load_default_alert_rules()

        # Load escalation policies
        self._load_escalation_policies()

        # Load correlation rules
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
                notification_channels=[
                    NotificationChannel.EMAIL,
                    NotificationChannel.SLACK,
                ],
                escalation_rules=[],
                tags={"category": "performance"},
            ),
            AlertRule(
                id="high_error_rate",
                name="High Error Rate",
                description="Error rate is above threshold",
                metric_name="request.error_rate",
                condition=">=",
                threshold=0.05,
                severity=AlertSeverity.CRITICAL,
                evaluation_period=180,
                notification_channels=[
                    NotificationChannel.EMAIL,
                    NotificationChannel.SLACK,
                ],
                escalation_rules=[],
                tags={"category": "availability"},
            ),
            AlertRule(
                id="low_cache_hit_ratio",
                name="Low Cache Hit Ratio",
                description="Cache hit ratio is below threshold",
                metric_name="cache.hit_ratio",
                condition="<=",
                threshold=0.8,
                severity=AlertSeverity.MEDIUM,
                evaluation_period=600,
                notification_channels=[NotificationChannel.EMAIL],
                escalation_rules=[],
                tags={"category": "performance"},
            ),
            AlertRule(
                id="high_cpu_usage",
                name="High CPU Usage",
                description="CPU usage is above threshold",
                metric_name="system.cpu_usage",
                condition=">=",
                threshold=80.0,
                severity=AlertSeverity.HIGH,
                evaluation_period=300,
                notification_channels=[
                    NotificationChannel.EMAIL,
                    NotificationChannel.SLACK,
                ],
                escalation_rules=[],
                tags={"category": "system"},
            ),
            AlertRule(
                id="high_memory_usage",
                name="High Memory Usage",
                description="Memory usage is above threshold",
                metric_name="system.memory_usage",
                condition=">=",
                threshold=85.0,
                severity=AlertSeverity.HIGH,
                evaluation_period=300,
                notification_channels=[
                    NotificationChannel.EMAIL,
                    NotificationChannel.SLACK,
                ],
                escalation_rules=[],
                tags={"category": "system"},
            ),
        ]

        for rule in default_rules:
            self.alert_rules[rule.id] = rule

    def _load_escalation_policies(self):
        """Load escalation policies."""
        escalation_policies = {
            "standard": {
                "levels": [
                    {
                        "delay_minutes": 15,
                        "actions": [
                            {"type": "notify", "recipients": ["team@company.com"]}
                        ],
                    },
                    {
                        "delay_minutes": 30,
                        "actions": [
                            {"type": "notify", "recipients": ["manager@company.com"]},
                            {"type": "create_ticket", "system": "jira"},
                        ],
                    },
                    {
                        "delay_minutes": 60,
                        "actions": [
                            {"type": "page", "recipient": "oncall@company.com"}
                        ],
                    },
                ]
            }
        }

        for policy_id, policy in escalation_policies.items():
            self.escalation_manager.add_escalation_policy(policy_id, policy)

    def _load_correlation_rules(self):
        """Load correlation rules."""
        correlation_rules = [
            {
                "name": "performance_issues",
                "tags": {"category": "performance"},
                "group_by": ["severity", "tags"],
                "time_window": 300,  # 5 minutes
            },
            {
                "name": "system_alerts",
                "tags": {"category": "system"},
                "group_by": ["severity"],
                "time_window": 180,  # 3 minutes
            },
        ]

        for rule in correlation_rules:
            self.correlation_engine.add_correlation_rule(rule)

    def _start_background_workers(self):
        """Start background worker threads."""

        # Alert evaluation worker
        def alert_worker():
            while True:
                try:
                    self._evaluate_alert_rules()
                    time.sleep(30)  # Check every 30 seconds
                except Exception as e:
                    logger.error(f"Error in alert worker: {e}")
                    time.sleep(60)

        # Escalation worker
        def escalation_worker():
            while True:
                try:
                    self._process_escalations()
                    time.sleep(60)  # Check every minute
                except Exception as e:
                    logger.error(f"Error in escalation worker: {e}")
                    time.sleep(60)

        alert_thread = threading.Thread(target=alert_worker, daemon=True)
        escalation_thread = threading.Thread(target=escalation_worker, daemon=True)

        alert_thread.start()
        escalation_thread.start()

    def _evaluate_alert_rules(self):
        """Evaluate all alert rules."""
        for rule in self.alert_rules.values():
            if not rule.enabled:
                continue

            try:
                # Get metric value
                metric_value = self._get_metric_value(rule.metric_name)

                if metric_value is not None:
                    # Evaluate rule
                    if rule.evaluate(metric_value):
                        self._trigger_alert(rule, metric_value)
                    else:
                        self._resolve_alert(rule.id)
            except Exception as e:
                logger.error(f"Error evaluating rule {rule.id}: {e}")

    def _get_metric_value(self, metric_name: str) -> Optional[float]:
        """Get current metric value."""
        # This would integrate with your metrics collection system
        # For now, we'll get it from the performance monitor
        try:
            from app.services.performance_monitor import performance_monitor

            if metric_name == "request.duration.avg":
                return performance_monitor.metrics.get_average_response_time()
            elif metric_name == "request.error_rate":
                return performance_monitor.metrics.get_error_rate()
            elif metric_name == "cache.hit_ratio":
                return performance_monitor.metrics.get_cache_hit_ratio()
            elif metric_name == "system.cpu_usage":
                return performance_monitor.system_monitor.get_cpu_usage()
            elif metric_name == "system.memory_usage":
                memory_info = performance_monitor.system_monitor.get_memory_usage()
                return memory_info["percentage"]

        except Exception as e:
            logger.error(f"Error getting metric value for {metric_name}: {e}")

        return None

    def _trigger_alert(self, rule: AlertRule, value: float):
        """Trigger an alert."""
        with self.lock:
            # Check if alert already exists
            if rule.id in self.active_alerts:
                # Update existing alert
                alert = self.active_alerts[rule.id]
                alert.value = value
                alert.updated_at = datetime.utcnow()
                return

            # Create new alert
            alert = Alert(
                id=str(uuid.uuid4()),
                rule_id=rule.id,
                name=rule.name,
                description=rule.description,
                severity=rule.severity,
                status=AlertStatus.ACTIVE,
                value=value,
                threshold=rule.threshold,
                condition=rule.condition,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                tags=rule.tags.copy(),
            )

            self.active_alerts[rule.id] = alert
            self.alert_history.append(alert)

            # Correlate alert
            correlation_group = self.correlation_engine.correlate_alert(alert)
            if correlation_group:
                alert.tags["correlation_group"] = correlation_group

            # Send notifications
            self._send_notifications(alert, rule)

            # Start escalation
            if rule.escalation_rules:
                self.escalation_manager.start_escalation(alert, "standard")

            logger.info(f"Alert triggered: {alert.name} ({alert.severity.value})")

    def _resolve_alert(self, rule_id: str):
        """Resolve an alert."""
        with self.lock:
            if rule_id in self.active_alerts:
                alert = self.active_alerts[rule_id]
                alert.status = AlertStatus.RESOLVED
                alert.resolved_at = datetime.utcnow()
                alert.updated_at = datetime.utcnow()

                # Stop escalation
                self.escalation_manager.stop_escalation(alert.id)

                # Remove from active alerts
                del self.active_alerts[rule_id]

                logger.info(f"Alert resolved: {alert.name}")

    def _send_notifications(self, alert: Alert, rule: AlertRule):
        """Send notifications for an alert."""
        for channel in rule.notification_channels:
            handler = self.notification_handlers.get(channel)
            if handler:
                try:
                    config = self._get_notification_config(channel)
                    success = handler.send_notification(alert, config)
                    if not success:
                        logger.warning(
                            f"Failed to send notification via {channel.value}"
                        )
                except Exception as e:
                    logger.error(f"Error sending notification via {channel.value}: {e}")

    def _get_notification_config(self, channel: NotificationChannel) -> Dict[str, Any]:
        """Get notification configuration for a channel."""
        # This would come from app configuration
        configs = {
            NotificationChannel.EMAIL: {
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "username": "alerts@company.com",
                "password": "app_password",
                "from_email": "alerts@company.com",
                "to_emails": ["team@company.com"],
            },
            NotificationChannel.SLACK: {
                "webhook_url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
            },
            NotificationChannel.WEBHOOK: {
                "url": "https://your-webhook-endpoint.com/alerts",
                "headers": {"Authorization": "Bearer your-token"},
            },
        }

        return configs.get(channel, {})

    def _process_escalations(self):
        """Process pending escalations."""
        escalations = self.escalation_manager.check_escalations()

        for escalation_data in escalations:
            self.escalation_manager.process_escalation(escalation_data)

    def add_alert_rule(self, rule: AlertRule):
        """Add a new alert rule."""
        with self.lock:
            self.alert_rules[rule.id] = rule

    def remove_alert_rule(self, rule_id: str):
        """Remove an alert rule."""
        with self.lock:
            if rule_id in self.alert_rules:
                del self.alert_rules[rule_id]

            # Resolve active alert if exists
            if rule_id in self.active_alerts:
                self._resolve_alert(rule_id)

    def acknowledge_alert(self, alert_id: str, user_id: str = None):
        """Acknowledge an alert."""
        with self.lock:
            for alert in self.active_alerts.values():
                if alert.id == alert_id:
                    alert.status = AlertStatus.ACKNOWLEDGED
                    alert.acknowledged_at = datetime.utcnow()
                    alert.updated_at = datetime.utcnow()

                    if user_id:
                        alert.metadata["acknowledged_by"] = user_id

                    # Stop escalation
                    self.escalation_manager.stop_escalation(alert_id)

                    logger.info(f"Alert acknowledged: {alert.name}")
                    return True

        return False

    def suppress_alert(self, alert_id: str, duration_minutes: int = 60):
        """Suppress an alert for a duration."""
        with self.lock:
            for alert in self.active_alerts.values():
                if alert.id == alert_id:
                    alert.status = AlertStatus.SUPPRESSED
                    alert.updated_at = datetime.utcnow()
                    alert.metadata["suppressed_until"] = (
                        datetime.utcnow() + timedelta(minutes=duration_minutes)
                    ).isoformat()

                    logger.info(f"Alert suppressed: {alert.name}")
                    return True

        return False

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get alerting dashboard data."""
        with self.lock:
            active_alerts_list = [
                alert.to_dict() for alert in self.active_alerts.values()
            ]
            recent_alerts = [
                alert.to_dict() for alert in list(self.alert_history)[-50:]
            ]

            # Alert statistics
            severity_counts = defaultdict(int)
            status_counts = defaultdict(int)

            for alert in self.active_alerts.values():
                severity_counts[alert.severity.value] += 1
                status_counts[alert.status.value] += 1

            return {
                "active_alerts": active_alerts_list,
                "recent_alerts": recent_alerts,
                "statistics": {
                    "total_active": len(self.active_alerts),
                    "severity_breakdown": dict(severity_counts),
                    "status_breakdown": dict(status_counts),
                },
                "alert_rules": {
                    rule_id: {
                        "name": rule.name,
                        "enabled": rule.enabled,
                        "severity": rule.severity.value,
                        "threshold": rule.threshold,
                    }
                    for rule_id, rule in self.alert_rules.items()
                },
                "timestamp": datetime.utcnow().isoformat(),
            }

    def get_alert_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get alert history."""
        with self.lock:
            alerts = list(self.alert_history)[-limit:]
            return [alert.to_dict() for alert in alerts]

    def search_alerts(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search alerts based on criteria."""
        results = []

        with self.lock:
            alerts_to_search = list(self.active_alerts.values()) + list(
                self.alert_history
            )

            for alert in alerts_to_search:
                if self._matches_alert_query(alert, query):
                    results.append(alert.to_dict())

        return results

    def _matches_alert_query(self, alert: Alert, query: Dict[str, Any]) -> bool:
        """Check if alert matches search query."""
        if "severity" in query and alert.severity.value != query["severity"]:
            return False

        if "status" in query and alert.status.value != query["status"]:
            return False

        if "name" in query and query["name"].lower() not in alert.name.lower():
            return False

        if "tags" in query:
            for key, value in query["tags"].items():
                if alert.tags.get(key) != value:
                    return False

        if "start_time" in query:
            start_time = datetime.fromisoformat(query["start_time"])
            if alert.created_at < start_time:
                return False

        if "end_time" in query:
            end_time = datetime.fromisoformat(query["end_time"])
            if alert.created_at > end_time:
                return False

        return True


# Global alerting service instance
alerting_service = AlertingService()
