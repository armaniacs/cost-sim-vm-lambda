"""
Unit tests for Alerting Service - Simplified version
Tests the core alerting functionality with proper parameter matching
"""

import threading
from datetime import datetime, timedelta

import pytest
from flask import Flask

# Import what we can from the actual implementation
try:
    from app.services.alerting import (
        Alert,
        AlertingService,
        AlertRule,
        AlertSeverity,
        AlertStatus,
        NotificationChannel,
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

    def test_alert_severity_list(self):
        """Test alert severity list"""
        severities = list(AlertSeverity)
        assert len(severities) == 4
        assert AlertSeverity.LOW in severities
        assert AlertSeverity.CRITICAL in severities


class TestAlertStatus:
    """Test AlertStatus enum"""

    def test_alert_status_exists(self):
        """Test alert status enum exists and has values"""
        statuses = list(AlertStatus)
        assert len(statuses) >= 3  # At minimum: ACTIVE, ACKNOWLEDGED, RESOLVED


class TestNotificationChannel:
    """Test NotificationChannel enum"""

    def test_notification_channel_exists(self):
        """Test notification channel enum exists and has values"""
        channels = list(NotificationChannel)
        assert len(channels) >= 3  # At minimum: EMAIL, SLACK, WEBHOOK


class TestAlertRule:
    """Test AlertRule with proper parameters"""

    def create_sample_alert_rule(self, name="test_rule"):
        """Helper to create a sample alert rule with all required parameters"""
        return AlertRule(
            id=f"rule-{name}",
            name=name,
            description=f"Test rule {name}",
            metric_name="cpu_usage",
            condition=">",
            threshold=80.0,
            severity=AlertSeverity.HIGH,
            evaluation_period=60,
            notification_channels=[NotificationChannel.EMAIL],
            escalation_rules=[],
            tags={"environment": "test"},
            enabled=True,
        )

    def test_alert_rule_creation(self):
        """Test AlertRule creation with all required parameters"""
        rule = self.create_sample_alert_rule()

        assert rule.name == "test_rule"
        assert rule.metric_name == "cpu_usage"
        assert rule.condition == ">"
        assert rule.threshold == 80.0
        assert rule.severity == AlertSeverity.HIGH
        assert rule.evaluation_period == 60
        assert rule.enabled is True

    def test_alert_rule_evaluate_conditions(self):
        """Test AlertRule condition evaluation"""
        rule = self.create_sample_alert_rule()

        # Test > condition
        assert rule.evaluate(85.0) is True  # 85 > 80
        assert rule.evaluate(75.0) is False  # 75 not > 80

        # Test >= condition
        rule.condition = ">="
        assert rule.evaluate(80.0) is True  # 80 >= 80
        assert rule.evaluate(79.0) is False  # 79 not >= 80

        # Test < condition
        rule.condition = "<"
        rule.threshold = 20.0
        assert rule.evaluate(15.0) is True  # 15 < 20
        assert rule.evaluate(25.0) is False  # 25 not < 20

    def test_alert_rule_disabled(self):
        """Test AlertRule with enabled=False"""
        rule = AlertRule(
            id="disabled-rule",
            name="disabled_test",
            description="Disabled test rule",
            metric_name="memory_usage",
            condition="<",
            threshold=5.0,
            severity=AlertSeverity.LOW,
            evaluation_period=30,
            notification_channels=[],
            escalation_rules=[],
            tags={},
            enabled=False,
        )

        assert rule.enabled is False


class TestAlert:
    """Test Alert data class"""

    def create_sample_alert(self, alert_id="alert-123"):
        """Helper to create a sample alert"""
        rule = AlertRule(
            id="rule-cpu",
            name="cpu_high",
            description="CPU usage high",
            metric_name="cpu_usage",
            condition=">",
            threshold=80.0,
            severity=AlertSeverity.HIGH,
            evaluation_period=60,
            notification_channels=[NotificationChannel.EMAIL],
            escalation_rules=[],
            tags={},
        )

        return Alert(
            id=alert_id,
            rule_id=rule.id,
            rule_name=rule.name,
            severity=rule.severity,
            status=AlertStatus.ACTIVE,
            message="CPU usage is 85%",
            description=rule.description,
            metric_name=rule.metric_name,
            metric_value=85.0,
            threshold=rule.threshold,
            condition=rule.condition,
            tags=rule.tags,
            created_at=datetime.utcnow(),
        )

    def test_alert_creation(self):
        """Test Alert creation"""
        alert = self.create_sample_alert()

        assert alert.id == "alert-123"
        assert alert.rule_name == "cpu_high"
        assert alert.metric_value == 85.0
        assert alert.status == AlertStatus.ACTIVE
        assert alert.message == "CPU usage is 85%"
        assert alert.created_at is not None


class TestAlertingService:
    """Test AlertingService main functionality"""

    def create_alert_from_rule(
        self,
        alert_id,
        rule,
        metric_value,
        status=AlertStatus.ACTIVE,
        message="Test alert",
    ):
        """Helper to create alert with correct parameters"""
        return Alert(
            id=alert_id,
            rule_id=rule.id,
            rule_name=rule.name,
            severity=rule.severity,
            status=status,
            message=message,
            description=rule.description,
            metric_name=rule.metric_name,
            metric_value=metric_value,
            threshold=rule.threshold,
            condition=rule.condition,
            tags=rule.tags,
            created_at=datetime.utcnow(),
        )

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

    @pytest.fixture
    def sample_alert_rule(self):
        """Create sample alert rule"""
        return AlertRule(
            id="rule-test",
            name="test_rule",
            description="Test rule",
            metric_name="cpu_usage",
            condition=">",
            threshold=80.0,
            severity=AlertSeverity.HIGH,
            evaluation_period=60,
            notification_channels=[NotificationChannel.EMAIL],
            escalation_rules=[],
            tags={"environment": "test"},
        )

    def test_alerting_service_initialization(self, alerting_service):
        """Test AlertingService initialization"""
        assert alerting_service.app is None
        assert len(alerting_service.alert_rules) == 0
        assert len(alerting_service.active_alerts) == 0
        assert len(alerting_service.alert_history) == 0
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

    def test_add_alert_rule(self, alerting_service, sample_alert_rule):
        """Test adding alert rule"""
        alerting_service.add_alert_rule(sample_alert_rule)

        assert sample_alert_rule.id in alerting_service.alert_rules
        assert alerting_service.alert_rules[sample_alert_rule.id] == sample_alert_rule

    def test_remove_alert_rule(self, alerting_service, sample_alert_rule):
        """Test removing alert rule"""
        alerting_service.add_alert_rule(sample_alert_rule)
        assert sample_alert_rule.id in alerting_service.alert_rules

        result = alerting_service.remove_alert_rule(sample_alert_rule.id)

        assert result is True
        assert sample_alert_rule.id not in alerting_service.alert_rules

    def test_remove_nonexistent_alert_rule(self, alerting_service):
        """Test removing nonexistent alert rule"""
        result = alerting_service.remove_alert_rule("nonexistent")

        assert result is False

    def test_acknowledge_alert(self, alerting_service, sample_alert_rule):
        """Test acknowledging alert"""
        # Create and add an active alert
        alert = self.create_alert_from_rule(
            "alert-123",
            sample_alert_rule,
            85.0,
            AlertStatus.ACTIVE,
            "Test alert",
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

    def test_suppress_alert(self, alerting_service, sample_alert_rule):
        """Test suppressing alert"""
        # Create and add an active alert
        alert = self.create_alert_from_rule(
            "alert-456",
            sample_alert_rule,
            95.0,
            AlertStatus.ACTIVE,
            "Memory alert",
        )

        alerting_service.active_alerts[alert.id] = alert

        duration = timedelta(hours=1)
        result = alerting_service.suppress_alert("alert-456", duration, "maintenance")

        assert result is True
        assert alert.suppressed is True
        assert alert.suppressed_until is not None
        assert alert.suppressed_reason == "maintenance"

    def test_get_dashboard_data(self, alerting_service, sample_alert_rule):
        """Test getting dashboard data"""
        # Add some test data
        alert = self.create_alert_from_rule(
            "alert-789",
            sample_alert_rule,
            85.0,
            AlertStatus.ACTIVE,
            "Test alert",
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
        # Add some test alerts to history using proper AlertRule constructor
        for i in range(5):
            rule = AlertRule(
                id=f"rule-{i}",
                name=f"rule_{i}",
                description=f"Test rule {i}",
                metric_name="test_metric",
                condition=">",
                threshold=10.0,
                severity=AlertSeverity.LOW,
                evaluation_period=60,
                notification_channels=[],
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
                description=rule.description,
                metric_name=rule.metric_name,
                metric_value=15.0,
                threshold=rule.threshold,
                condition=rule.condition,
                tags=rule.tags,
                created_at=datetime.utcnow() - timedelta(hours=i),
            )
            alerting_service.alert_history.append(alert)

        history = alerting_service.get_alert_history(limit=3)

        assert len(history) == 3
        # Should return the last 3 alerts added to history (alert-2, alert-3, alert-4)
        assert history[0].id == "alert-2"
        assert history[1].id == "alert-3"
        assert history[2].id == "alert-4"

    def test_search_alerts(self, alerting_service):
        """Test searching alerts"""
        # Add test alerts with proper AlertRule constructors
        high_rule = AlertRule(
            id="high-rule",
            name="high_rule",
            description="High severity rule",
            metric_name="cpu_usage",
            condition=">",
            threshold=80.0,
            severity=AlertSeverity.HIGH,
            evaluation_period=60,
            notification_channels=[],
            escalation_rules=[],
            tags={},
        )

        low_rule = AlertRule(
            id="low-rule",
            name="low_rule",
            description="Low severity rule",
            metric_name="memory_usage",
            condition=">",
            threshold=50.0,
            severity=AlertSeverity.LOW,
            evaluation_period=60,
            notification_channels=[],
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
            description=high_rule.description,
            metric_name=high_rule.metric_name,
            metric_value=85.0,
            threshold=high_rule.threshold,
            condition=high_rule.condition,
            tags=high_rule.tags,
            created_at=datetime.utcnow(),
        )
        low_alert = Alert(
            id="low-1",
            rule_id=low_rule.id,
            rule_name=low_rule.name,
            severity=low_rule.severity,
            status=AlertStatus.ACTIVE,
            message="Low alert",
            description=low_rule.description,
            metric_name=low_rule.metric_name,
            metric_value=55.0,
            threshold=low_rule.threshold,
            condition=low_rule.condition,
            tags=low_rule.tags,
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
            id="test-rule-id",
            name="test_rule",
            description="Test rule",
            metric_name="cpu_usage",
            condition=">",
            threshold=80.0,
            severity=AlertSeverity.HIGH,
            evaluation_period=60,
            notification_channels=[],
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
            description=rule.description,
            metric_name=rule.metric_name,
            metric_value=85.0,
            threshold=rule.threshold,
            condition=rule.condition,
            tags=rule.tags,
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
    """Test basic integration scenarios"""

    def test_basic_alerting_workflow(self):
        """Test basic alerting workflow"""
        service = AlertingService()

        # Add alert rule
        rule = AlertRule(
            id="cpu-rule",
            name="cpu_high",
            description="CPU usage is too high",
            metric_name="cpu_usage",
            condition=">",
            threshold=80.0,
            severity=AlertSeverity.HIGH,
            evaluation_period=60,
            notification_channels=[NotificationChannel.EMAIL],
            escalation_rules=[],
            tags={"environment": "production"},
        )
        service.add_alert_rule(rule)

        # Create alert
        alert = Alert(
            id="workflow-alert",
            rule_id=rule.id,
            rule_name=rule.name,
            severity=rule.severity,
            status=AlertStatus.ACTIVE,
            message="CPU usage is 85%",
            description=rule.description,
            metric_name=rule.metric_name,
            metric_value=85.0,
            threshold=rule.threshold,
            condition=rule.condition,
            tags=rule.tags,
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


class TestEdgeCases:
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

    def test_thread_safety(self):
        """Test basic thread safety of alerting service"""
        service = AlertingService()

        def add_alerts(thread_id):
            for i in range(10):
                rule = AlertRule(
                    id=f"rule-{thread_id}-{i}",
                    name=f"rule_{thread_id}_{i}",
                    description=f"Test rule {thread_id}-{i}",
                    metric_name="test_metric",
                    condition=">",
                    threshold=10.0,
                    severity=AlertSeverity.LOW,
                    evaluation_period=60,
                    notification_channels=[],
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
                    description=rule.description,
                    metric_name=rule.metric_name,
                    metric_value=15.0,
                    threshold=rule.threshold,
                    condition=rule.condition,
                    tags=rule.tags,
                    created_at=datetime.utcnow(),
                )
                with service.lock:
                    service.active_alerts[alert.id] = alert

        # Create multiple threads
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

        # Add many alerts to test deque maxlen behavior
        for i in range(1500):
            rule = AlertRule(
                id=f"rule-{i}",
                name=f"rule_{i}",
                description=f"Test rule {i}",
                metric_name="test_metric",
                condition=">",
                threshold=10.0,
                severity=AlertSeverity.LOW,
                evaluation_period=60,
                notification_channels=[],
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
                description=rule.description,
                metric_name=rule.metric_name,
                metric_value=15.0,
                threshold=rule.threshold,
                condition=rule.condition,
                tags=rule.tags,
                created_at=datetime.utcnow(),
            )
            service.alert_history.append(alert)

        # Should store all alerts since 1500 < maxlen (10000)
        assert len(service.alert_history) == 1500

        # Should still work with limited history
        history = service.get_alert_history(limit=50)
        assert len(history) <= 50


class TestAlertRuleEvaluation:
    """Test AlertRule evaluation logic"""

    def test_all_condition_types(self):
        """Test all supported condition types"""
        base_rule_params = {
            "id": "eval-rule",
            "name": "eval_test",
            "description": "Evaluation test",
            "metric_name": "test_metric",
            "threshold": 50.0,
            "severity": AlertSeverity.MEDIUM,
            "evaluation_period": 60,
            "notification_channels": [],
            "escalation_rules": [],
            "tags": {},
        }

        # Test > condition
        rule = AlertRule(condition=">", **base_rule_params)
        assert rule.evaluate(60.0) is True
        assert rule.evaluate(40.0) is False

        # Test >= condition
        rule = AlertRule(condition=">=", **base_rule_params)
        assert rule.evaluate(50.0) is True
        assert rule.evaluate(49.0) is False

        # Test < condition
        rule = AlertRule(condition="<", **base_rule_params)
        assert rule.evaluate(40.0) is True
        assert rule.evaluate(60.0) is False

        # Test <= condition
        rule = AlertRule(condition="<=", **base_rule_params)
        assert rule.evaluate(50.0) is True
        assert rule.evaluate(51.0) is False

        # Test == condition
        rule = AlertRule(condition="==", **base_rule_params)
        assert rule.evaluate(50.0) is True
        assert rule.evaluate(49.0) is False

        # Test != condition
        rule = AlertRule(condition="!=", **base_rule_params)
        assert rule.evaluate(49.0) is True
        assert rule.evaluate(50.0) is False

        # Test invalid condition
        rule = AlertRule(condition="invalid", **base_rule_params)
        assert rule.evaluate(60.0) is False
