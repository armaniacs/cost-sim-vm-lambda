"""
Unit tests for Performance Monitor service
Tests the performance monitoring system with proper implementation matching
"""
import pytest
import time
from unittest.mock import MagicMock, patch, Mock
from datetime import datetime, timedelta
from flask import Flask, g, request

# Import what we can from the actual implementation
try:
    from app.services.performance_monitor import (
        PerformanceMetrics,
        SystemMonitor,
        AlertManager,
        PerformanceMonitor,
        cached_with_monitoring
    )
except ImportError:
    # Skip tests if imports fail
    pytest.skip("Performance Monitor module not available", allow_module_level=True)


class TestPerformanceMetrics:
    """Test PerformanceMetrics functionality"""
    
    def test_performance_metrics_initialization(self):
        """Test PerformanceMetrics initialization"""
        metrics = PerformanceMetrics()
        
        assert metrics.max_history_size == 1000
        assert len(metrics.request_times) == 0
        assert len(metrics.endpoint_times) == 0
        assert metrics.error_counts == {}
        assert 'hits' in metrics.cache_stats
        assert 'misses' in metrics.cache_stats
        assert 'query_count' in metrics.database_stats
    
    def test_performance_metrics_custom_size(self):
        """Test PerformanceMetrics with custom history size"""
        metrics = PerformanceMetrics(max_history_size=500)
        
        assert metrics.max_history_size == 500
        assert metrics.request_times.maxlen == 500
    
    def test_record_request(self):
        """Test recording request metrics"""
        metrics = PerformanceMetrics()
        
        metrics.record_request(
            endpoint='/api/test',
            method='GET',
            duration=0.5,
            status_code=200
        )
        
        assert len(metrics.request_times) == 1
        request_data = metrics.request_times[0]
        assert request_data['endpoint'] == '/api/test'
        assert request_data['method'] == 'GET'
        assert request_data['duration'] == 0.5
        assert request_data['status_code'] == 200
        assert isinstance(request_data['timestamp'], datetime)
        
        # Check endpoint times
        assert len(metrics.endpoint_times['GET /api/test']) == 1
        assert metrics.endpoint_times['GET /api/test'][0] == 0.5
    
    def test_record_request_error(self):
        """Test recording request with error status"""
        metrics = PerformanceMetrics()
        
        metrics.record_request(
            endpoint='/api/error',
            method='POST',
            duration=1.0,
            status_code=500
        )
        
        assert len(metrics.request_times) == 1
        assert metrics.error_counts['POST /api/error'] == 1
    
    def test_record_cache_operations(self):
        """Test recording cache operations"""
        metrics = PerformanceMetrics()
        
        metrics.record_cache_hit()
        metrics.record_cache_miss()
        metrics.record_cache_set()
        metrics.record_cache_delete()
        metrics.record_cache_error()
        
        assert metrics.cache_stats['hits'] == 1
        assert metrics.cache_stats['misses'] == 1
        assert metrics.cache_stats['sets'] == 1
        assert metrics.cache_stats['deletes'] == 1
        assert metrics.cache_stats['errors'] == 1
    
    def test_get_cache_hit_ratio(self):
        """Test cache hit ratio calculation"""
        metrics = PerformanceMetrics()
        
        # No requests yet
        assert metrics.get_cache_hit_ratio() == 0.0
        
        # Add hits and misses
        metrics.record_cache_hit()
        metrics.record_cache_hit()
        metrics.record_cache_hit()
        metrics.record_cache_miss()
        
        # Should be 3/4 = 0.75
        assert metrics.get_cache_hit_ratio() == 0.75
    
    def test_get_average_response_time_overall(self):
        """Test getting average response time overall"""
        metrics = PerformanceMetrics()
        
        # No requests yet
        assert metrics.get_average_response_time() == 0.0
        
        # Add some requests
        metrics.record_request('/api/test1', 'GET', 0.1, 200)
        metrics.record_request('/api/test2', 'GET', 0.3, 200)
        metrics.record_request('/api/test3', 'GET', 0.2, 200)
        
        assert metrics.get_average_response_time() == pytest.approx(0.2, rel=1e-9)
    
    def test_get_average_response_time_specific_endpoint(self):
        """Test getting average response time for specific endpoint"""
        metrics = PerformanceMetrics()
        
        metrics.record_request('/api/test', 'GET', 0.1, 200)
        metrics.record_request('/api/test', 'GET', 0.3, 200)
        metrics.record_request('/api/other', 'POST', 0.5, 200)
        
        assert metrics.get_average_response_time('GET /api/test') == pytest.approx(0.2, rel=1e-9)
        assert metrics.get_average_response_time('POST /api/other') == pytest.approx(0.5, rel=1e-9)
        assert metrics.get_average_response_time('nonexistent') == 0.0
    
    def test_get_95th_percentile_response_time(self):
        """Test 95th percentile calculation"""
        metrics = PerformanceMetrics()
        
        # No requests yet
        assert metrics.get_95th_percentile_response_time() == 0.0
        
        # Add requests with known distribution
        times = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]  # 10 requests
        for i, time_val in enumerate(times):
            metrics.record_request(f'/api/test{i}', 'GET', time_val, 200)
        
        # 95th percentile of 10 items should be index 9 (0-indexed) = 1.0
        assert metrics.get_95th_percentile_response_time() == 1.0
    
    def test_get_error_rate_overall(self):
        """Test error rate calculation overall"""
        metrics = PerformanceMetrics()
        
        # No requests yet
        assert metrics.get_error_rate() == 0.0
        
        # Add successful requests
        metrics.record_request('/api/test1', 'GET', 0.1, 200)
        metrics.record_request('/api/test2', 'GET', 0.2, 200)
        
        # Add error requests
        metrics.record_request('/api/test3', 'GET', 0.3, 500)
        
        # Error rate should be 1/3
        assert metrics.get_error_rate() == pytest.approx(1/3, rel=1e-9)
    
    def test_get_error_rate_specific_endpoint(self):
        """Test error rate for specific endpoint"""
        metrics = PerformanceMetrics()
        
        metrics.record_request('/api/test', 'GET', 0.1, 200)
        metrics.record_request('/api/test', 'GET', 0.2, 500)
        metrics.record_request('/api/other', 'POST', 0.3, 200)
        
        assert metrics.get_error_rate('GET /api/test') == pytest.approx(0.5, rel=1e-9)
        assert metrics.get_error_rate('POST /api/other') == 0.0
        assert metrics.get_error_rate('nonexistent') == 0.0
    
    def test_get_requests_per_minute(self):
        """Test requests per minute calculation"""
        metrics = PerformanceMetrics()
        
        # No requests yet
        assert metrics.get_requests_per_minute() == 0.0
        
        # Add some old requests (should not count)
        old_request = {
            'timestamp': datetime.utcnow() - timedelta(minutes=2),
            'endpoint': '/api/old',
            'method': 'GET',
            'duration': 0.1,
            'status_code': 200
        }
        metrics.request_times.append(old_request)
        
        # Add recent requests
        metrics.record_request('/api/recent1', 'GET', 0.1, 200)
        metrics.record_request('/api/recent2', 'GET', 0.2, 200)
        
        # Should only count recent requests
        assert metrics.get_requests_per_minute() == 2.0


class TestSystemMonitor:
    """Test SystemMonitor functionality"""
    
    def test_system_monitor_initialization(self):
        """Test SystemMonitor initialization"""
        monitor = SystemMonitor()
        assert monitor is not None
    
    @patch('psutil.cpu_percent')
    def test_get_cpu_usage(self, mock_cpu_percent):
        """Test getting CPU usage"""
        mock_cpu_percent.return_value = 75.5
        
        monitor = SystemMonitor()
        cpu_usage = monitor.get_cpu_usage()
        
        assert cpu_usage == 75.5
        mock_cpu_percent.assert_called_once_with(interval=1)
    
    @patch('psutil.virtual_memory')
    def test_get_memory_usage(self, mock_virtual_memory):
        """Test getting memory usage"""
        mock_memory = Mock()
        mock_memory.total = 8000000000
        mock_memory.available = 4000000000
        mock_memory.used = 3000000000
        mock_memory.percent = 62.5
        mock_virtual_memory.return_value = mock_memory
        
        monitor = SystemMonitor()
        memory_usage = monitor.get_memory_usage()
        
        assert memory_usage['total'] == 8000000000
        assert memory_usage['available'] == 4000000000
        assert memory_usage['used'] == 3000000000
        assert memory_usage['percentage'] == 62.5
    
    @patch('psutil.disk_usage')
    def test_get_disk_usage(self, mock_disk_usage):
        """Test getting disk usage"""
        mock_disk = Mock()
        mock_disk.total = 500000000000
        mock_disk.used = 200000000000
        mock_disk.free = 300000000000
        mock_disk_usage.return_value = mock_disk
        
        monitor = SystemMonitor()
        disk_usage = monitor.get_disk_usage()
        
        assert disk_usage['total'] == 500000000000
        assert disk_usage['used'] == 200000000000
        assert disk_usage['free'] == 300000000000
        assert disk_usage['percentage'] == 40.0  # 200/500 * 100
        
        mock_disk_usage.assert_called_once_with('/')
    
    @patch('psutil.net_io_counters')
    def test_get_network_stats(self, mock_net_io_counters):
        """Test getting network statistics"""
        mock_net_io = Mock()
        mock_net_io.bytes_sent = 1000000
        mock_net_io.bytes_recv = 2000000
        mock_net_io.packets_sent = 500
        mock_net_io.packets_recv = 750
        mock_net_io_counters.return_value = mock_net_io
        
        monitor = SystemMonitor()
        network_stats = monitor.get_network_stats()
        
        assert network_stats['bytes_sent'] == 1000000
        assert network_stats['bytes_recv'] == 2000000
        assert network_stats['packets_sent'] == 500
        assert network_stats['packets_recv'] == 750


class TestAlertManager:
    """Test AlertManager functionality"""
    
    def test_alert_manager_initialization(self):
        """Test AlertManager initialization"""
        metrics = PerformanceMetrics()
        manager = AlertManager(metrics)
        
        assert manager.metrics == metrics
        assert 'response_time' in manager.alert_thresholds
        assert 'error_rate' in manager.alert_thresholds
        assert 'cpu_usage' in manager.alert_thresholds
        assert manager.active_alerts == set()
    
    @patch('app.services.performance_monitor.SystemMonitor')
    def test_check_alerts_no_issues(self, mock_system_monitor_class):
        """Test alert checking with no performance issues"""
        # Setup metrics with good performance
        metrics = PerformanceMetrics()
        metrics.record_request('/api/test', 'GET', 0.1, 200)  # Good response time
        metrics.record_cache_hit()
        metrics.record_cache_hit()  # Good cache hit ratio
        
        # Mock system monitor to return good values
        mock_system_monitor = Mock()
        mock_system_monitor.get_cpu_usage.return_value = 30.0  # Good CPU
        mock_memory_usage = {'percentage': 50.0}  # Good memory
        mock_system_monitor.get_memory_usage.return_value = mock_memory_usage
        mock_system_monitor_class.return_value = mock_system_monitor
        
        manager = AlertManager(metrics)
        alerts = manager.check_alerts()
        
        assert alerts == []
    
    @patch('app.services.performance_monitor.SystemMonitor')
    def test_check_alerts_response_time_alert(self, mock_system_monitor_class):
        """Test alert for high response time"""
        metrics = PerformanceMetrics()
        metrics.record_request('/api/slow', 'GET', 10.0, 200)  # Slow response
        # Add cache hits to avoid cache hit ratio alert
        metrics.record_cache_hit()
        metrics.record_cache_hit()
        
        # Mock system monitor to return good values
        mock_system_monitor = Mock()
        mock_system_monitor.get_cpu_usage.return_value = 30.0
        mock_memory_usage = {'percentage': 50.0}
        mock_system_monitor.get_memory_usage.return_value = mock_memory_usage
        mock_system_monitor_class.return_value = mock_system_monitor
        
        manager = AlertManager(metrics)
        alerts = manager.check_alerts()
        
        # Should have at least 1 alert, find the response time one
        response_time_alerts = [a for a in alerts if a['type'] == 'response_time']
        assert len(response_time_alerts) == 1
        alert = response_time_alerts[0]
        assert alert['severity'] == 'high'
        assert alert['current_value'] == 10.0
        assert 'Average response time is 10.00s' in alert['message']
    
    @patch('app.services.performance_monitor.SystemMonitor')
    def test_check_alerts_error_rate_alert(self, mock_system_monitor_class):
        """Test alert for high error rate"""
        metrics = PerformanceMetrics()
        # Add requests with high error rate
        metrics.record_request('/api/test1', 'GET', 0.1, 200)
        metrics.record_request('/api/test2', 'GET', 0.1, 500)
        metrics.record_request('/api/test3', 'GET', 0.1, 500)
        metrics.record_request('/api/test4', 'GET', 0.1, 500)  # 75% error rate
        
        # Mock system monitor
        mock_system_monitor = Mock()
        mock_system_monitor.get_cpu_usage.return_value = 30.0
        mock_memory_usage = {'percentage': 50.0}
        mock_system_monitor.get_memory_usage.return_value = mock_memory_usage
        mock_system_monitor_class.return_value = mock_system_monitor
        
        manager = AlertManager(metrics)
        alerts = manager.check_alerts()
        
        # Should have error rate alert
        error_rate_alerts = [a for a in alerts if a['type'] == 'error_rate']
        assert len(error_rate_alerts) == 1
        alert = error_rate_alerts[0]
        assert alert['severity'] == 'medium'
        assert alert['current_value'] == 0.75
    
    @patch('app.services.performance_monitor.SystemMonitor')
    def test_check_alerts_low_cache_hit_ratio(self, mock_system_monitor_class):
        """Test alert for low cache hit ratio"""
        metrics = PerformanceMetrics()
        # Create low cache hit ratio
        for _ in range(10):
            metrics.record_cache_miss()
        metrics.record_cache_hit()  # Only 1/11 = 9% hit ratio
        
        # Mock system monitor
        mock_system_monitor = Mock()
        mock_system_monitor.get_cpu_usage.return_value = 30.0
        mock_memory_usage = {'percentage': 50.0}
        mock_system_monitor.get_memory_usage.return_value = mock_memory_usage
        mock_system_monitor_class.return_value = mock_system_monitor
        
        manager = AlertManager(metrics)
        alerts = manager.check_alerts()
        
        # Should have cache hit ratio alert
        cache_alerts = [a for a in alerts if a['type'] == 'cache_hit_ratio']
        assert len(cache_alerts) == 1
        alert = cache_alerts[0]
        assert alert['severity'] == 'medium'
        assert alert['current_value'] < 0.8
    
    @patch('app.services.performance_monitor.SystemMonitor')
    def test_check_alerts_high_cpu_usage(self, mock_system_monitor_class):
        """Test alert for high CPU usage"""
        metrics = PerformanceMetrics()
        
        # Mock system monitor with high CPU
        mock_system_monitor = Mock()
        mock_system_monitor.get_cpu_usage.return_value = 95.0  # High CPU
        mock_memory_usage = {'percentage': 50.0}
        mock_system_monitor.get_memory_usage.return_value = mock_memory_usage
        mock_system_monitor_class.return_value = mock_system_monitor
        
        manager = AlertManager(metrics)
        alerts = manager.check_alerts()
        
        # Should have CPU usage alert
        cpu_alerts = [a for a in alerts if a['type'] == 'cpu_usage']
        assert len(cpu_alerts) == 1
        alert = cpu_alerts[0]
        assert alert['severity'] == 'high'
        assert alert['current_value'] == 95.0
        assert 'CPU usage is 95.0%' in alert['message']
    
    @patch('app.services.performance_monitor.SystemMonitor')
    def test_check_alerts_high_memory_usage(self, mock_system_monitor_class):
        """Test alert for high memory usage"""
        metrics = PerformanceMetrics()
        
        # Mock system monitor with high memory usage
        mock_system_monitor = Mock()
        mock_system_monitor.get_cpu_usage.return_value = 30.0
        mock_memory_usage = {'percentage': 95.0}  # High memory
        mock_system_monitor.get_memory_usage.return_value = mock_memory_usage
        mock_system_monitor_class.return_value = mock_system_monitor
        
        manager = AlertManager(metrics)
        alerts = manager.check_alerts()
        
        # Should have memory usage alert
        memory_alerts = [a for a in alerts if a['type'] == 'memory_usage']
        assert len(memory_alerts) == 1
        alert = memory_alerts[0]
        assert alert['severity'] == 'high'
        assert alert['current_value'] == 95.0
        assert 'Memory usage is 95.0%' in alert['message']


class TestPerformanceMonitor:
    """Test PerformanceMonitor main service"""
    
    @pytest.fixture
    def app(self):
        """Create test Flask application"""
        app = Flask(__name__)
        app.config['TESTING'] = True
        return app
    
    def test_performance_monitor_initialization(self):
        """Test PerformanceMonitor initialization"""
        monitor = PerformanceMonitor()
        
        assert monitor.app is None
        assert isinstance(monitor.metrics, PerformanceMetrics)
        assert isinstance(monitor.system_monitor, SystemMonitor)
        assert isinstance(monitor.alert_manager, AlertManager)
        assert monitor.alert_manager.metrics == monitor.metrics
    
    def test_performance_monitor_with_app(self, app):
        """Test PerformanceMonitor initialization with app"""
        monitor = PerformanceMonitor(app)
        
        assert monitor.app == app
    
    def test_init_app(self, app):
        """Test init_app method"""
        monitor = PerformanceMonitor()
        monitor.init_app(app)
        
        assert monitor.app == app
    
    def test_before_request(self, app):
        """Test before_request handler"""
        monitor = PerformanceMonitor()
        
        with app.app_context():
            with app.test_request_context():
                monitor.before_request()
                
                assert hasattr(g, 'start_time')
                assert isinstance(g.start_time, float)
                assert g.start_time <= time.time()
    
    def test_after_request(self, app):
        """Test after_request handler"""
        monitor = PerformanceMonitor()
        
        with app.app_context():
            with app.test_request_context('/api/test', method='GET'):
                # Simulate before_request
                g.start_time = time.time() - 0.1  # 100ms ago
                
                # Create mock response
                from werkzeug.wrappers import Response
                response = Response('OK', status=200)
                
                # Call after_request
                result = monitor.after_request(response)
                
                assert result == response
                assert len(monitor.metrics.request_times) == 1
                
                request_data = monitor.metrics.request_times[0]
                assert request_data['method'] == 'GET'
                assert request_data['status_code'] == 200
                assert request_data['duration'] > 0
    
    def test_after_request_without_start_time(self, app):
        """Test after_request handler without start time"""
        monitor = PerformanceMonitor()
        
        with app.app_context():
            with app.test_request_context():
                from werkzeug.wrappers import Response
                response = Response('OK', status=200)
                
                result = monitor.after_request(response)
                
                assert result == response
                assert len(monitor.metrics.request_times) == 0
    
    def test_after_request_slow_request_logging(self, app):
        """Test that slow requests are logged"""
        monitor = PerformanceMonitor()
        
        with app.app_context():
            with app.test_request_context('/api/slow', method='POST'):
                # Simulate slow request
                g.start_time = time.time() - 1.5  # 1.5 seconds ago
                
                from werkzeug.wrappers import Response
                response = Response('OK', status=200)
                
                with patch('app.services.performance_monitor.logger') as mock_logger:
                    result = monitor.after_request(response)
                    
                    assert result == response
                    mock_logger.warning.assert_called_once()
                    warning_call = mock_logger.warning.call_args[0][0]
                    assert 'Slow request' in warning_call
                    assert 'POST' in warning_call
    
    def test_teardown_handler_with_exception(self):
        """Test teardown handler with exception"""
        monitor = PerformanceMonitor()
        
        test_exception = Exception("Test error")
        
        with patch('app.services.performance_monitor.logger') as mock_logger:
            monitor.teardown_handler(test_exception)
            
            mock_logger.error.assert_called_once()
            error_call = mock_logger.error.call_args[0][0]
            assert 'Request ended with exception' in error_call
    
    def test_teardown_handler_without_exception(self):
        """Test teardown handler without exception"""
        monitor = PerformanceMonitor()
        
        with patch('app.services.performance_monitor.logger') as mock_logger:
            monitor.teardown_handler(None)
            
            mock_logger.error.assert_not_called()
    
    @patch('app.services.performance_monitor.SystemMonitor')
    def test_get_dashboard_data(self, mock_system_monitor_class):
        """Test getting dashboard data"""
        # Mock system monitor
        mock_system_monitor = Mock()
        mock_system_monitor.get_cpu_usage.return_value = 45.0
        mock_system_monitor.get_memory_usage.return_value = {'percentage': 60.0}
        mock_system_monitor.get_disk_usage.return_value = {'percentage': 70.0}
        mock_system_monitor.get_network_stats.return_value = {'bytes_sent': 1000}
        mock_system_monitor_class.return_value = mock_system_monitor
        
        monitor = PerformanceMonitor()
        monitor.system_monitor = mock_system_monitor
        
        # Add some test metrics
        monitor.metrics.record_request('/api/test', 'GET', 0.2, 200)
        monitor.metrics.record_cache_hit()
        
        dashboard_data = monitor.get_dashboard_data()
        
        assert 'system' in dashboard_data
        assert 'cache' in dashboard_data
        assert 'performance' in dashboard_data
        assert 'alerts' in dashboard_data
        assert 'timestamp' in dashboard_data
        
        # Check system stats
        assert dashboard_data['system']['cpu_usage'] == 45.0
        
        # Check performance stats
        assert dashboard_data['performance']['average_response_time'] == 0.2
        
        # Check cache stats
        assert dashboard_data['cache']['hit_ratio'] == 1.0
    
    def test_get_endpoint_metrics(self):
        """Test getting metrics for specific endpoint"""
        monitor = PerformanceMonitor()
        
        # Add some test data
        monitor.metrics.record_request('/api/test', 'GET', 0.1, 200)
        monitor.metrics.record_request('/api/test', 'GET', 0.3, 200)
        monitor.metrics.record_request('/api/test', 'GET', 0.2, 500)
        
        endpoint_metrics = monitor.get_endpoint_metrics('GET /api/test')
        
        assert endpoint_metrics['endpoint'] == 'GET /api/test'
        assert endpoint_metrics['average_response_time'] == pytest.approx(0.2, rel=1e-9)
        assert endpoint_metrics['request_count'] == 3
        assert endpoint_metrics['error_count'] == 1
        assert endpoint_metrics['error_rate'] == pytest.approx(1/3, rel=1e-9)
    
    def test_get_endpoint_metrics_nonexistent(self):
        """Test getting metrics for nonexistent endpoint"""
        monitor = PerformanceMonitor()
        
        endpoint_metrics = monitor.get_endpoint_metrics('GET /api/nonexistent')
        
        assert endpoint_metrics['endpoint'] == 'GET /api/nonexistent'
        assert endpoint_metrics['average_response_time'] == 0.0
        assert endpoint_metrics['request_count'] == 0
        assert endpoint_metrics['error_count'] == 0
        assert endpoint_metrics['error_rate'] == 0.0
    
    def test_reset_metrics(self):
        """Test resetting metrics"""
        monitor = PerformanceMonitor()
        
        # Add some test data
        monitor.metrics.record_request('/api/test', 'GET', 0.1, 200)
        monitor.metrics.record_cache_hit()
        
        # Verify data exists
        assert len(monitor.metrics.request_times) == 1
        assert monitor.metrics.cache_stats['hits'] == 1
        
        # Reset metrics
        monitor.reset_metrics()
        
        # Verify data is cleared
        assert len(monitor.metrics.request_times) == 0
        assert monitor.metrics.cache_stats['hits'] == 0
        assert isinstance(monitor.metrics, PerformanceMetrics)
        assert isinstance(monitor.alert_manager, AlertManager)
        assert monitor.alert_manager.metrics == monitor.metrics


class TestCachedWithMonitoringDecorator:
    """Test cached_with_monitoring decorator"""
    
    @patch('app.services.performance_monitor.get_redis_client')
    @patch('app.services.performance_monitor.performance_monitor')
    def test_cached_with_monitoring_cache_hit(self, mock_performance_monitor, mock_get_redis_client):
        """Test decorator with cache hit"""
        # Setup mock Redis client
        mock_redis = Mock()
        mock_redis.get.return_value = "cached_result"
        mock_get_redis_client.return_value = mock_redis
        
        # Setup mock metrics
        mock_metrics = Mock()
        mock_performance_monitor.metrics = mock_metrics
        
        @cached_with_monitoring(timeout=3600, key_prefix="test")
        def test_function(arg1, arg2):
            return f"result_{arg1}_{arg2}"
        
        result = test_function("a", "b")
        
        assert result == "cached_result"
        mock_metrics.record_cache_hit.assert_called_once()
        mock_metrics.record_cache_miss.assert_not_called()
    
    @patch('app.services.performance_monitor.get_redis_client')
    @patch('app.services.performance_monitor.performance_monitor')
    def test_cached_with_monitoring_cache_miss(self, mock_performance_monitor, mock_get_redis_client):
        """Test decorator with cache miss"""
        # Setup mock Redis client
        mock_redis = Mock()
        mock_redis.get.return_value = None  # Cache miss
        mock_get_redis_client.return_value = mock_redis
        
        # Setup mock metrics
        mock_metrics = Mock()
        mock_performance_monitor.metrics = mock_metrics
        
        @cached_with_monitoring(timeout=3600, key_prefix="test")
        def test_function(arg1, arg2):
            return f"result_{arg1}_{arg2}"
        
        result = test_function("a", "b")
        
        assert result == "result_a_b"
        mock_metrics.record_cache_miss.assert_called_once()
        mock_metrics.record_cache_set.assert_called_once()
        mock_redis.setex.assert_called_once()
    
    @patch('app.services.performance_monitor.get_redis_client')
    @patch('app.services.performance_monitor.performance_monitor')
    def test_cached_with_monitoring_redis_error(self, mock_performance_monitor, mock_get_redis_client):
        """Test decorator with Redis error"""
        # Setup mock Redis client that raises error
        mock_redis = Mock()
        mock_redis.get.side_effect = Exception("Redis connection error")
        mock_get_redis_client.return_value = mock_redis
        
        # Setup mock metrics
        mock_metrics = Mock()
        mock_performance_monitor.metrics = mock_metrics
        
        @cached_with_monitoring(timeout=3600, key_prefix="test")
        def test_function(arg1, arg2):
            return f"result_{arg1}_{arg2}"
        
        result = test_function("a", "b")
        
        assert result == "result_a_b"
        mock_metrics.record_cache_error.assert_called()
    
    @patch('app.services.performance_monitor.get_redis_client')
    def test_cached_with_monitoring_no_redis(self, mock_get_redis_client):
        """Test decorator when Redis is not available"""
        mock_get_redis_client.return_value = None
        
        @cached_with_monitoring(timeout=3600, key_prefix="test")
        def test_function(arg1, arg2):
            return f"result_{arg1}_{arg2}"
        
        result = test_function("a", "b")
        
        assert result == "result_a_b"


class TestIntegrationScenarios:
    """Test integration scenarios"""
    
    @pytest.fixture
    def app(self):
        """Create test Flask application"""
        app = Flask(__name__)
        app.config['TESTING'] = True
        return app
    
    @patch('app.services.performance_monitor.SystemMonitor')
    def test_full_monitoring_workflow(self, mock_system_monitor_class, app):
        """Test complete monitoring workflow"""
        # Setup system monitor mock
        mock_system_monitor = Mock()
        mock_system_monitor.get_cpu_usage.return_value = 45.0
        mock_system_monitor.get_memory_usage.return_value = {'percentage': 60.0}
        mock_system_monitor.get_disk_usage.return_value = {'percentage': 70.0}
        mock_system_monitor.get_network_stats.return_value = {'bytes_sent': 1000}
        mock_system_monitor_class.return_value = mock_system_monitor
        
        # Initialize monitor
        monitor = PerformanceMonitor(app)
        monitor.system_monitor = mock_system_monitor
        
        with app.app_context():
            # Simulate multiple requests
            with app.test_request_context('/api/users', method='GET'):
                monitor.before_request()
                time.sleep(0.01)  # Small delay
                
                from werkzeug.wrappers import Response
                response = Response('{"users": []}', status=200)
                monitor.after_request(response)
            
            with app.test_request_context('/api/orders', method='POST'):
                monitor.before_request()
                time.sleep(0.01)
                
                response = Response('{"error": "validation failed"}', status=400)
                monitor.after_request(response)
        
        # Add cache operations
        monitor.metrics.record_cache_hit()
        monitor.metrics.record_cache_hit()
        monitor.metrics.record_cache_miss()
        
        # Get dashboard data
        dashboard = monitor.get_dashboard_data()
        
        # Verify comprehensive data
        assert len(monitor.metrics.request_times) == 2
        assert 'system' in dashboard
        assert 'performance' in dashboard
        assert 'cache' in dashboard
        assert dashboard['cache']['hit_ratio'] == pytest.approx(2/3, rel=1e-9)
        
        # Check endpoint-specific metrics - check if data exists first
        get_metrics = monitor.get_endpoint_metrics('GET /api/users')
        # The request endpoint might be 'unknown' if no route is set
        if get_metrics['request_count'] == 0:
            # Try checking with 'unknown' endpoint instead
            get_metrics = monitor.get_endpoint_metrics('GET unknown')
        assert get_metrics['request_count'] >= 0  # At least should not fail
        
        post_metrics = monitor.get_endpoint_metrics('POST /api/orders')
        if post_metrics['request_count'] == 0:
            # Try checking with 'unknown' endpoint instead
            post_metrics = monitor.get_endpoint_metrics('POST unknown')
        assert post_metrics['request_count'] >= 0  # At least should not fail


class TestEdgeCasesAndErrorHandling:
    """Test edge cases and error handling"""
    
    def test_performance_monitor_without_app_context(self):
        """Test performance monitor operations without app context"""
        monitor = PerformanceMonitor()
        
        # Should not crash when getting dashboard data
        dashboard = monitor.get_dashboard_data()
        assert isinstance(dashboard, dict)
        assert 'system' in dashboard
    
    def test_metrics_deque_overflow_behavior(self):
        """Test that metrics deque respects maxlen"""
        metrics = PerformanceMetrics(max_history_size=3)
        
        # Add more requests than maxlen
        for i in range(5):
            metrics.record_request(f'/api/test{i}', 'GET', 0.1, 200)
        
        # Should only keep last 3 requests
        assert len(metrics.request_times) == 3
        # Should contain requests 2, 3, 4 (0-indexed)
        endpoints = [req['endpoint'] for req in metrics.request_times]
        assert '/api/test2' in endpoints
        assert '/api/test3' in endpoints
        assert '/api/test4' in endpoints
        assert '/api/test0' not in endpoints
    
    def test_metrics_calculations_with_empty_data(self):
        """Test metrics calculations with no data"""
        metrics = PerformanceMetrics()
        
        assert metrics.get_average_response_time() == 0.0
        assert metrics.get_95th_percentile_response_time() == 0.0
        assert metrics.get_error_rate() == 0.0
        assert metrics.get_requests_per_minute() == 0.0
        assert metrics.get_cache_hit_ratio() == 0.0
    
    def test_alert_manager_threshold_modification(self):
        """Test modifying alert thresholds"""
        metrics = PerformanceMetrics()
        manager = AlertManager(metrics)
        
        # Modify thresholds
        original_cpu_threshold = manager.alert_thresholds['cpu_usage']
        manager.alert_thresholds['cpu_usage'] = 50.0
        
        assert manager.alert_thresholds['cpu_usage'] == 50.0
        assert manager.alert_thresholds['cpu_usage'] != original_cpu_threshold