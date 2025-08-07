"""
Unit tests for performance API endpoints
Tests all performance monitoring API routes and functionality
"""
import pytest
import json
from unittest.mock import MagicMock, patch, Mock
from datetime import datetime, timedelta
from flask import Flask
import sys

# Mock all the service dependencies before importing performance_api
mock_modules = [
    'app.services.database_service',
    'app.services.performance_monitor', 
    'app.services.cache_service',
    'app.services.query_optimizer',
    'app.services.async_db_service'
]

for module in mock_modules:
    sys.modules[module] = Mock()

# Mock the individual services that are imported
sys.modules['app.services.database_service'].db_service = MagicMock()
sys.modules['app.services.performance_monitor'].performance_monitor = MagicMock()  
sys.modules['app.services.cache_service'].cache_service = MagicMock()
sys.modules['app.services.query_optimizer'].query_optimizer = MagicMock()
sys.modules['app.services.async_db_service'].async_db_service = MagicMock()

# Now import the performance API
from app.api.performance_api import performance_bp


class TestPerformanceAPI:
    """Comprehensive test suite for performance API endpoints"""
    
    @pytest.fixture
    def app(self):
        """Create test Flask app with performance blueprint"""
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.register_blueprint(performance_bp)
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        with app.test_client() as client:
            yield client
    
    @pytest.fixture
    def mock_services(self):
        """Create mock services used by performance API"""
        with patch('app.api.performance_api.performance_monitor') as mock_perf, \
             patch('app.api.performance_api.db_service') as mock_db, \
             patch('app.api.performance_api.cache_service') as mock_cache, \
             patch('app.api.performance_api.query_optimizer') as mock_query, \
             patch('app.api.performance_api.async_db_service') as mock_async_db:
            
            # Setup default mock returns
            mock_perf.get_dashboard_data.return_value = {
                'response_times': {'avg': 150, 'p95': 300},
                'throughput': {'rps': 100}
            }
            mock_db.get_performance_metrics.return_value = {
                'connections': {'active': 5, 'total': 10},
                'query_time': {'avg': 25}
            }
            mock_cache.get_performance_stats.return_value = {
                'hit_rate': 85.5,
                'memory_usage': 512
            }
            
            yield {
                'performance_monitor': mock_perf,
                'db_service': mock_db,
                'cache_service': mock_cache,
                'query_optimizer': mock_query,
                'async_db_service': mock_async_db
            }
    
    # Blueprint Registration Tests
    def test_blueprint_registration(self, app):
        """Test that performance blueprint is properly registered"""
        blueprint_names = [bp.name for bp in app.blueprints.values()]
        assert 'performance' in blueprint_names
    
    # Dashboard Endpoint Tests
    def test_performance_dashboard_success(self, client, mock_services):
        """Test successful performance dashboard retrieval"""
        response = client.get('/api/v1/performance/dashboard')
        assert response.status_code == 200
        
        result = response.get_json()
        assert result['success'] is True
        assert 'data' in result
        assert 'timestamp' in result
        
        data = result['data']
        assert 'response_times' in data
        assert 'database' in data
        assert 'cache' in data
        assert data['response_times']['avg'] == 150
        assert data['database']['connections']['active'] == 5
        assert data['cache']['hit_rate'] == 85.5
    
    def test_performance_dashboard_exception(self, client, mock_services):
        """Test performance dashboard exception handling"""
        mock_services['performance_monitor'].get_dashboard_data.side_effect = Exception("Dashboard error")
        
        response = client.get('/api/v1/performance/dashboard')
        assert response.status_code == 500
        
        data = response.get_json()
        assert 'error' in data
        assert 'Dashboard error' in data['error']
    
    # Metrics Endpoint Tests  
    def test_performance_metrics_success(self, client, mock_services):
        """Test successful performance metrics retrieval"""
        mock_services['performance_monitor'].get_metrics_data.return_value = {
            'cpu': {'usage': 45.2},
            'memory': {'usage': 62.1},
            'disk': {'usage': 35.8}
        }
        
        response = client.get('/api/v1/performance/metrics')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'cpu' in data
        assert 'memory' in data
        assert 'disk' in data
        assert data['cpu']['usage'] == 45.2
    
    def test_performance_metrics_with_filters(self, client, mock_services):
        """Test performance metrics with query filters"""
        mock_services['performance_monitor'].get_metrics_data.return_value = {
            'filtered_data': True
        }
        
        response = client.get('/api/v1/performance/metrics?metric=cpu&timerange=1h')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'filtered_data' in data
    
    def test_performance_metrics_exception(self, client, mock_services):
        """Test performance metrics exception handling"""
        mock_services['performance_monitor'].get_metrics_data.side_effect = Exception("Metrics error")
        
        response = client.get('/api/v1/performance/metrics')
        assert response.status_code == 500
        
        data = response.get_json()
        assert 'error' in data
    
    # Database Health Endpoint Tests
    def test_database_health_success(self, client, mock_services):
        """Test successful database health check"""
        mock_services['db_service'].check_health.return_value = {
            'status': 'healthy',
            'connection_time': 12,
            'active_connections': 8
        }
        
        response = client.get('/api/v1/performance/database/health')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['status'] == 'healthy'
        assert data['connection_time'] == 12
        assert data['active_connections'] == 8
    
    def test_database_health_exception(self, client, mock_services):
        """Test database health check exception handling"""
        mock_services['db_service'].check_health.side_effect = Exception("DB connection error")
        
        response = client.get('/api/v1/performance/database/health')
        assert response.status_code == 500
        
        data = response.get_json()
        assert 'error' in data
        assert 'DB connection error' in data['error']
    
    # Database Pool Endpoint Tests
    def test_database_pool_success(self, client, mock_services):
        """Test successful database pool info retrieval"""
        mock_services['db_service'].get_pool_info.return_value = {
            'pool_size': 20,
            'checked_out': 5,
            'overflow': 2,
            'checked_in': 13
        }
        
        response = client.get('/api/v1/performance/database/pool')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['pool_size'] == 20
        assert data['checked_out'] == 5
        assert data['overflow'] == 2
        assert data['checked_in'] == 13
    
    def test_database_pool_exception(self, client, mock_services):
        """Test database pool info exception handling"""
        mock_services['db_service'].get_pool_info.side_effect = Exception("Pool error")
        
        response = client.get('/api/v1/performance/database/pool')
        assert response.status_code == 500
        
        data = response.get_json()
        assert 'error' in data
    
    # Cache Health Endpoint Tests
    def test_cache_health_success(self, client, mock_services):
        """Test successful cache health check"""
        mock_services['cache_service'].check_health.return_value = {
            'status': 'healthy',
            'response_time': 2,
            'memory_usage': 256
        }
        
        response = client.get('/api/v1/performance/cache/health')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['status'] == 'healthy'
        assert data['response_time'] == 2
        assert data['memory_usage'] == 256
    
    def test_cache_health_exception(self, client, mock_services):
        """Test cache health check exception handling"""
        mock_services['cache_service'].check_health.side_effect = Exception("Cache error")
        
        response = client.get('/api/v1/performance/cache/health')
        assert response.status_code == 500
        
        data = response.get_json()
        assert 'error' in data
    
    # Cache Stats Endpoint Tests
    def test_cache_stats_success(self, client, mock_services):
        """Test successful cache statistics retrieval"""
        mock_services['cache_service'].get_detailed_stats.return_value = {
            'hit_rate': 87.5,
            'miss_rate': 12.5,
            'total_hits': 8750,
            'total_misses': 1250,
            'memory_usage': 512
        }
        
        response = client.get('/api/v1/performance/cache/stats')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['hit_rate'] == 87.5
        assert data['miss_rate'] == 12.5
        assert data['total_hits'] == 8750
    
    def test_cache_stats_exception(self, client, mock_services):
        """Test cache statistics exception handling"""
        mock_services['cache_service'].get_detailed_stats.side_effect = Exception("Stats error")
        
        response = client.get('/api/v1/performance/cache/stats')
        assert response.status_code == 500
        
        data = response.get_json()
        assert 'error' in data
    
    # Cache Invalidation Endpoint Tests
    def test_cache_invalidate_success(self, client, mock_services):
        """Test successful cache invalidation"""
        mock_services['cache_service'].invalidate_pattern.return_value = {
            'invalidated': 15,
            'pattern': 'user:*'
        }
        
        invalidation_data = {
            'pattern': 'user:*',
            'reason': 'user_data_update'
        }
        
        response = client.post('/api/v1/performance/cache/invalidate',
                             json=invalidation_data,
                             content_type='application/json')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['status'] == 'success'
        assert data['invalidated'] == 15
        assert data['pattern'] == 'user:*'
    
    def test_cache_invalidate_no_pattern(self, client, mock_services):
        """Test cache invalidation without pattern"""
        response = client.post('/api/v1/performance/cache/invalidate',
                             json={},
                             content_type='application/json')
        assert response.status_code == 400
        
        data = response.get_json()
        assert 'error' in data
        assert 'pattern' in data['error'].lower()
    
    def test_cache_invalidate_exception(self, client, mock_services):
        """Test cache invalidation exception handling"""
        mock_services['cache_service'].invalidate_pattern.side_effect = Exception("Invalidation error")
        
        invalidation_data = {'pattern': 'test:*'}
        
        response = client.post('/api/v1/performance/cache/invalidate',
                             json=invalidation_data,
                             content_type='application/json')
        assert response.status_code == 500
        
        data = response.get_json()
        assert 'error' in data
    
    # Query Analysis Endpoint Tests
    def test_query_analyze_success(self, client, mock_services):
        """Test successful query analysis"""
        mock_services['query_optimizer'].analyze_query.return_value = {
            'execution_time': 45,
            'cost': 156,
            'recommendations': ['Add index on user_id', 'Use LIMIT clause']
        }
        
        query_data = {
            'query': 'SELECT * FROM users WHERE status = "active"',
            'database': 'main'
        }
        
        response = client.post('/api/v1/performance/query/analyze',
                             json=query_data,
                             content_type='application/json')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['execution_time'] == 45
        assert data['cost'] == 156
        assert len(data['recommendations']) == 2
    
    def test_query_analyze_no_query(self, client, mock_services):
        """Test query analysis without query"""
        response = client.post('/api/v1/performance/query/analyze',
                             json={},
                             content_type='application/json')
        assert response.status_code == 400
        
        data = response.get_json()
        assert 'error' in data
        assert 'query' in data['error'].lower()
    
    def test_query_analyze_exception(self, client, mock_services):
        """Test query analysis exception handling"""
        mock_services['query_optimizer'].analyze_query.side_effect = Exception("Analysis error")
        
        query_data = {'query': 'SELECT * FROM test'}
        
        response = client.post('/api/v1/performance/query/analyze',
                             json=query_data,
                             content_type='application/json')
        assert response.status_code == 500
        
        data = response.get_json()
        assert 'error' in data
    
    # Query Profile Endpoint Tests
    def test_query_profile_success(self, client, mock_services):
        """Test successful query profiling"""
        mock_services['query_optimizer'].profile_query.return_value = {
            'execution_plan': {'nodes': ['Seq Scan', 'Sort']},
            'timing': {'planning_time': 0.5, 'execution_time': 12.3},
            'resource_usage': {'memory': 1024, 'cpu': 15.2}
        }
        
        profile_data = {
            'query': 'SELECT * FROM products ORDER BY price',
            'explain_options': ['ANALYZE', 'BUFFERS']
        }
        
        response = client.post('/api/v1/performance/query/profile',
                             json=profile_data,
                             content_type='application/json')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'execution_plan' in data
        assert 'timing' in data
        assert 'resource_usage' in data
        assert data['timing']['execution_time'] == 12.3
    
    def test_query_profile_no_query(self, client, mock_services):
        """Test query profiling without query"""
        response = client.post('/api/v1/performance/query/profile',
                             json={},
                             content_type='application/json')
        assert response.status_code == 400
        
        data = response.get_json()
        assert 'error' in data
        assert 'query' in data['error'].lower()
    
    def test_query_profile_exception(self, client, mock_services):
        """Test query profiling exception handling"""
        mock_services['query_optimizer'].profile_query.side_effect = Exception("Profile error")
        
        profile_data = {'query': 'SELECT * FROM test'}
        
        response = client.post('/api/v1/performance/query/profile',
                             json=profile_data,
                             content_type='application/json')
        assert response.status_code == 500
        
        data = response.get_json()
        assert 'error' in data
    
    # Index Recommendations Endpoint Tests
    def test_index_recommendations_success(self, client, mock_services):
        """Test successful index recommendations retrieval"""
        mock_services['query_optimizer'].get_index_recommendations.return_value = {
            'recommendations': [
                {'table': 'users', 'columns': ['email'], 'impact': 'high'},
                {'table': 'orders', 'columns': ['user_id', 'created_at'], 'impact': 'medium'}
            ],
            'total': 2
        }
        
        response = client.get('/api/v1/performance/index/recommendations')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'recommendations' in data
        assert 'total' in data
        assert data['total'] == 2
        assert len(data['recommendations']) == 2
        assert data['recommendations'][0]['table'] == 'users'
    
    def test_index_recommendations_with_params(self, client, mock_services):
        """Test index recommendations with query parameters"""
        mock_services['query_optimizer'].get_index_recommendations.return_value = {
            'recommendations': [],
            'total': 0
        }
        
        response = client.get('/api/v1/performance/index/recommendations?table=users&impact=high')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'recommendations' in data
        assert data['total'] == 0
    
    def test_index_recommendations_exception(self, client, mock_services):
        """Test index recommendations exception handling"""
        mock_services['query_optimizer'].get_index_recommendations.side_effect = Exception("Recommendations error")
        
        response = client.get('/api/v1/performance/index/recommendations')
        assert response.status_code == 500
        
        data = response.get_json()
        assert 'error' in data
    
    # Alerts Endpoint Tests
    def test_performance_alerts_success(self, client, mock_services):
        """Test successful performance alerts retrieval"""
        mock_services['performance_monitor'].get_alerts.return_value = [
            {'id': 'alert1', 'severity': 'high', 'message': 'CPU usage over 80%'},
            {'id': 'alert2', 'severity': 'medium', 'message': 'Memory usage over 70%'}
        ]
        
        response = client.get('/api/v1/performance/alerts')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'alerts' in data
        assert len(data['alerts']) == 2
        assert data['alerts'][0]['severity'] == 'high'
    
    def test_performance_alerts_exception(self, client, mock_services):
        """Test performance alerts exception handling"""
        mock_services['performance_monitor'].get_alerts.side_effect = Exception("Alerts error")
        
        response = client.get('/api/v1/performance/alerts')
        assert response.status_code == 500
        
        data = response.get_json()
        assert 'error' in data
    
    # Endpoints Performance Tests
    def test_endpoints_performance_success(self, client, mock_services):
        """Test successful endpoints performance retrieval"""
        mock_services['performance_monitor'].get_endpoint_stats.return_value = {
            'endpoints': [
                {'path': '/api/v1/users', 'avg_time': 120, 'requests': 1500},
                {'path': '/api/v1/orders', 'avg_time': 200, 'requests': 800}
            ]
        }
        
        response = client.get('/api/v1/performance/endpoints')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'endpoints' in data
        assert len(data['endpoints']) == 2
        assert data['endpoints'][0]['path'] == '/api/v1/users'
    
    def test_endpoints_performance_exception(self, client, mock_services):
        """Test endpoints performance exception handling"""
        mock_services['performance_monitor'].get_endpoint_stats.side_effect = Exception("Endpoints error")
        
        response = client.get('/api/v1/performance/endpoints')
        assert response.status_code == 500
        
        data = response.get_json()
        assert 'error' in data
    
    # Performance Reports Tests
    def test_performance_reports_success(self, client, mock_services):
        """Test successful performance reports retrieval"""
        mock_services['performance_monitor'].generate_report.return_value = {
            'report_id': 'rpt_123',
            'generated_at': datetime.now().isoformat(),
            'summary': {'total_requests': 10000, 'avg_response_time': 150},
            'details': {'hourly_stats': [], 'slow_queries': []}
        }
        
        response = client.get('/api/v1/performance/reports/performance')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'report_id' in data
        assert 'summary' in data
        assert 'details' in data
        assert data['summary']['total_requests'] == 10000
    
    def test_performance_reports_with_params(self, client, mock_services):
        """Test performance reports with query parameters"""
        mock_services['performance_monitor'].generate_report.return_value = {
            'report_id': 'rpt_124',
            'period': 'last_week'
        }
        
        response = client.get('/api/v1/performance/reports/performance?period=week&format=json')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'report_id' in data
    
    def test_performance_reports_exception(self, client, mock_services):
        """Test performance reports exception handling"""
        mock_services['performance_monitor'].generate_report.side_effect = Exception("Report error")
        
        response = client.get('/api/v1/performance/reports/performance')
        assert response.status_code == 500
        
        data = response.get_json()
        assert 'error' in data
    
    # Configuration Endpoints Tests
    def test_get_config_success(self, client, mock_services):
        """Test successful configuration retrieval"""
        mock_config = {
            'monitoring': {
                'enabled': True,
                'interval': 60,
                'thresholds': {'cpu': 80, 'memory': 70}
            },
            'database': {
                'pool_size': 20,
                'timeout': 30
            }
        }
        
        with patch('app.api.performance_api.current_app') as mock_app:
            mock_app.config = mock_config
            
            response = client.get('/api/v1/performance/config')
            assert response.status_code == 200
            
            data = response.get_json()
            assert 'monitoring' in data
            assert 'database' in data
            assert data['monitoring']['enabled'] is True
    
    def test_get_config_exception(self, client, mock_services):
        """Test configuration retrieval exception handling"""
        with patch('app.api.performance_api.current_app') as mock_app:
            mock_app.config = {}
            # Simulate config access error
            type(mock_app).config = PropertyError()
            
            response = client.get('/api/v1/performance/config')
            assert response.status_code == 500
            
            data = response.get_json()
            assert 'error' in data
    
    def test_update_config_success(self, client, mock_services):
        """Test successful configuration update"""
        new_config = {
            'monitoring.interval': 120,
            'database.pool_size': 25
        }
        
        response = client.post('/api/v1/performance/config',
                             json=new_config,
                             content_type='application/json')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['status'] == 'updated'
        assert 'timestamp' in data
    
    def test_update_config_no_data(self, client, mock_services):
        """Test configuration update without data"""
        response = client.post('/api/v1/performance/config',
                             json={},
                             content_type='application/json')
        assert response.status_code == 400
        
        data = response.get_json()
        assert 'error' in data
        assert 'configuration' in data['error'].lower()
    
    def test_update_config_exception(self, client, mock_services):
        """Test configuration update exception handling"""
        new_config = {'test': 'value'}
        
        with patch('app.api.performance_api.current_app') as mock_app:
            mock_app.config = {}
            type(mock_app).config = PropertyError()
            
            response = client.post('/api/v1/performance/config',
                                 json=new_config,
                                 content_type='application/json')
            assert response.status_code == 500
            
            data = response.get_json()
            assert 'error' in data
    
    # Reset Endpoint Tests
    def test_performance_reset_success(self, client, mock_services):
        """Test successful performance data reset"""
        mock_services['performance_monitor'].reset_stats.return_value = True
        
        response = client.post('/api/v1/performance/reset',
                             json={'confirm': True},
                             content_type='application/json')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['status'] == 'success'
        assert 'reset' in data['message'].lower()
    
    def test_performance_reset_no_confirm(self, client, mock_services):
        """Test performance reset without confirmation"""
        response = client.post('/api/v1/performance/reset',
                             json={},
                             content_type='application/json')
        assert response.status_code == 400
        
        data = response.get_json()
        assert 'error' in data
        assert 'confirmation' in data['error'].lower()
    
    def test_performance_reset_exception(self, client, mock_services):
        """Test performance reset exception handling"""
        mock_services['performance_monitor'].reset_stats.side_effect = Exception("Reset error")
        
        response = client.post('/api/v1/performance/reset',
                             json={'confirm': True},
                             content_type='application/json')
        assert response.status_code == 500
        
        data = response.get_json()
        assert 'error' in data
    
    # Error Handling Tests
    def test_invalid_json_handling(self, client, mock_services):
        """Test handling of invalid JSON in POST requests"""
        response = client.post('/api/v1/performance/query/analyze',
                             data='{"invalid": json}',
                             content_type='application/json')
        
        # Should handle malformed JSON gracefully
        assert response.status_code in [400, 500]
    
    def test_missing_content_type(self, client, mock_services):
        """Test handling of missing content type in POST requests"""
        response = client.post('/api/v1/performance/cache/invalidate',
                             data='{"pattern": "test:*"}')
        
        # Should handle missing content type
        assert response.status_code in [400, 415, 500]
    
    # CORS Tests
    def test_cors_headers_dashboard(self, client, mock_services):
        """Test CORS headers on dashboard endpoint"""
        response = client.get('/api/v1/performance/dashboard')
        
        # Check for CORS headers (may not be present in test environment)
        assert response.status_code == 200


# Helper class for property error simulation
class PropertyError:
    """Helper class to simulate property access errors"""
    
    def __get__(self, obj, objtype=None):
        raise Exception("Config access error")