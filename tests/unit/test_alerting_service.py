"""
Unit tests for Alerting Service
Tests alert rule management, notification handling, escalation, and correlation
"""

import threading
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest
from flask import Flask

# Import what we can from the actual implementation
try:
    from app.services.alerting import (
        Alert,
        AlertCorrelationEngine,
        AlertingService,
        AlertRule,
        AlertSeverity,
        AlertStatus,
        EmailNotificationHandler,
        EscalationManager,
        NotificationChannel,
        SlackNotificationHandler,
        WebhookNotificationHandler,
    )
except ImportError:
    # Skip tests if imports fail
    pytest.skip("Alerting Service module not available", allow_module_level=True)


class TestAlertSeverity:
    """Test AlertSeverity enum"""

    def test_alert_severity_values(self):
        """Test alert severity enum values"""
        assert AlertSeverity.LOW.value == "low"
        assert AlertSeverity.MEDIUM.value == "medium"
        assert AlertSeverity.HIGH.value == "high"
        assert AlertSeverity.CRITICAL.value == "critical"

    def test_alert_severity_comparison(self):
        """Test alert severity comparison"""
        severities = list(AlertSeverity)
        assert len(severities) == 4
        assert AlertSeverity.LOW in severities
        assert AlertSeverity.CRITICAL in severities


class TestAlertStatus:
    """Test AlertStatus enum"""

    def test_alert_status_values(self):
        """Test alert status enum values"""
        # Test basic status values exist
        statuses = list(AlertStatus)
        assert len(statuses) >= 3  # At minimum: ACTIVE, ACKNOWLEDGED, RESOLVED


class TestNotificationChannel:
    """Test NotificationChannel enum"""

    def test_notification_channel_values(self):
        """Test notification channel enum values"""
        # Test basic channel values exist
        channels = list(NotificationChannel)
        assert len(channels) >= 3  # At minimum: EMAIL, SLACK, WEBHOOK


class TestAlertRule:
    """Test AlertRule data class"""

    def test_alert_rule_creation(self):
        """Test AlertRule creation"""
        rule = AlertRule(
            id="cpu_high_001",
            name="cpu_high",
            metric_name="cpu_usage",
            condition=">",
            threshold=80.0,
            severity=AlertSeverity.HIGH,
            description="CPU usage is high",
            evaluation_period=300,
            notification_channels=[NotificationChannel.EMAIL],
            escalation_rules=[],
            tags={},
        )

        assert rule.name == "cpu_high"
        assert rule.metric_name == "cpu_usage"
        assert rule.condition == ">"
        assert rule.threshold == 80.0
        assert rule.severity == AlertSeverity.HIGH
        assert rule.description == "CPU usage is high"
        assert rule.enabled is True  # Default value

    def test_alert_rule_disabled(self):
        """Test AlertRule with enabled=False"""
        rule = AlertRule(
            id="test_rule_001",
            name="test_rule",
            metric_name="test_metric",
            condition="<",
            threshold=5.0,
            severity=AlertSeverity.LOW,
            description="Test rule",
            evaluation_period=300,
            notification_channels=[NotificationChannel.EMAIL],
            escalation_rules=[],
            tags={},
            enabled=False,
        )

        assert rule.enabled is False


class TestAlert:
    """Test Alert data class"""

    def test_alert_creation(self):
        """Test Alert creation"""
        rule = AlertRule(
            id="cpu_high_001",
            name="cpu_high",
            metric_name="cpu_usage",
            condition=">",
            threshold=80.0,
            severity=AlertSeverity.HIGH,
            description="CPU usage is high",
            evaluation_period=300,
            notification_channels=[NotificationChannel.EMAIL],
            escalation_rules=[],
            tags={},
        )

        alert = Alert(
            id="alert-123",
            rule_id=rule.id,
            rule_name=rule.name,
            severity=rule.severity,
            status=AlertStatus.ACTIVE,
            message="CPU usage is 85%",
            description="CPU usage threshold exceeded",
            metric_name="cpu_usage",
            metric_value=85.0,
            threshold=80.0,
            condition=">",
            tags={},
            created_at=datetime.utcnow(),
        )

        assert alert.id == "alert-123"
        assert alert.rule_id == rule.id
        assert alert.metric_value == 85.0
        assert alert.status == AlertStatus.ACTIVE
        assert alert.message == "CPU usage is 85%"
        assert alert.created_at is not None


class TestNotificationChannelHandler:
    """Test base NotificationChannelHandler"""

    def test_handler_abstract_methods(self):
        """Test that handler requires implementation"""
        # Should be abstract - test subclasses instead
        handler = EmailNotificationHandler()
        assert hasattr(handler, "send_notification")


class TestEmailNotificationHandler:
    """Test EmailNotificationHandler"""

    def test_email_handler_initialization(self):
        """Test email handler initialization"""
        handler = EmailNotificationHandler()
        assert handler is not None
        assert hasattr(handler, "send_notification")

    def test_email_handler_send_success(self):
        """Test successful email sending"""
        handler = EmailNotificationHandler()
        config = {
            "smtp_server": "smtp.example.com",
            "from_email": "test@example.com",
            "to_emails": ["test@example.com"],
        }

        # Mock the SMTP server
        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value = mock_server

            alert = Mock()
            alert.id = "test-alert"
            alert.rule_name = "Test Rule"
            alert.message = "Test alert"
            alert.severity = AlertSeverity.HIGH
            alert.created_at = datetime.utcnow()
            alert.tags = {}

            result = handler.send_notification(alert, config)

            assert result is True
            mock_smtp.assert_called_once_with("smtp.example.com", 587)

    def test_email_handler_send_failure(self):
        """Test email sending failure"""
        handler = EmailNotificationHandler()
        config = {}

        alert = Mock()
        alert.id = "test-alert"
        alert.message = "Test alert"

        result = handler.send_notification(alert, config)
        assert result is False


class TestSlackNotificationHandler:
    """Test SlackNotificationHandler"""

    def test_slack_handler_initialization(self):
        """Test Slack handler initialization"""
        handler = SlackNotificationHandler()
        assert handler is not None
        assert hasattr(handler, "send_notification")

    def test_slack_handler_send_success(self):
        """Test successful Slack notification"""
        handler = SlackNotificationHandler()
        config = {"webhook_url": "https://hooks.slack.com/services/xxx"}

        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.text = "ok"

            alert = Mock()
            alert.id = "test-alert"
            alert.rule_name = "Test Rule"
            alert.message = "Test alert"
            alert.severity = AlertSeverity.CRITICAL
            alert.status = AlertStatus.ACTIVE
            alert.metric_value = 95.0
            alert.threshold = 80.0
            alert.condition = ">"
            alert.created_at = datetime.utcnow()
            alert.tags = {}

            result = handler.send_notification(alert, config)

            assert result is True
            mock_post.assert_called_once()

    def test_slack_handler_send_failure(self):
        """Test Slack notification failure"""
        handler = SlackNotificationHandler()
        config = {}

        alert = Mock()
        alert.message = "Test alert"

        result = handler.send_notification(alert, config)
        assert result is False


class TestWebhookNotificationHandler:
    """Test WebhookNotificationHandler"""

    def test_webhook_handler_initialization(self):
        """Test webhook handler initialization"""
        handler = WebhookNotificationHandler()
        assert handler is not None
        assert hasattr(handler, "send_notification")

    def test_webhook_handler_send_success(self):
        """Test successful webhook notification"""
        handler = WebhookNotificationHandler()
        config = {"url": "https://example.com/webhook"}

        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {"status": "received"}

            alert = Mock()
            alert.id = "test-alert"
            alert.rule_name = "Test Rule"
            alert.message = "Test alert"
            alert.severity = AlertSeverity.HIGH
            alert.created_at = datetime.utcnow()
            alert.to_dict.return_value = {"id": "test-alert"}

            result = handler.send_notification(alert, config)

            assert result is True
            mock_post.assert_called_once()


class TestAlertCorrelationEngine:
    """Test AlertCorrelationEngine"""

    def test_correlation_engine_initialization(self):
        """Test correlation engine initialization"""
        engine = AlertCorrelationEngine()

        assert hasattr(engine, "correlation_rules")
        assert hasattr(engine, "alert_groups")

    def test_add_correlation_rule(self):
        """Test adding correlation rule"""
        engine = AlertCorrelationEngine()

        rule = {
            "name": "cpu_memory_correlation",
            "conditions": ["cpu_usage > 80", "memory_usage > 90"],
            "action": "create_incident",
        }

        engine.add_correlation_rule(rule)

        assert rule in engine.correlation_rules

    def test_correlate_alerts(self):
        """Test alert correlation"""
        engine = AlertCorrelationEngine()

        # Create test alerts
        cpu_alert = Mock()
        cpu_alert.rule_name = "cpu_high"
        cpu_alert.metric_name = "cpu_usage"
        cpu_alert.severity = AlertSeverity.HIGH
        cpu_alert.tags = {}

        # Test correlation
        correlated_group = engine.correlate_alert(cpu_alert)

        # Should return None or group key
        # Since no rules are configured, it should return None
        assert correlated_group is None


class TestEscalationManager:
    """Test EscalationManager"""

    def test_escalation_manager_initialization(self):
        """Test escalation manager initialization"""
        manager = EscalationManager()

        assert hasattr(manager, "escalation_policies")
        assert hasattr(manager, "active_escalations")

    def test_add_escalation_policy(self):
        """Test adding escalation policy"""
        manager = EscalationManager()

        policy = {
            "name": "critical_escalation",
            "levels": [
                {"delay_minutes": 5, "actions": []},
                {"delay_minutes": 15, "actions": []},
                {"delay_minutes": 30, "actions": []},
            ],
        }

        manager.add_escalation_policy("critical", policy)

        assert "critical" in manager.escalation_policies
        assert manager.escalation_policies["critical"] == policy

    def test_start_escalation(self):
        """Test starting escalation"""
        manager = EscalationManager()

        # Add a policy first
        policy = {
            "name": "test_escalation",
            "levels": [{"delay_minutes": 1, "actions": []}],
        }
        manager.add_escalation_policy("test", policy)

        alert = Mock()
        alert.id = "alert-123"
        alert.severity = AlertSeverity.HIGH

        result = manager.start_escalation(alert, "test")

        assert result is True
        assert "alert-123" in manager.active_escalations

    def test_stop_escalation(self):
        """Test stopping escalation"""
        manager = EscalationManager()

        alert = Mock()
        alert.id = "alert-123"

        # Start escalation first
        manager.active_escalations["alert-123"] = {"policy": "test", "level": 0}

        result = manager.stop_escalation("alert-123")

        assert result is True
        assert "alert-123" not in manager.active_escalations


class TestAlertingService:
    """Test AlertingService main functionality"""

    @pytest.fixture
    def app(self):
        """Create test Flask application"""
        app = Flask(__name__)
        app.config["TESTING"] = True
        return app

    @pytest.fixture
    def alerting_service(self):
        """Create AlertingService instance"""
        return AlertingService()

    def test_alerting_service_initialization(self, alerting_service):
        """Test AlertingService initialization"""
        assert alerting_service.app is None
        assert len(alerting_service.alert_rules) == 0
        assert len(alerting_service.active_alerts) == 0
        assert len(alerting_service.alert_history) == 0
        assert len(alerting_service.notification_handlers) > 0  # Has default handlers
        assert alerting_service.correlation_engine is not None
        assert alerting_service.escalation_manager is not None

    def test_alerting_service_with_app(self, app):
        """Test AlertingService with Flask app"""
        service = AlertingService(app)

        assert service.app == app

    def test_init_app(self, app, alerting_service):
        """Test init_app method"""
        alerting_service.init_app(app)

        assert alerting_service.app == app

    def test_add_alert_rule(self, alerting_service):
        """Test adding alert rule"""
        rule = AlertRule(
            id="test_rule_001",
            name="test_rule",
            description="Test rule description",
            metric_name="test_metric",
            condition=">",
            threshold=10.0,
            severity=AlertSeverity.MEDIUM,
            evaluation_period=300,
            notification_channels=[NotificationChannel.EMAIL],
            escalation_rules=[],
            tags={},
        )

        alerting_service.add_alert_rule(rule)

        assert rule.id in alerting_service.alert_rules

    def test_remove_alert_rule(self, alerting_service):
        """Test removing alert rule"""
        rule = AlertRule(
            id="test_rule_001",
            name="test_rule",
            description="Test rule description",
            metric_name="test_metric",
            condition=">",
            threshold=10.0,
            severity=AlertSeverity.MEDIUM,
            evaluation_period=300,
            notification_channels=[NotificationChannel.EMAIL],
            escalation_rules=[],
            tags={},
        )

        alerting_service.add_alert_rule(rule)
        assert rule.id in alerting_service.alert_rules

        result = alerting_service.remove_alert_rule(rule.id)

        assert result is True
        assert rule.id not in alerting_service.alert_rules

    def test_remove_nonexistent_alert_rule(self, alerting_service):
        """Test removing nonexistent alert rule"""
        result = alerting_service.remove_alert_rule("nonexistent")

        assert result is False

    def test_acknowledge_alert(self, alerting_service):
        """Test acknowledging alert"""
        # Create and add an active alert
        rule = AlertRule(
            id="test_rule_001",
            name="test",
            description="Test CPU rule",
            metric_name="cpu",
            condition=">",
            threshold=80.0,
            severity=AlertSeverity.HIGH,
            evaluation_period=300,
            notification_channels=[NotificationChannel.EMAIL],
            escalation_rules=[],
            tags={},
        )
        alert = Alert(
            id="alert-123",
            rule_id=rule.id,
            rule_name=rule.name,
            severity=rule.severity,
            status=AlertStatus.ACTIVE,
            message="Test alert",
            description="Test alert description",
            metric_name=rule.metric_name,
            metric_value=85.0,
            threshold=rule.threshold,
            condition=rule.condition,
            tags={},
            created_at=datetime.utcnow(),
        )

        alerting_service.active_alerts[alert.id] = alert

        result = alerting_service.acknowledge_alert("alert-123", "test_user")

        assert result is True
        assert alert.status == AlertStatus.ACKNOWLEDGED
        assert alert.acknowledged_by == "test_user"
        assert alert.acknowledged_at is not None

    def test_acknowledge_nonexistent_alert(self, alerting_service):
        """Test acknowledging nonexistent alert"""
        result = alerting_service.acknowledge_alert("nonexistent", "user")

        assert result is False

    def test_suppress_alert(self, alerting_service):
        """Test suppressing alert"""
        # Create and add an active alert
        rule = AlertRule(
            id="test_rule_002",
            name="test",
            description="Test memory rule",
            metric_name="memory",
            condition=">",
            threshold=90.0,
            severity=AlertSeverity.CRITICAL,
            evaluation_period=300,
            notification_channels=[NotificationChannel.EMAIL],
            escalation_rules=[],
            tags={},
        )
        alert = Alert(
            id="alert-456",
            rule_id=rule.id,
            rule_name=rule.name,
            severity=rule.severity,
            status=AlertStatus.ACTIVE,
            message="Memory alert",
            description="Memory alert description",
            metric_name=rule.metric_name,
            metric_value=95.0,
            threshold=rule.threshold,
            condition=rule.condition,
            tags={},
            created_at=datetime.utcnow(),
        )

        alerting_service.active_alerts[alert.id] = alert

        duration = timedelta(hours=1)
        result = alerting_service.suppress_alert("alert-456", duration, "maintenance")

        assert result is True
        assert alert.suppressed is True
        assert alert.suppressed_until is not None
        assert alert.suppressed_reason == "maintenance"

    def test_get_dashboard_data(self, alerting_service):
        """Test getting dashboard data"""
        # Add some test data
        rule = AlertRule(
            id="test_rule_003",
            name="test",
            description="Test CPU rule",
            metric_name="cpu",
            condition=">",
            threshold=80.0,
            severity=AlertSeverity.HIGH,
            evaluation_period=300,
            notification_channels=[NotificationChannel.EMAIL],
            escalation_rules=[],
            tags={},
        )
        alert = Alert(
            id="alert-789",
            rule_id=rule.id,
            rule_name=rule.name,
            severity=rule.severity,
            status=AlertStatus.ACTIVE,
            message="Test alert",
            description="Test alert description",
            metric_name=rule.metric_name,
            metric_value=85.0,
            threshold=rule.threshold,
            condition=rule.condition,
            tags={},
            created_at=datetime.utcnow(),
        )

        alerting_service.active_alerts[alert.id] = alert
        alerting_service.alert_history.append(alert)

        data = alerting_service.get_dashboard_data()

        assert "active_alerts" in data
        assert "alert_counts" in data
        assert "severity_breakdown" in data
        assert "recent_alerts" in data
        assert data["active_alerts"]["total"] == 1
        assert data["alert_counts"]["total"] == 1

    def test_get_alert_history(self, alerting_service):
        """Test getting alert history"""
        # Add some test alerts to history
        for i in range(5):
            rule = AlertRule(
                id=f"rule-{i}_001",
                name=f"rule-{i}",
                description=f"Test rule {i}",
                metric_name="metric",
                condition=">",
                threshold=10.0,
                severity=AlertSeverity.LOW,
                evaluation_period=300,
                notification_channels=[NotificationChannel.EMAIL],
                escalation_rules=[],
                tags={},
            )
            alert = Alert(
                id=f"alert-{i}",
                rule_id=rule.id,
                rule_name=rule.name,
                severity=rule.severity,
                status=AlertStatus.RESOLVED,
                message=f"Alert {i}",
                description=f"Alert {i} description",
                metric_name=rule.metric_name,
                metric_value=15.0,
                threshold=rule.threshold,
                condition=rule.condition,
                tags={},
                created_at=datetime.utcnow() - timedelta(hours=i),
            )
            alerting_service.alert_history.append(alert)

        history = alerting_service.get_alert_history(limit=3)

        assert len(history) == 3
        # get_alert_history returns the last 3 items from deque (alert-2, alert-3, alert-4)
        assert history[-1].id == "alert-4"  # Last added to deque

    def test_search_alerts(self, alerting_service):
        """Test searching alerts"""
        # Add test alerts
        high_rule = AlertRule(
            id="high_rule_001",
            name="high_rule",
            description="High CPU rule",
            metric_name="cpu",
            condition=">",
            threshold=80.0,
            severity=AlertSeverity.HIGH,
            evaluation_period=300,
            notification_channels=[NotificationChannel.EMAIL],
            escalation_rules=[],
            tags={},
        )
        low_rule = AlertRule(
            id="low_rule_001",
            name="low_rule",
            description="Low memory rule",
            metric_name="memory",
            condition=">",
            threshold=50.0,
            severity=AlertSeverity.LOW,
            evaluation_period=300,
            notification_channels=[NotificationChannel.EMAIL],
            escalation_rules=[],
            tags={},
        )

        high_alert = Alert(
            id="high-1",
            rule_id=high_rule.id,
            rule_name=high_rule.name,
            severity=high_rule.severity,
            status=AlertStatus.ACTIVE,
            message="High alert",
            description="High alert description",
            metric_name=high_rule.metric_name,
            metric_value=85.0,
            threshold=high_rule.threshold,
            condition=high_rule.condition,
            tags={},
            created_at=datetime.utcnow(),
        )
        low_alert = Alert(
            id="low-1",
            rule_id=low_rule.id,
            rule_name=low_rule.name,
            severity=low_rule.severity,
            status=AlertStatus.ACTIVE,
            message="Low alert",
            description="Low alert description",
            metric_name=low_rule.metric_name,
            metric_value=55.0,
            threshold=low_rule.threshold,
            condition=low_rule.condition,
            tags={},
            created_at=datetime.utcnow(),
        )

        alerting_service.active_alerts["high-1"] = high_alert
        alerting_service.active_alerts["low-1"] = low_alert

        # Search for high severity alerts
        results = alerting_service.search_alerts({"severity": "high"})

        assert len(results) == 1
        assert results[0].id == "high-1"

    def test_matches_alert_query(self, alerting_service):
        """Test _matches_alert_query method"""
        rule = AlertRule(
            id="test_rule_004",
            name="test_rule",
            description="Test CPU usage rule",
            metric_name="cpu_usage",
            condition=">",
            threshold=80.0,
            severity=AlertSeverity.HIGH,
            evaluation_period=300,
            notification_channels=[NotificationChannel.EMAIL],
            escalation_rules=[],
            tags={},
        )
        alert = Alert(
            id="test-alert",
            rule_id=rule.id,
            rule_name=rule.name,
            severity=rule.severity,
            status=AlertStatus.ACTIVE,
            message="CPU is high",
            description="CPU is high description",
            metric_name=rule.metric_name,
            metric_value=85.0,
            threshold=rule.threshold,
            condition=rule.condition,
            tags={},
            created_at=datetime.utcnow(),
        )

        # Test severity matching
        assert alerting_service._matches_alert_query(alert, {"severity": "high"})
        assert not alerting_service._matches_alert_query(alert, {"severity": "low"})

        # Test status matching
        assert alerting_service._matches_alert_query(alert, {"status": "active"})
        assert not alerting_service._matches_alert_query(alert, {"status": "resolved"})

        # Test rule name matching
        assert alerting_service._matches_alert_query(alert, {"rule_name": "test_rule"})
        assert not alerting_service._matches_alert_query(
            alert, {"rule_name": "other_rule"}
        )


class TestIntegrationScenarios:
    """Test integration scenarios"""

    def test_full_alerting_workflow(self):
        """Test complete alerting workflow"""
        service = AlertingService()

        # Add alert rule
        rule = AlertRule(
            id="cpu_high_001",
            name="cpu_high",
            description="CPU usage is too high",
            metric_name="cpu_usage",
            condition=">",
            threshold=80.0,
            severity=AlertSeverity.HIGH,
            evaluation_period=300,
            notification_channels=[NotificationChannel.EMAIL],
            escalation_rules=[],
            tags={},
        )
        service.add_alert_rule(rule)

        # Simulate triggering an alert
        alert = Alert(
            id="workflow-alert",
            rule_id=rule.id,
            rule_name=rule.name,
            severity=rule.severity,
            status=AlertStatus.ACTIVE,
            message="CPU usage is 85%",
            description="CPU usage is too high",
            metric_name=rule.metric_name,
            metric_value=85.0,
            threshold=rule.threshold,
            condition=rule.condition,
            tags={},
            created_at=datetime.utcnow(),
        )

        service.active_alerts[alert.id] = alert

        # Acknowledge the alert
        service.acknowledge_alert(alert.id, "admin")

        # Verify state changes
        assert alert.status == AlertStatus.ACKNOWLEDGED
        assert alert.acknowledged_by == "admin"

        # Get dashboard data
        dashboard = service.get_dashboard_data()
        assert dashboard["active_alerts"]["total"] == 1
        assert dashboard["alert_counts"]["acknowledged"] == 1

    def test_alert_correlation_scenario(self):
        """Test alert correlation scenario"""
        service = AlertingService()

        # Create related alerts
        cpu_rule = AlertRule(
            id="cpu_high_002",
            name="cpu_high",
            description="CPU usage is too high",
            metric_name="cpu_usage",
            condition=">",
            threshold=80.0,
            severity=AlertSeverity.HIGH,
            evaluation_period=300,
            notification_channels=[NotificationChannel.EMAIL],
            escalation_rules=[],
            tags={},
        )
        memory_rule = AlertRule(
            id="memory_high_001",
            name="memory_high",
            description="Memory usage is too high",
            metric_name="memory_usage",
            condition=">",
            threshold=90.0,
            severity=AlertSeverity.HIGH,
            evaluation_period=300,
            notification_channels=[NotificationChannel.EMAIL],
            escalation_rules=[],
            tags={},
        )

        cpu_alert = Alert(
            id="cpu-1",
            rule_id=cpu_rule.id,
            rule_name=cpu_rule.name,
            severity=cpu_rule.severity,
            status=AlertStatus.ACTIVE,
            message="CPU high",
            description="CPU usage is too high",
            metric_name=cpu_rule.metric_name,
            metric_value=85.0,
            threshold=cpu_rule.threshold,
            condition=cpu_rule.condition,
            tags={},
            created_at=datetime.utcnow(),
        )
        memory_alert = Alert(
            id="mem-1",
            rule_id=memory_rule.id,
            rule_name=memory_rule.name,
            severity=memory_rule.severity,
            status=AlertStatus.ACTIVE,
            message="Memory high",
            description="Memory usage is too high",
            metric_name=memory_rule.metric_name,
            metric_value=95.0,
            threshold=memory_rule.threshold,
            condition=memory_rule.condition,
            tags={},
            created_at=datetime.utcnow(),
        )

        service.active_alerts["cpu-1"] = cpu_alert
        service.active_alerts["mem-1"] = memory_alert

        # Test correlation
        alerts_list = list(service.active_alerts.values())

        # Test individual alert correlation
        cpu_group = service.correlation_engine.correlate_alert(cpu_alert)
        mem_group = service.correlation_engine.correlate_alert(memory_alert)

        # Since no correlation rules are set, should return None
        assert cpu_group is None
        assert mem_group is None

    def test_alert_escalation_scenario(self):
        """Test alert escalation scenario"""
        service = AlertingService()

        # Add escalation policy
        escalation_policy = {
            "name": "critical_escalation",
            "levels": [
                {"delay_minutes": 5, "actions": []},
                {"delay_minutes": 15, "actions": []},
            ],
        }
        service.escalation_manager.add_escalation_policy("critical", escalation_policy)

        # Create critical alert
        rule = AlertRule(
            id="disk_full_001",
            name="disk_full",
            description="Disk usage is too high",
            metric_name="disk_usage",
            condition=">",
            threshold=95.0,
            severity=AlertSeverity.CRITICAL,
            evaluation_period=300,
            notification_channels=[NotificationChannel.EMAIL],
            escalation_rules=[],
            tags={},
        )
        alert = Alert(
            id="critical-1",
            rule_id=rule.id,
            rule_name=rule.name,
            severity=rule.severity,
            status=AlertStatus.ACTIVE,
            message="Disk full",
            description="Disk usage is too high",
            metric_name=rule.metric_name,
            metric_value=98.0,
            threshold=rule.threshold,
            condition=rule.condition,
            tags={},
            created_at=datetime.utcnow(),
        )

        service.active_alerts[alert.id] = alert

        # Start escalation
        service.escalation_manager.start_escalation(alert, "critical")

        # Verify escalation started
        assert alert.id in service.escalation_manager.active_escalations


class TestEdgeCasesAndErrorHandling:
    """Test edge cases and error handling"""

    def test_empty_alerting_service(self):
        """Test alerting service with no data"""
        service = AlertingService()

        dashboard = service.get_dashboard_data()
        assert dashboard["active_alerts"]["total"] == 0
        assert dashboard["alert_counts"]["total"] == 0

        # Should not crash on empty operations
        history = service.get_alert_history()
        assert history == []

        results = service.search_alerts({"severity": "high"})
        assert results == []

    def test_notification_handler_errors(self):
        """Test notification handler error scenarios"""
        # Test email handler with invalid config
        handler = EmailNotificationHandler()
        alert = Mock()
        alert.id = "test-alert"
        alert.message = "Test"
        alert.severity = AlertSeverity.HIGH
        alert.created_at = datetime.utcnow()
        alert.tags = {}

        # Should handle missing config gracefully
        result = handler.send_notification(alert, {})
        assert result is False

    def test_thread_safety(self):
        """Test thread safety of alerting service"""
        service = AlertingService()

        def add_alerts(thread_id):
            for i in range(10):
                rule = AlertRule(
                    id=f"rule-{thread_id}-{i}_thread",
                    name=f"rule-{thread_id}-{i}",
                    description=f"Test rule {thread_id}-{i}",
                    metric_name="metric",
                    condition=">",
                    threshold=10.0,
                    severity=AlertSeverity.LOW,
                    evaluation_period=300,
                    notification_channels=[NotificationChannel.EMAIL],
                    escalation_rules=[],
                    tags={},
                )
                alert = Alert(
                    id=f"alert-{thread_id}-{i}",
                    rule_id=rule.id,
                    rule_name=rule.name,
                    severity=rule.severity,
                    status=AlertStatus.ACTIVE,
                    message="Test",
                    description="Test alert",
                    metric_name=rule.metric_name,
                    metric_value=15.0,
                    threshold=rule.threshold,
                    condition=rule.condition,
                    tags={},
                    created_at=datetime.utcnow(),
                )
                with service.lock:
                    service.active_alerts[alert.id] = alert

        # Create multiple threads with unique IDs
        threads = []
        for thread_id in range(3):
            thread = threading.Thread(target=add_alerts, args=(thread_id,))
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Check results
        assert len(service.active_alerts) == 30

    def test_large_alert_volume_handling(self):
        """Test handling of large alert volumes"""
        service = AlertingService()

        # Add many alerts
        for i in range(1500):
            rule = AlertRule(
                id=f"rule-{i}_volume",
                name=f"rule-{i}",
                description=f"Test rule {i}",
                metric_name="metric",
                condition=">",
                threshold=10.0,
                severity=AlertSeverity.LOW,
                evaluation_period=300,
                notification_channels=[NotificationChannel.EMAIL],
                escalation_rules=[],
                tags={},
            )
            alert = Alert(
                id=f"alert-{i}",
                rule_id=rule.id,
                rule_name=rule.name,
                severity=rule.severity,
                status=AlertStatus.RESOLVED,
                message="Test",
                description="Test alert",
                metric_name=rule.metric_name,
                metric_value=15.0,
                threshold=rule.threshold,
                condition=rule.condition,
                tags={},
                created_at=datetime.utcnow(),
            )
            service.alert_history.append(alert)

        # Should limit history size (maxlen in AlertingService is 10000)
        assert len(service.alert_history) == 1500

        # Should still work with limited history
        history = service.get_alert_history(limit=50)
        assert len(history) == 50
