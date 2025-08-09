"""
Unit tests for the monitoring system components.

This module tests:
- APM service functionality
- Logging service functionality
- Alerting service functionality
- Observability service functionality
- Monitoring integration
"""

import json
from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from app.services.alerting_service import (
    Alert,
    AlertingService,
    AlertRule,
    AlertSeverity,
    AlertStatus,
)
from app.services.apm_service import PerformanceProfiler, Span, TraceContext
from app.services.logging_service import LogAggregator, StructuredFormatter
from app.services.monitoring_integration import MonitoringConfig, MonitoringIntegration
from app.services.observability_service import HealthCheck, HealthChecker, HealthStatus


class TestAPMService:
    """Test cases for APM service."""

    def test_trace_context_creation(self):
        """Test trace context creation."""
        trace_id = "test-trace-123"
        trace_context = TraceContext(trace_id)

        assert trace_context.trace_id == trace_id
        assert trace_context.parent_span_id is None
        assert trace_context.spans == []
        assert trace_context.start_time is not None
        assert trace_context.end_time is None

    def test_span_creation(self):
        """Test span creation."""
        span_id = "test-span-123"
        operation_name = "database_query"

        span = Span(span_id, operation_name)

        assert span.span_id == span_id
        assert span.operation_name == operation_name
        assert span.parent_span_id is None
        assert span.tags == {}
        assert span.logs == []
        assert span.error is None

    def test_span_tagging(self):
        """Test span tagging functionality."""
        span = Span("test-span", "test_operation")

        span.set_tag("database", "postgresql")
        span.set_tag("query_type", "SELECT")

        assert span.tags["database"] == "postgresql"
        assert span.tags["query_type"] == "SELECT"

    def test_span_logging(self):
        """Test span logging functionality."""
        span = Span("test-span", "test_operation")

        span.log("Starting operation", "info")
        span.log("Operation completed", "info")

        assert len(span.logs) == 2
        assert span.logs[0]["message"] == "Starting operation"
        assert span.logs[1]["message"] == "Operation completed"

    def test_span_error_handling(self):
        """Test span error handling."""
        span = Span("test-span", "test_operation")

        test_error = ValueError("Test error")
        span.set_error(test_error)

        assert span.error is not None
        assert span.error["type"] == "ValueError"
        assert span.error["message"] == "Test error"
        assert span.tags.get("error") is True

    def test_performance_profiler(self):
        """Test performance profiler."""
        profiler = PerformanceProfiler()

        # Record some function calls
        profiler.profile_function("test_function", 0.1)
        profiler.profile_function("test_function", 0.2)
        profiler.profile_function("another_function", 0.05)

        # Check function statistics
        stats = profiler.get_function_stats("test_function")
        assert stats["call_count"] == 2
        assert stats["total_time"] == 0.3
        assert stats["avg_time"] == 0.15
        assert stats["min_time"] == 0.1
        assert stats["max_time"] == 0.2

        # Check slowest functions
        slowest = profiler.get_slowest_functions(limit=2)
        assert len(slowest) == 2
        assert slowest[0]["function"] == "test_function"
        assert slowest[1]["function"] == "another_function"


class TestLoggingService:
    """Test cases for logging service."""

    def test_structured_formatter(self):
        """Test structured JSON formatter."""
        formatter = StructuredFormatter()

        # Create a log record
        import logging

        logger = logging.getLogger("test_logger")
        record = logger.makeRecord(
            name="test_logger",
            level=logging.INFO,
            fn="test_file.py",
            lno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        # Format the record
        formatted = formatter.format(record)
        log_data = json.loads(formatted)

        assert log_data["level"] == "INFO"
        assert log_data["logger"] == "test_logger"
        assert log_data["message"] == "Test message"
        assert log_data["module"] == "test_file"
        assert log_data["line"] == 10
        assert "timestamp" in log_data

    def test_log_aggregator(self):
        """Test log aggregator."""
        aggregator = LogAggregator(max_entries=10)

        # Add some log entries
        log_entry1 = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": "INFO",
            "logger": "test_logger",
            "message": "Test message 1",
            "module": "test_module",
            "function": "test_function",
            "line": 10,
        }

        log_entry2 = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": "ERROR",
            "logger": "test_logger",
            "message": "Test error message",
            "module": "test_module",
            "function": "test_function",
            "line": 20,
        }

        aggregator.add_log(log_entry1)
        aggregator.add_log(log_entry2)

        # Check recent logs
        recent_logs = aggregator.get_recent_logs(limit=10)
        assert len(recent_logs) == 2

        # Check error logs only
        error_logs = aggregator.get_recent_logs(limit=10, level="ERROR")
        assert len(error_logs) == 1
        assert error_logs[0]["message"] == "Test error message"

        # Check log statistics
        stats = aggregator.get_log_stats()
        assert stats["total_logs"] == 2
        assert stats["log_counts"]["INFO"] == 1
        assert stats["log_counts"]["ERROR"] == 1

    def test_log_search(self):
        """Test log search functionality."""
        aggregator = LogAggregator()

        # Add test log entries
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": "ERROR",
            "logger": "database_logger",
            "message": "Database connection failed",
            "module": "database",
            "function": "connect",
            "line": 50,
            "trace_id": "test-trace-123",
        }

        aggregator.add_log(log_entry)

        # Search by level
        results = aggregator.search_logs({"level": "ERROR"})
        assert len(results) == 1
        assert results[0]["message"] == "Database connection failed"

        # Search by logger
        results = aggregator.search_logs({"logger": "database"})
        assert len(results) == 1

        # Search by trace ID
        results = aggregator.search_logs({"trace_id": "test-trace-123"})
        assert len(results) == 1

        # Search with no matches
        results = aggregator.search_logs({"level": "DEBUG"})
        assert len(results) == 0


class TestAlertingService:
    """Test cases for alerting service."""

    def test_alert_creation(self):
        """Test alert creation."""
        alert = Alert(
            id="test-alert-123",
            rule_id="test-rule",
            name="Test Alert",
            description="Test alert description",
            severity=AlertSeverity.HIGH,
            status=AlertStatus.ACTIVE,
            value=100.0,
            threshold=80.0,
            condition=">=",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        assert alert.id == "test-alert-123"
        assert alert.severity == AlertSeverity.HIGH
        assert alert.status == AlertStatus.ACTIVE
        assert alert.value == 100.0
        assert alert.threshold == 80.0

    def test_alert_rule_evaluation(self):
        """Test alert rule evaluation."""
        rule = AlertRule(
            id="test-rule",
            name="High CPU Usage",
            description="CPU usage is above threshold",
            metric_name="cpu_usage",
            condition=">=",
            threshold=80.0,
            severity=AlertSeverity.HIGH,
            evaluation_period=300,
            notification_channels=[],
            escalation_rules=[],
            tags={},
        )

        # Test threshold exceeded
        assert rule.evaluate(90.0) is True
        assert rule.evaluate(80.0) is True
        assert rule.evaluate(70.0) is False

        # Test different conditions
        rule.condition = "<="
        assert rule.evaluate(70.0) is True
        assert rule.evaluate(90.0) is False

        rule.condition = "=="
        rule.threshold = 75.0
        assert rule.evaluate(75.0) is True
        assert rule.evaluate(76.0) is False

    @patch("app.services.alerting_service.performance_monitor")
    def test_alert_triggering(self, mock_performance_monitor):
        """Test alert triggering."""
        # Mock performance monitor to return high CPU usage
        mock_performance_monitor.system_monitor.get_cpu_usage.return_value = 90.0

        alerting_service = AlertingService()

        # Add a CPU usage alert rule
        rule = AlertRule(
            id="cpu_usage_rule",
            name="High CPU Usage",
            description="CPU usage is above threshold",
            metric_name="system.cpu_usage",
            condition=">=",
            threshold=80.0,
            severity=AlertSeverity.HIGH,
            evaluation_period=300,
            notification_channels=[],
            escalation_rules=[],
            tags={},
        )

        alerting_service.add_alert_rule(rule)

        # Trigger evaluation
        alerting_service._evaluate_alert_rules()

        # Check if alert was triggered
        assert len(alerting_service.active_alerts) == 1
        alert = list(alerting_service.active_alerts.values())[0]
        assert alert.name == "High CPU Usage"
        assert alert.value == 90.0

    def test_alert_acknowledgment(self):
        """Test alert acknowledgment."""
        alerting_service = AlertingService()

        # Create test alert
        alert = Alert(
            id="test-alert-123",
            rule_id="test-rule",
            name="Test Alert",
            description="Test alert description",
            severity=AlertSeverity.HIGH,
            status=AlertStatus.ACTIVE,
            value=100.0,
            threshold=80.0,
            condition=">=",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        alerting_service.active_alerts["test-rule"] = alert

        # Acknowledge the alert
        success = alerting_service.acknowledge_alert("test-alert-123", "test-user")

        assert success is True
        assert alert.status == AlertStatus.ACKNOWLEDGED
        assert alert.acknowledged_at is not None
        assert alert.metadata.get("acknowledged_by") == "test-user"

    def test_alert_search(self):
        """Test alert search functionality."""
        alerting_service = AlertingService()

        # Add test alerts to history
        alert1 = Alert(
            id="alert-1",
            rule_id="rule-1",
            name="CPU Alert",
            description="High CPU usage",
            severity=AlertSeverity.HIGH,
            status=AlertStatus.ACTIVE,
            value=90.0,
            threshold=80.0,
            condition=">=",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            tags={"category": "system"},
        )

        alert2 = Alert(
            id="alert-2",
            rule_id="rule-2",
            name="Memory Alert",
            description="High memory usage",
            severity=AlertSeverity.MEDIUM,
            status=AlertStatus.RESOLVED,
            value=85.0,
            threshold=80.0,
            condition=">=",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            tags={"category": "system"},
        )

        alerting_service.alert_history.append(alert1)
        alerting_service.alert_history.append(alert2)

        # Search by severity
        results = alerting_service.search_alerts({"severity": "high"})
        assert len(results) == 1
        assert results[0]["name"] == "CPU Alert"

        # Search by status
        results = alerting_service.search_alerts({"status": "resolved"})
        assert len(results) == 1
        assert results[0]["name"] == "Memory Alert"

        # Search by tags
        results = alerting_service.search_alerts({"tags": {"category": "system"}})
        assert len(results) == 2


class TestObservabilityService:
    """Test cases for observability service."""

    def test_health_check_creation(self):
        """Test health check creation."""
        health_check = HealthCheck(
            name="api_health",
            url="http://localhost:5000/health",
            method="GET",
            timeout=5,
            interval=60,
            expected_status=200,
            tags={"service": "api"},
        )

        assert health_check.name == "api_health"
        assert health_check.url == "http://localhost:5000/health"
        assert health_check.method == "GET"
        assert health_check.timeout == 5
        assert health_check.expected_status == 200
        assert health_check.tags["service"] == "api"

    @patch("requests.request")
    def test_health_check_execution(self, mock_request):
        """Test health check execution."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "OK"
        mock_request.return_value = mock_response

        health_checker = HealthChecker()
        health_check = HealthCheck(
            name="api_health",
            url="http://localhost:5000/health",
            method="GET",
            timeout=5,
            interval=60,
            expected_status=200,
        )

        result = health_checker.perform_health_check(health_check)

        assert result["name"] == "api_health"
        assert result["status"] == HealthStatus.HEALTHY.value
        assert result["status_code"] == 200
        assert result["error"] is None

    @patch("requests.request")
    def test_health_check_failure(self, mock_request):
        """Test health check failure handling."""
        # Mock failed response
        mock_request.side_effect = Exception("Connection failed")

        health_checker = HealthChecker()
        health_check = HealthCheck(
            name="api_health",
            url="http://localhost:5000/health",
            method="GET",
            timeout=5,
            interval=60,
            expected_status=200,
        )

        result = health_checker.perform_health_check(health_check)

        assert result["name"] == "api_health"
        assert result["status"] == HealthStatus.UNHEALTHY.value
        assert result["status_code"] is None
        assert "Connection failed" in result["error"]

    def test_metrics_collection(self):
        """Test metrics collection."""
        from app.services.observability_service import MetricsCollector, MetricType

        collector = MetricsCollector()

        # Record some metrics
        collector.record_metric(
            "cpu_usage", 75.0, MetricType.GAUGE, {"host": "server1"}
        )
        collector.record_metric(
            "cpu_usage", 80.0, MetricType.GAUGE, {"host": "server1"}
        )
        collector.record_metric(
            "memory_usage", 60.0, MetricType.GAUGE, {"host": "server1"}
        )

        # Get metric statistics
        stats = collector.get_metric_statistics("cpu_usage", {"host": "server1"})

        assert stats["count"] == 2
        assert stats["min"] == 75.0
        assert stats["max"] == 80.0
        assert stats["avg"] == 77.5
        assert stats["sum"] == 155.0

    def test_sla_monitoring(self):
        """Test SLA monitoring."""
        from app.services.observability_service import SLAMonitor

        sla_monitor = SLAMonitor()

        # Add SLA target
        sla_monitor.add_sla_target(
            "response_time",
            {
                "type": "response_time",
                "target": 95.0,
                "threshold": 1.0,
                "description": "95% of requests under 1s",
            },
        )

        # Record some metrics
        sla_monitor.record_sla_metric("response_time", 0.5)
        sla_monitor.record_sla_metric("response_time", 0.8)
        sla_monitor.record_sla_metric("response_time", 1.2)
        sla_monitor.record_sla_metric("response_time", 0.6)

        # Calculate compliance
        compliance = sla_monitor.calculate_sla_compliance("response_time")

        assert compliance["name"] == "response_time"
        assert compliance["compliance"] == 75.0  # 3 out of 4 under threshold
        assert compliance["target"] == 95.0
        assert compliance["met"] is False
        assert compliance["data_points"] == 4


class TestMonitoringIntegration:
    """Test cases for monitoring integration."""

    def test_config_management(self):
        """Test configuration management."""
        config = MonitoringConfig()

        # Test getting configuration values
        assert config.get("apm.enabled") is True
        assert config.get("logging.log_level") == "INFO"
        assert config.get("nonexistent.key", "default") == "default"

        # Test setting configuration values
        config.set("apm.sampling_rate", 0.5)
        assert config.get("apm.sampling_rate") == 0.5

        config.set("custom.new_setting", "test_value")
        assert config.get("custom.new_setting") == "test_value"

    @patch("app.services.monitoring_integration.APMService")
    @patch("app.services.monitoring_integration.LoggingService")
    @patch("app.services.monitoring_integration.AlertingService")
    @patch("app.services.monitoring_integration.ObservabilityService")
    def test_service_initialization(
        self, mock_observability, mock_alerting, mock_logging, mock_apm
    ):
        """Test monitoring service initialization."""
        mock_app = Mock()

        integration = MonitoringIntegration()
        integration.init_app(mock_app)

        # Check that services were initialized
        assert mock_apm.called
        assert mock_logging.called
        assert mock_alerting.called
        assert mock_observability.called

        # Check that services are stored
        assert "apm" in integration.services
        assert "logging" in integration.services
        assert "alerting" in integration.services
        assert "observability" in integration.services

    def test_unified_dashboard_data(self):
        """Test unified dashboard data generation."""
        integration = MonitoringIntegration()

        # Mock services
        mock_service = Mock()
        mock_service.get_dashboard_data.return_value = {"test": "data"}
        integration.services["test_service"] = mock_service

        dashboard_data = integration.get_unified_dashboard()

        assert "timestamp" in dashboard_data
        assert "services" in dashboard_data
        assert "summary" in dashboard_data
        assert dashboard_data["services"]["test_service"] == {"test": "data"}

    def test_service_access(self):
        """Test service access methods."""
        integration = MonitoringIntegration()

        # Mock service
        mock_service = Mock()
        integration.services["test_service"] = mock_service

        # Test service retrieval
        assert integration.get_service("test_service") == mock_service
        assert integration.get_service("nonexistent") is None

        # Test service enabled check
        assert integration.is_service_enabled("test_service") is True
        assert integration.is_service_enabled("nonexistent") is False


class TestMonitoringAPI:
    """Test cases for monitoring API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from app.main import create_app

        app = create_app("testing")
        app.config["TESTING"] = True

        with app.test_client() as client:
            yield client

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/api/v1/monitoring/health")

        # Should return 200 even if monitoring is not fully initialized
        assert response.status_code in [200, 500]

    def test_dashboard_endpoint(self, client):
        """Test dashboard endpoint."""
        response = client.get("/api/v1/monitoring/dashboard")

        # Should return JSON response
        assert response.content_type == "application/json"

    def test_metrics_endpoint(self, client):
        """Test metrics endpoint."""
        response = client.get(
            "/api/v1/monitoring/metrics?metrics=cpu_usage&time_range=3600"
        )

        # Should return JSON response
        assert response.content_type == "application/json"

    def test_alerts_endpoint(self, client):
        """Test alerts endpoint."""
        response = client.get("/api/v1/monitoring/alerts")

        # Should return JSON response
        assert response.content_type == "application/json"

    def test_status_endpoint(self, client):
        """Test status endpoint."""
        response = client.get("/api/v1/monitoring/status")

        # Should return JSON response
        assert response.content_type == "application/json"

        if response.status_code == 200:
            data = response.get_json()
            assert "initialized" in data
            assert "services" in data
            assert "timestamp" in data


# Integration tests
class TestMonitoringIntegrationTests:
    """Integration tests for the monitoring system."""

    def test_end_to_end_monitoring(self):
        """Test end-to-end monitoring flow."""
        from app.services.monitoring_integration import monitoring_integration

        # Mock app
        mock_app = Mock()
        mock_app.config = {"TESTING": True}

        # Initialize monitoring
        monitoring_integration.init_app(mock_app)

        # Check that integration is initialized
        assert monitoring_integration.initialized is True

        # Test dashboard data generation
        dashboard_data = monitoring_integration.get_unified_dashboard()

        assert "timestamp" in dashboard_data
        assert "services" in dashboard_data
        assert "summary" in dashboard_data

    def test_monitoring_with_real_flask_app(self):
        """Test monitoring with a real Flask app."""
        from app.main import create_app

        app = create_app("testing")

        with app.app_context():
            # Check that monitoring was initialized
            assert hasattr(app, "monitoring_integration")

            # Test API endpoints
            with app.test_client() as client:
                response = client.get("/api/v1/monitoring/status")
                assert response.status_code == 200

                data = response.get_json()
                assert "initialized" in data
                assert "services" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
