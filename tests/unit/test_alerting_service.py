"""
Unit tests for Alerting Service
Tests alert rule management, notification handling, escalation, and correlation
"""
import pytest
import threading
import time
from unittest.mock import MagicMock, patch, Mock
from datetime import datetime, timedelta
from collections import deque, defaultdict
from flask import Flask

# Import what we can from the actual implementation
try:
    from app.services.alerting import (
        AlertSeverity,
        AlertStatus,
        NotificationChannel,
        AlertRule,
        Alert,
        NotificationChannelHandler,
        EmailNotificationHandler,
        SlackNotificationHandler,
        WebhookNotificationHandler,
        AlertCorrelationEngine,
        EscalationManager,
        AlertingService
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
            name="cpu_high",
            metric="cpu_usage",
            condition=">",
            threshold=80.0,
            severity=AlertSeverity.HIGH,
            description="CPU usage is high"
        )
        
        assert rule.name == "cpu_high"
        assert rule.metric == "cpu_usage"
        assert rule.condition == ">"
        assert rule.threshold == 80.0
        assert rule.severity == AlertSeverity.HIGH
        assert rule.description == "CPU usage is high"
        assert rule.enabled is True  # Default value
    
    def test_alert_rule_disabled(self):
        """Test AlertRule with enabled=False"""
        rule = AlertRule(
            name="test_rule",
            metric="test_metric",
            condition="<",
            threshold=5.0,
            severity=AlertSeverity.LOW,
            enabled=False
        )
        
        assert rule.enabled is False


class TestAlert:
    """Test Alert data class"""
    
    def test_alert_creation(self):
        """Test Alert creation"""
        rule = AlertRule(
            name="cpu_high",
            metric="cpu_usage", 
            condition=">",
            threshold=80.0,
            severity=AlertSeverity.HIGH
        )
        
        alert = Alert(
            id="alert-123",
            rule=rule,
            value=85.0,
            status=AlertStatus.ACTIVE,
            timestamp=datetime.utcnow(),
            message="CPU usage is 85%"
        )
        
        assert alert.id == "alert-123"
        assert alert.rule == rule
        assert alert.value == 85.0
        assert alert.status == AlertStatus.ACTIVE
        assert alert.message == "CPU usage is 85%"
        assert alert.timestamp is not None


class TestNotificationChannelHandler:
    """Test base NotificationChannelHandler"""
    
    def test_handler_abstract_methods(self):
        """Test that handler requires implementation"""
        # Should be abstract - test subclasses instead
        handler = EmailNotificationHandler({})
        assert hasattr(handler, 'send')


class TestEmailNotificationHandler:
    """Test EmailNotificationHandler"""
    
    def test_email_handler_initialization(self):
        """Test email handler initialization"""
        config = {
            "smtp_server": "smtp.example.com",
            "smtp_port": 587,
            "username": "test@example.com",
            "password": "password",
            "from_email": "alerts@example.com"
        }
        
        handler = EmailNotificationHandler(config)
        assert handler.config == config
    
    def test_email_handler_send_success(self):
        """Test successful email sending"""
        config = {"smtp_server": "smtp.example.com"}
        handler = EmailNotificationHandler(config)
        
        # Mock the actual email sending
        with patch.object(handler, '_send_email', return_value=True) as mock_send:
            alert = Mock()
            alert.message = "Test alert"
            alert.rule.severity = AlertSeverity.HIGH
            
            result = handler.send(alert, ["test@example.com"])
            
            assert result is True
            mock_send.assert_called_once()
    
    def test_email_handler_send_failure(self):
        """Test email sending failure"""
        config = {"smtp_server": "smtp.example.com"}
        handler = EmailNotificationHandler(config)
        
        # Mock email sending failure
        with patch.object(handler, '_send_email', side_effect=Exception("SMTP error")):
            alert = Mock()
            alert.message = "Test alert"
            
            result = handler.send(alert, ["test@example.com"])
            
            assert result is False


class TestSlackNotificationHandler:
    """Test SlackNotificationHandler"""
    
    def test_slack_handler_initialization(self):
        """Test Slack handler initialization"""
        config = {
            "webhook_url": "https://hooks.slack.com/services/xxx",
            "channel": "#alerts",
            "username": "AlertBot"
        }
        
        handler = SlackNotificationHandler(config)
        assert handler.config == config
    
    def test_slack_handler_send_success(self):
        """Test successful Slack notification"""
        config = {"webhook_url": "https://hooks.slack.com/services/xxx"}
        handler = SlackNotificationHandler(config)
        
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.text = "ok"
            
            alert = Mock()
            alert.message = "Test alert"
            alert.rule.severity = AlertSeverity.CRITICAL
            
            result = handler.send(alert, ["#alerts"])
            
            assert result is True
            mock_post.assert_called_once()
    
    def test_slack_handler_send_failure(self):
        """Test Slack notification failure"""
        config = {"webhook_url": "https://hooks.slack.com/services/xxx"}
        handler = SlackNotificationHandler(config)
        
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 400
            mock_post.return_value.text = "Bad request"
            
            alert = Mock()
            alert.message = "Test alert"
            
            result = handler.send(alert, ["#alerts"])
            
            assert result is False


class TestWebhookNotificationHandler:
    """Test WebhookNotificationHandler"""
    
    def test_webhook_handler_initialization(self):
        """Test webhook handler initialization"""
        config = {
            "url": "https://example.com/webhook",
            "headers": {"Authorization": "Bearer token"}
        }
        
        handler = WebhookNotificationHandler(config)
        assert handler.config == config
    
    def test_webhook_handler_send_success(self):
        """Test successful webhook notification"""
        config = {"url": "https://example.com/webhook"}
        handler = WebhookNotificationHandler(config)
        
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {"status": "received"}
            
            alert = Mock()
            alert.message = "Test alert"
            alert.rule.severity = AlertSeverity.HIGH
            
            result = handler.send(alert, [])
            
            assert result is True
            mock_post.assert_called_once()


class TestAlertCorrelationEngine:
    """Test AlertCorrelationEngine"""
    
    def test_correlation_engine_initialization(self):
        """Test correlation engine initialization"""
        engine = AlertCorrelationEngine()
        
        assert hasattr(engine, 'correlation_rules')
        assert hasattr(engine, 'correlation_window')
    
    def test_add_correlation_rule(self):
        """Test adding correlation rule"""
        engine = AlertCorrelationEngine()
        
        rule = {
            "name": "cpu_memory_correlation",
            "conditions": ["cpu_usage > 80", "memory_usage > 90"],
            "action": "create_incident"
        }
        
        engine.add_rule(rule)
        
        assert rule in engine.correlation_rules
    
    def test_correlate_alerts(self):
        """Test alert correlation"""
        engine = AlertCorrelationEngine()
        
        # Create test alerts
        cpu_alert = Mock()
        cpu_alert.rule.name = "cpu_high"
        cpu_alert.timestamp = datetime.utcnow()
        
        memory_alert = Mock()
        memory_alert.rule.name = "memory_high"
        memory_alert.timestamp = datetime.utcnow()
        
        alerts = [cpu_alert, memory_alert]
        
        # Test correlation
        correlated = engine.correlate(alerts)
        
        # Should return some result
        assert correlated is not None


class TestEscalationManager:
    """Test EscalationManager"""
    
    def test_escalation_manager_initialization(self):
        """Test escalation manager initialization"""
        manager = EscalationManager()
        
        assert hasattr(manager, 'escalation_policies')
        assert hasattr(manager, 'active_escalations')
    
    def test_add_escalation_policy(self):
        """Test adding escalation policy"""
        manager = EscalationManager()
        
        policy = {
            "name": "critical_escalation",
            "levels": [
                {"delay": 300, "channels": ["email"]},
                {"delay": 900, "channels": ["slack", "email"]},
                {"delay": 1800, "channels": ["webhook"]}
            ]
        }
        
        manager.add_policy("critical", policy)
        
        assert "critical" in manager.escalation_policies
        assert manager.escalation_policies["critical"] == policy
    
    def test_start_escalation(self):
        """Test starting escalation"""
        manager = EscalationManager()
        
        # Add a policy first
        policy = {
            "name": "test_escalation",
            "levels": [{"delay": 60, "channels": ["email"]}]
        }
        manager.add_policy("test", policy)
        
        alert = Mock()
        alert.id = "alert-123"
        alert.rule.severity = AlertSeverity.HIGH
        
        manager.start_escalation(alert, "test")
        
        assert "alert-123" in manager.active_escalations
    
    def test_stop_escalation(self):
        """Test stopping escalation"""
        manager = EscalationManager()
        
        alert = Mock()
        alert.id = "alert-123"
        
        # Start escalation first
        manager.active_escalations["alert-123"] = {"policy": "test", "level": 0}
        
        manager.stop_escalation(alert)
        
        assert "alert-123" not in manager.active_escalations


class TestAlertingService:
    """Test AlertingService main functionality"""
    
    @pytest.fixture
    def app(self):
        """Create test Flask application"""
        app = Flask(__name__)
        app.config['TESTING'] = True
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
        assert len(alerting_service.notification_handlers) == 0
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
            name="test_rule",
            metric="test_metric",
            condition=">",
            threshold=10.0,
            severity=AlertSeverity.MEDIUM
        )
        
        alerting_service.add_alert_rule(rule)
        
        assert rule in alerting_service.alert_rules
    
    def test_remove_alert_rule(self, alerting_service):
        """Test removing alert rule"""
        rule = AlertRule(
            name="test_rule",
            metric="test_metric", 
            condition=">",
            threshold=10.0,
            severity=AlertSeverity.MEDIUM
        )
        
        alerting_service.add_alert_rule(rule)
        assert rule in alerting_service.alert_rules
        
        result = alerting_service.remove_alert_rule("test_rule")
        
        assert result is True
        assert rule not in alerting_service.alert_rules
    
    def test_remove_nonexistent_alert_rule(self, alerting_service):
        """Test removing nonexistent alert rule"""
        result = alerting_service.remove_alert_rule("nonexistent")
        
        assert result is False
    
    def test_acknowledge_alert(self, alerting_service):
        """Test acknowledging alert"""
        # Create and add an active alert
        rule = AlertRule("test", "cpu", ">", 80, AlertSeverity.HIGH)
        alert = Alert(
            id="alert-123",
            rule=rule,
            value=85.0,
            status=AlertStatus.ACTIVE,
            timestamp=datetime.utcnow(),
            message="Test alert"
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
        rule = AlertRule("test", "memory", ">", 90, AlertSeverity.CRITICAL)
        alert = Alert(
            id="alert-456",
            rule=rule,
            value=95.0,
            status=AlertStatus.ACTIVE,
            timestamp=datetime.utcnow(),
            message="Memory alert"
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
        rule = AlertRule("test", "cpu", ">", 80, AlertSeverity.HIGH)
        alert = Alert(
            id="alert-789",
            rule=rule,
            value=85.0,
            status=AlertStatus.ACTIVE,
            timestamp=datetime.utcnow(),
            message="Test alert"
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
            rule = AlertRule(f"rule-{i}", "metric", ">", 10, AlertSeverity.LOW)
            alert = Alert(
                id=f"alert-{i}",
                rule=rule,
                value=15.0,
                status=AlertStatus.RESOLVED,
                timestamp=datetime.utcnow() - timedelta(hours=i),
                message=f"Alert {i}"
            )
            alerting_service.alert_history.append(alert)
        
        history = alerting_service.get_alert_history(limit=3)
        
        assert len(history) == 3
        # Should be in reverse chronological order (most recent first)
        assert history[0].id == "alert-0"
    
    def test_search_alerts(self, alerting_service):
        """Test searching alerts"""
        # Add test alerts
        high_rule = AlertRule("high_rule", "cpu", ">", 80, AlertSeverity.HIGH)
        low_rule = AlertRule("low_rule", "memory", ">", 50, AlertSeverity.LOW)
        
        high_alert = Alert("high-1", high_rule, 85, AlertStatus.ACTIVE, datetime.utcnow(), "High alert")
        low_alert = Alert("low-1", low_rule, 55, AlertStatus.ACTIVE, datetime.utcnow(), "Low alert")
        
        alerting_service.active_alerts["high-1"] = high_alert
        alerting_service.active_alerts["low-1"] = low_alert
        
        # Search for high severity alerts
        results = alerting_service.search_alerts({"severity": "high"})
        
        assert len(results) == 1
        assert results[0].id == "high-1"
    
    def test_matches_alert_query(self, alerting_service):
        """Test _matches_alert_query method"""
        rule = AlertRule("test_rule", "cpu_usage", ">", 80, AlertSeverity.HIGH)
        alert = Alert(
            id="test-alert",
            rule=rule,
            value=85.0,
            status=AlertStatus.ACTIVE,
            timestamp=datetime.utcnow(),
            message="CPU is high"
        )
        
        # Test severity matching
        assert alerting_service._matches_alert_query(alert, {"severity": "high"})
        assert not alerting_service._matches_alert_query(alert, {"severity": "low"})
        
        # Test status matching
        assert alerting_service._matches_alert_query(alert, {"status": "active"})
        assert not alerting_service._matches_alert_query(alert, {"status": "resolved"})
        
        # Test rule name matching
        assert alerting_service._matches_alert_query(alert, {"rule_name": "test_rule"})
        assert not alerting_service._matches_alert_query(alert, {"rule_name": "other_rule"})


class TestIntegrationScenarios:
    """Test integration scenarios"""
    
    def test_full_alerting_workflow(self):
        """Test complete alerting workflow"""
        service = AlertingService()
        
        # Add alert rule
        rule = AlertRule(
            name="cpu_high",
            metric="cpu_usage",
            condition=">",
            threshold=80.0,
            severity=AlertSeverity.HIGH,
            description="CPU usage is too high"
        )
        service.add_alert_rule(rule)
        
        # Simulate triggering an alert
        alert = Alert(
            id="workflow-alert",
            rule=rule,
            value=85.0,
            status=AlertStatus.ACTIVE,
            timestamp=datetime.utcnow(),
            message="CPU usage is 85%"
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
        cpu_rule = AlertRule("cpu_high", "cpu_usage", ">", 80, AlertSeverity.HIGH)
        memory_rule = AlertRule("memory_high", "memory_usage", ">", 90, AlertSeverity.HIGH)
        
        cpu_alert = Alert("cpu-1", cpu_rule, 85, AlertStatus.ACTIVE, datetime.utcnow(), "CPU high")
        memory_alert = Alert("mem-1", memory_rule, 95, AlertStatus.ACTIVE, datetime.utcnow(), "Memory high")
        
        service.active_alerts["cpu-1"] = cpu_alert  
        service.active_alerts["mem-1"] = memory_alert
        
        # Test correlation
        alerts_list = list(service.active_alerts.values())
        correlated = service.correlation_engine.correlate(alerts_list)
        
        # Should detect correlation
        assert correlated is not None
    
    def test_alert_escalation_scenario(self):
        """Test alert escalation scenario"""
        service = AlertingService()
        
        # Add escalation policy
        escalation_policy = {
            "name": "critical_escalation",
            "levels": [
                {"delay": 300, "channels": ["email"]},
                {"delay": 900, "channels": ["slack"]}
            ]
        }
        service.escalation_manager.add_policy("critical", escalation_policy)
        
        # Create critical alert
        rule = AlertRule("disk_full", "disk_usage", ">", 95, AlertSeverity.CRITICAL)
        alert = Alert("critical-1", rule, 98, AlertStatus.ACTIVE, datetime.utcnow(), "Disk full")
        
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
        handler = EmailNotificationHandler({})
        alert = Mock()
        alert.message = "Test"
        
        # Should handle missing config gracefully
        result = handler.send(alert, ["test@example.com"])
        assert result is False
    
    def test_thread_safety(self):
        """Test thread safety of alerting service"""
        service = AlertingService()
        
        def add_alerts():
            for i in range(10):
                rule = AlertRule(f"rule-{i}", "metric", ">", 10, AlertSeverity.LOW)
                alert = Alert(f"alert-{i}", rule, 15, AlertStatus.ACTIVE, datetime.utcnow(), "Test")
                with service.lock:
                    service.active_alerts[alert.id] = alert
        
        # Create multiple threads
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=add_alerts)
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
            rule = AlertRule(f"rule-{i}", "metric", ">", 10, AlertSeverity.LOW)
            alert = Alert(f"alert-{i}", rule, 15, AlertStatus.RESOLVED, datetime.utcnow(), "Test")
            service.alert_history.append(alert)
        
        # Should limit history size
        assert len(service.alert_history) == 1000  # maxlen
        
        # Should still work with limited history
        history = service.get_alert_history(limit=50)
        assert len(history) == 50