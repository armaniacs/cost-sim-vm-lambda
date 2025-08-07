"""
Unit tests for monitoring API endpoints
Tests all monitoring API routes and error handling
"""
import pytest
import json
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from flask import Flask

from app.api.monitoring_api import monitoring_bp


@pytest.fixture
def mock_current_app():
    """Mock Flask current_app for testing"""
    mock_app = MagicMock()
    with patch('app.api.monitoring_api.current_app', mock_app):
        yield mock_app


class TestMonitoringAPIBlueprint:
    """Test monitoring API blueprint registration and basic functionality"""
    
    @pytest.fixture
    def app(self):
        """Create test Flask app with monitoring blueprint"""
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.register_blueprint(monitoring_bp)
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        with app.test_client() as client:
            yield client
    
    def test_blueprint_registration(self, app):
        """Test that monitoring blueprint is properly registered"""
        # Check if blueprint is registered
        blueprint_names = [bp.name for bp in app.blueprints.values()]
        assert 'monitoring' in blueprint_names


class TestHealthCheckEndpoint:
    """Test /health endpoint"""
    
    @pytest.fixture
    def app(self):
        """Create test Flask app"""
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.register_blueprint(monitoring_bp)
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        with app.test_client() as client:
            yield client
    
    def test_health_check_no_monitoring(self, client):
        """Test health check when monitoring is not initialized"""
        response = client.get('/api/v1/monitoring/health')
        assert response.status_code == 500
        
        data = response.get_json()
        assert data['status'] == 'error'
        assert 'Monitoring not initialized' in data['message']
    
    def test_health_check_with_monitoring(self, mock_current_app, client):
        """Test health check with monitoring initialized"""
        # Mock monitoring integration
        mock_monitoring = MagicMock()
        mock_monitoring.is_service_enabled.return_value = True
        
        mock_observability = MagicMock()
        mock_health_data = {
            'status': 'healthy',
            'services': {'database': 'healthy', 'redis': 'healthy'}
        }
        mock_observability.health_checker.get_health_summary.return_value = mock_health_data
        mock_monitoring.get_service.return_value = mock_observability
        
        mock_current_app.monitoring_integration = mock_monitoring
        
        response = client.get('/api/v1/monitoring/health')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['status'] == 'healthy'
        assert 'services' in data
    
    def test_health_check_basic_monitoring(self, mock_current_app, client):
        """Test health check with basic monitoring (no observability service)"""
        mock_monitoring = MagicMock()
        mock_monitoring.is_service_enabled.return_value = False
        mock_current_app.monitoring_integration = mock_monitoring
        
        response = client.get('/api/v1/monitoring/health')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['status'] == 'healthy'
        assert data['message'] == 'Basic monitoring active'
    
    def test_health_check_exception_handling(self, mock_current_app, client):
        """Test health check exception handling"""
        mock_monitoring = MagicMock()
        mock_monitoring.is_service_enabled.side_effect = Exception("Service error")
        mock_current_app.monitoring_integration = mock_monitoring
        
        response = client.get('/api/v1/monitoring/health')
        assert response.status_code == 500
        
        data = response.get_json()
        assert data['status'] == 'error'
        assert 'Service error' in data['message']


class TestDashboardEndpoint:
    """Test /dashboard endpoint"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.register_blueprint(monitoring_bp)
        with app.test_client() as client:
            yield client
    
    def test_dashboard_no_monitoring(self, client):
        """Test dashboard when monitoring is not initialized"""
        response = client.get('/api/v1/monitoring/dashboard')
        assert response.status_code == 500
        
        data = response.get_json()
        assert data['error'] == 'Monitoring not initialized'
    
    def test_dashboard_with_monitoring(self, client):
        """Test dashboard with monitoring initialized"""
        # Get the Flask app from the client
        app = client.application
        
        # Create mock monitoring integration
        mock_monitoring = MagicMock()
        mock_dashboard_data = {
            'timestamp': datetime.now().isoformat(),
            'services': {'apm': 'active', 'logging': 'active'},
            'metrics': {'cpu': 45.2, 'memory': 62.1}
        }
        mock_monitoring.get_unified_dashboard.return_value = mock_dashboard_data
        
        # Set monitoring integration on the app
        app.monitoring_integration = mock_monitoring
        
        response = client.get('/api/v1/monitoring/dashboard')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'timestamp' in data
        assert 'services' in data
        assert 'metrics' in data
    
    def test_dashboard_exception_handling(self, client):
        """Test dashboard exception handling"""
        # Get the Flask app from the client
        app = client.application
        
        # Create mock monitoring integration that raises exception
        mock_monitoring = MagicMock()
        mock_monitoring.get_unified_dashboard.side_effect = Exception("Dashboard error")
        
        # Set monitoring integration on the app
        app.monitoring_integration = mock_monitoring
        
        response = client.get('/api/v1/monitoring/dashboard')
        assert response.status_code == 500
        
        data = response.get_json()
        assert data['error'] == 'Dashboard error'


class TestMetricsEndpoints:
    """Test metrics endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.register_blueprint(monitoring_bp)
        with app.test_client() as client:
            yield client
    
    def test_get_metrics_no_monitoring(self, client):
        """Test GET /metrics when monitoring is not initialized"""
        response = client.get('/api/v1/monitoring/metrics')
        assert response.status_code == 500
        
        data = response.get_json()
        assert data['error'] == 'Monitoring not initialized'
    
    def test_get_metrics_with_observability(self, mock_current_app, client):
        """Test GET /metrics with observability service"""
        mock_monitoring = MagicMock()
        mock_monitoring.is_service_enabled.return_value = True
        
        mock_observability = MagicMock()
        mock_metrics_data = {
            'cpu_usage': [{'timestamp': '2023-01-01T00:00:00', 'value': 45.2}],
            'memory_usage': [{'timestamp': '2023-01-01T00:00:00', 'value': 62.1}]
        }
        mock_observability.get_metrics_for_dashboard.return_value = mock_metrics_data
        mock_monitoring.get_service.return_value = mock_observability
        mock_current_app.monitoring_integration = mock_monitoring
        
        response = client.get('/api/v1/monitoring/metrics?metrics=cpu_usage&metrics=memory_usage&time_range=3600')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'cpu_usage' in data
        assert 'memory_usage' in data
    
    def test_get_metrics_no_observability(self, mock_current_app, client):
        """Test GET /metrics without observability service"""
        mock_monitoring = MagicMock()
        mock_monitoring.is_service_enabled.return_value = False
        mock_current_app.monitoring_integration = mock_monitoring
        
        response = client.get('/api/v1/monitoring/metrics')
        assert response.status_code == 404
        
        data = response.get_json()
        assert data['error'] == 'Observability service not available'
    
    def test_post_metrics_no_monitoring(self, client):
        """Test POST /metrics when monitoring is not initialized"""
        metric_data = {
            'name': 'test_metric',
            'value': 42.0,
            'timestamp': datetime.now().isoformat(),
            'tags': {'environment': 'test'}
        }
        
        response = client.post('/api/v1/monitoring/metrics', 
                             json=metric_data,
                             content_type='application/json')
        assert response.status_code == 500
        
        data = response.get_json()
        assert data['error'] == 'Monitoring not initialized'
    
    def test_post_metrics_with_observability(self, mock_current_app, client):
        """Test POST /metrics with observability service"""
        mock_monitoring = MagicMock()
        mock_monitoring.is_service_enabled.return_value = True
        
        mock_observability = MagicMock()
        mock_observability.record_metric.return_value = True
        mock_monitoring.get_service.return_value = mock_observability
        mock_current_app.monitoring_integration = mock_monitoring
        
        metric_data = {
            'name': 'test_metric',
            'value': 42.0,
            'timestamp': datetime.now().isoformat(),
            'tags': {'environment': 'test'}
        }
        
        response = client.post('/api/v1/monitoring/metrics',
                             json=metric_data,
                             content_type='application/json')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['status'] == 'recorded'
    
    def test_post_metrics_invalid_data(self, mock_current_app, client):
        """Test POST /metrics with invalid data"""
        mock_monitoring = MagicMock()
        mock_current_app.monitoring_integration = mock_monitoring
        
        # Missing required fields
        invalid_data = {'name': 'test_metric'}
        
        response = client.post('/api/v1/monitoring/metrics',
                             json=invalid_data,
                             content_type='application/json')
        assert response.status_code == 400
        
        data = response.get_json()
        assert 'error' in data
        assert 'required' in data['error'].lower()


class TestAlertsEndpoints:
    """Test alerts endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.register_blueprint(monitoring_bp)
        with app.test_client() as client:
            yield client
    
    def test_get_alerts_no_monitoring(self, client):
        """Test GET /alerts when monitoring is not initialized"""
        response = client.get('/api/v1/monitoring/alerts')
        assert response.status_code == 500
    
    def test_get_alerts_with_alerting(self, mock_current_app, client):
        """Test GET /alerts with alerting service"""
        mock_monitoring = MagicMock()
        mock_monitoring.is_service_enabled.return_value = True
        
        mock_alerting = MagicMock()
        mock_alerts = [
            {'id': 'alert1', 'severity': 'high', 'message': 'CPU usage high'},
            {'id': 'alert2', 'severity': 'medium', 'message': 'Memory usage elevated'}
        ]
        mock_alerting.get_active_alerts.return_value = mock_alerts
        mock_monitoring.get_service.return_value = mock_alerting
        mock_current_app.monitoring_integration = mock_monitoring
        
        response = client.get('/api/v1/monitoring/alerts')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'active_alerts' in data
        assert len(data['active_alerts']) == 2
    
    def test_alert_search_no_monitoring(self, client):
        """Test POST /alerts/search when monitoring is not initialized"""
        search_data = {
            'severity': 'high',
            'time_range': 3600
        }
        
        response = client.post('/api/v1/monitoring/alerts/search',
                             json=search_data,
                             content_type='application/json')
        assert response.status_code == 500
    
    def test_acknowledge_alert(self, mock_current_app, client):
        """Test POST /alerts/<id>/acknowledge"""
        mock_monitoring = MagicMock()
        mock_monitoring.is_service_enabled.return_value = True
        
        mock_alerting = MagicMock()
        mock_alerting.acknowledge_alert.return_value = True
        mock_monitoring.get_service.return_value = mock_alerting
        mock_current_app.monitoring_integration = mock_monitoring
        
        response = client.post('/api/v1/monitoring/alerts/alert123/acknowledge',
                             json={'user': 'test_user'},
                             content_type='application/json')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['status'] == 'acknowledged'
    
    def test_suppress_alert(self, mock_current_app, client):
        """Test POST /alerts/<id>/suppress"""
        mock_monitoring = MagicMock()
        mock_monitoring.is_service_enabled.return_value = True
        
        mock_alerting = MagicMock()
        mock_alerting.suppress_alert.return_value = True
        mock_monitoring.get_service.return_value = mock_alerting
        mock_current_app.monitoring_integration = mock_monitoring
        
        response = client.post('/api/v1/monitoring/alerts/alert123/suppress',
                             json={'duration': 3600, 'reason': 'maintenance'},
                             content_type='application/json')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['status'] == 'suppressed'


class TestTracesEndpoints:
    """Test traces endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.register_blueprint(monitoring_bp)
        with app.test_client() as client:
            yield client
    
    def test_get_traces_no_monitoring(self, client):
        """Test GET /traces when monitoring is not initialized"""
        response = client.get('/api/v1/monitoring/traces')
        assert response.status_code == 500
    
    def test_get_traces_with_apm(self, mock_current_app, client):
        """Test GET /traces with APM service"""
        mock_monitoring = MagicMock()
        mock_monitoring.is_service_enabled.return_value = True
        
        mock_apm = MagicMock()
        mock_traces = [
            {'trace_id': 'trace1', 'duration': 150, 'operation': 'api_call'},
            {'trace_id': 'trace2', 'duration': 89, 'operation': 'database_query'}
        ]
        mock_apm.get_recent_traces.return_value = mock_traces
        mock_monitoring.get_service.return_value = mock_apm
        mock_current_app.monitoring_integration = mock_monitoring
        
        response = client.get('/api/v1/monitoring/traces?limit=10&time_range=3600')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'traces' in data
        assert len(data['traces']) == 2
    
    def test_trace_search_no_monitoring(self, client):
        """Test POST /traces/search when monitoring is not initialized"""
        search_data = {
            'operation': 'api_call',
            'min_duration': 100,
            'time_range': 3600
        }
        
        response = client.post('/api/v1/monitoring/traces/search',
                             json=search_data,
                             content_type='application/json')
        assert response.status_code == 500


class TestLogsEndpoints:
    """Test logs endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.register_blueprint(monitoring_bp)
        with app.test_client() as client:
            yield client
    
    def test_get_logs_no_monitoring(self, client):
        """Test GET /logs when monitoring is not initialized"""
        response = client.get('/api/v1/monitoring/logs')
        assert response.status_code == 500
    
    def test_get_logs_with_logging(self, mock_current_app, client):
        """Test GET /logs with logging service"""
        mock_monitoring = MagicMock()
        mock_monitoring.is_service_enabled.return_value = True
        
        mock_logging = MagicMock()
        mock_logs = [
            {'timestamp': '2023-01-01T00:00:00', 'level': 'INFO', 'message': 'Test message 1'},
            {'timestamp': '2023-01-01T00:01:00', 'level': 'ERROR', 'message': 'Test error message'}
        ]
        mock_logging.aggregator.get_recent_logs.return_value = mock_logs
        mock_monitoring.get_service.return_value = mock_logging
        mock_current_app.monitoring_integration = mock_monitoring
        
        response = client.get('/api/v1/monitoring/logs?level=INFO&limit=50')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'logs' in data
        assert len(data['logs']) == 2
    
    def test_log_search_no_monitoring(self, client):
        """Test POST /logs/search when monitoring is not initialized"""
        search_data = {
            'level': 'ERROR',
            'message_contains': 'database',
            'time_range': 3600
        }
        
        response = client.post('/api/v1/monitoring/logs/search',
                             json=search_data,
                             content_type='application/json')
        assert response.status_code == 500


class TestPerformanceEndpoints:
    """Test performance endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.register_blueprint(monitoring_bp)
        with app.test_client() as client:
            yield client
    
    def test_get_performance_no_monitoring(self, client):
        """Test GET /performance when monitoring is not initialized"""
        response = client.get('/api/v1/monitoring/performance')
        assert response.status_code == 500
    
    def test_get_performance_with_monitoring(self, mock_current_app, client):
        """Test GET /performance with monitoring"""
        mock_monitoring = MagicMock()
        mock_performance_data = {
            'response_times': {'avg': 150, 'p95': 300, 'p99': 500},
            'throughput': {'requests_per_second': 100},
            'error_rates': {'total_errors': 5, 'error_percentage': 2.1}
        }
        mock_monitoring.get_performance_metrics.return_value = mock_performance_data
        mock_current_app.monitoring_integration = mock_monitoring
        
        response = client.get('/api/v1/monitoring/performance?time_range=3600')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'response_times' in data
        assert 'throughput' in data
        assert 'error_rates' in data
    
    def test_get_sla_no_monitoring(self, client):
        """Test GET /sla when monitoring is not initialized"""
        response = client.get('/api/v1/monitoring/sla')
        assert response.status_code == 500
    
    def test_get_dependencies_no_monitoring(self, client):
        """Test GET /dependencies when monitoring is not initialized"""
        response = client.get('/api/v1/monitoring/dependencies')
        assert response.status_code == 500


class TestConfigurationEndpoints:
    """Test configuration endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.register_blueprint(monitoring_bp)
        with app.test_client() as client:
            yield client
    
    def test_get_config_no_monitoring(self, client):
        """Test GET /config when monitoring is not initialized"""
        response = client.get('/api/v1/monitoring/config')
        assert response.status_code == 500
    
    def test_get_config_with_monitoring(self, mock_current_app, client):
        """Test GET /config with monitoring"""
        mock_monitoring = MagicMock()
        mock_config = {
            'apm': {'sampling_rate': 0.1, 'enabled': True},
            'logging': {'level': 'INFO', 'retention_days': 30},
            'alerting': {'email_enabled': True, 'slack_enabled': False}
        }
        mock_monitoring.config.get_all.return_value = mock_config
        mock_current_app.monitoring_integration = mock_monitoring
        
        response = client.get('/api/v1/monitoring/config')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'apm' in data
        assert 'logging' in data
        assert 'alerting' in data
    
    def test_put_config_no_monitoring(self, client):
        """Test PUT /config when monitoring is not initialized"""
        config_data = {
            'apm.sampling_rate': 0.2,
            'logging.level': 'DEBUG'
        }
        
        response = client.put('/api/v1/monitoring/config',
                            json=config_data,
                            content_type='application/json')
        assert response.status_code == 500
    
    def test_put_config_with_monitoring(self, mock_current_app, client):
        """Test PUT /config with monitoring"""
        mock_monitoring = MagicMock()
        mock_monitoring.config.set.return_value = True
        mock_current_app.monitoring_integration = mock_monitoring
        
        config_data = {
            'apm.sampling_rate': 0.2,
            'logging.level': 'DEBUG'
        }
        
        response = client.put('/api/v1/monitoring/config',
                            json=config_data,
                            content_type='application/json')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['status'] == 'updated'


class TestStatusAndEventsEndpoints:
    """Test status and events endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.register_blueprint(monitoring_bp)
        with app.test_client() as client:
            yield client
    
    def test_get_status_no_monitoring(self, client):
        """Test GET /status when monitoring is not initialized"""
        response = client.get('/api/v1/monitoring/status')
        assert response.status_code == 500
    
    def test_get_status_with_monitoring(self, mock_current_app, client):
        """Test GET /status with monitoring"""
        mock_monitoring = MagicMock()
        mock_monitoring.initialized = True
        mock_monitoring.services = {
            'apm': MagicMock(name='APM Service'),
            'logging': MagicMock(name='Logging Service')
        }
        mock_current_app.monitoring_integration = mock_monitoring
        
        response = client.get('/api/v1/monitoring/status')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['initialized'] is True
        assert 'services' in data
        assert 'timestamp' in data
    
    def test_post_events_no_monitoring(self, client):
        """Test POST /events when monitoring is not initialized"""
        event_data = {
            'type': 'custom',
            'event': 'user_action',
            'details': {'action': 'login', 'user': 'test_user'},
            'user_id': 'test_user'
        }
        
        response = client.post('/api/v1/monitoring/events',
                             json=event_data,
                             content_type='application/json')
        assert response.status_code == 500
    
    def test_post_events_with_monitoring(self, mock_current_app, client):
        """Test POST /events with monitoring"""
        mock_monitoring = MagicMock()
        mock_monitoring.record_custom_event.return_value = True
        mock_current_app.monitoring_integration = mock_monitoring
        
        event_data = {
            'type': 'custom',
            'event': 'user_action',
            'details': {'action': 'login', 'user': 'test_user'},
            'user_id': 'test_user'
        }
        
        response = client.post('/api/v1/monitoring/events',
                             json=event_data,
                             content_type='application/json')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['status'] == 'success'
        assert 'recorded' in data['message']


class TestMonitoringAPIErrorHandling:
    """Test error handling across all endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.register_blueprint(monitoring_bp)
        with app.test_client() as client:
            yield client
    
    def test_general_exception_handling(self, mock_current_app, client):
        """Test general exception handling across endpoints"""
        # Mock monitoring to raise exception
        mock_monitoring = MagicMock()
        mock_monitoring.get_unified_dashboard.side_effect = Exception("General error")
        mock_current_app.monitoring_integration = mock_monitoring
        
        # Test multiple endpoints handle exceptions gracefully
        endpoints = [
            '/api/v1/monitoring/dashboard',
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 500
            
            data = response.get_json()
            assert 'error' in data
    
    def test_invalid_json_handling(self, client):
        """Test handling of invalid JSON in POST requests"""
        # Test with malformed JSON
        response = client.post('/api/v1/monitoring/metrics',
                             data='{"invalid": json}',
                             content_type='application/json')
        
        # Should handle malformed JSON gracefully
        assert response.status_code in [400, 500]
    
    def test_missing_content_type(self, client):
        """Test handling of missing content type in POST requests"""
        response = client.post('/api/v1/monitoring/metrics',
                             data='{"name": "test"}')
        
        # Should handle missing content type
        assert response.status_code in [400, 415, 500]


class TestMonitoringAPIRequestParameters:
    """Test request parameter handling"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.register_blueprint(monitoring_bp)
        with app.test_client() as client:
            yield client
    
    def test_metrics_query_parameters(self, mock_current_app, client):
        """Test metrics endpoint query parameter handling"""
        mock_monitoring = MagicMock()
        mock_monitoring.is_service_enabled.return_value = True
        
        mock_observability = MagicMock()
        mock_observability.get_metrics_for_dashboard.return_value = {}
        mock_monitoring.get_service.return_value = mock_observability
        mock_current_app.monitoring_integration = mock_monitoring
        
        # Test with various parameter combinations
        test_cases = [
            '/api/v1/monitoring/metrics',  # No parameters
            '/api/v1/monitoring/metrics?metrics=cpu',  # Single metric
            '/api/v1/monitoring/metrics?metrics=cpu&metrics=memory',  # Multiple metrics
            '/api/v1/monitoring/metrics?time_range=7200',  # Custom time range
            '/api/v1/monitoring/metrics?metrics=cpu&time_range=1800',  # Combined
        ]
        
        for url in test_cases:
            response = client.get(url)
            assert response.status_code == 200
    
    def test_invalid_time_range_parameter(self, mock_current_app, client):
        """Test handling of invalid time_range parameter"""
        mock_monitoring = MagicMock()
        mock_monitoring.is_service_enabled.return_value = True
        mock_current_app.monitoring_integration = mock_monitoring
        
        # Test with non-numeric time_range
        response = client.get('/api/v1/monitoring/metrics?time_range=invalid')
        assert response.status_code == 500  # Should handle conversion error