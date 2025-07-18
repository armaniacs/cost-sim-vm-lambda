"""
Monitoring API endpoints for enterprise cost management platform.

This module provides REST API endpoints for:
- Health checks and system status
- Metrics collection and retrieval
- Alert management
- APM traces and spans
- Log aggregation and search
- Observability dashboards
"""

from flask import Blueprint, jsonify, request, current_app
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Create monitoring blueprint
monitoring_bp = Blueprint('monitoring', __name__, url_prefix='/api/v1/monitoring')


@monitoring_bp.route('/health', methods=['GET'])
def health_check():
    """
    Get overall system health status.
    
    Returns:
        JSON response with health status of all monitored services
    """
    try:
        monitoring_integration = getattr(current_app, 'monitoring_integration', None)
        if not monitoring_integration:
            return jsonify({'status': 'error', 'message': 'Monitoring not initialized'}), 500
        
        if monitoring_integration.is_service_enabled('observability'):
            observability_service = monitoring_integration.get_service('observability')
            health_data = observability_service.health_checker.get_health_summary()
            return jsonify(health_data)
        else:
            return jsonify({'status': 'healthy', 'message': 'Basic monitoring active'})
    
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@monitoring_bp.route('/dashboard', methods=['GET'])
def get_dashboard():
    """
    Get comprehensive monitoring dashboard data.
    
    Returns:
        JSON response with data from all monitoring services
    """
    try:
        monitoring_integration = getattr(current_app, 'monitoring_integration', None)
        if not monitoring_integration:
            return jsonify({'error': 'Monitoring not initialized'}), 500
        
        dashboard_data = monitoring_integration.get_unified_dashboard()
        return jsonify(dashboard_data)
    
    except Exception as e:
        logger.error(f"Error getting dashboard: {e}")
        return jsonify({'error': str(e)}), 500


@monitoring_bp.route('/metrics', methods=['GET'])
def get_metrics():
    """
    Get metrics data for specified metrics and time range.
    
    Query Parameters:
        metrics: List of metric names to retrieve
        time_range: Time range in seconds (default: 3600)
    
    Returns:
        JSON response with metrics data
    """
    try:
        monitoring_integration = getattr(current_app, 'monitoring_integration', None)
        if not monitoring_integration:
            return jsonify({'error': 'Monitoring not initialized'}), 500
        
        metric_names = request.args.getlist('metrics')
        time_range = int(request.args.get('time_range', 3600))
        
        if monitoring_integration.is_service_enabled('observability'):
            observability_service = monitoring_integration.get_service('observability')
            metrics = observability_service.get_metrics_for_dashboard(metric_names, time_range)
            return jsonify(metrics)
        else:
            return jsonify({'error': 'Observability service not available'}), 404
    
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        return jsonify({'error': str(e)}), 500


@monitoring_bp.route('/metrics', methods=['POST'])
def record_metric():
    """
    Record a custom metric.
    
    Request Body:
        {
            "name": "metric_name",
            "value": 123.45,
            "tags": {"key": "value"}
        }
    
    Returns:
        JSON response confirming metric recording
    """
    try:
        monitoring_integration = getattr(current_app, 'monitoring_integration', None)
        if not monitoring_integration:
            return jsonify({'error': 'Monitoring not initialized'}), 500
        
        data = request.json
        if not data or 'name' not in data or 'value' not in data:
            return jsonify({'error': 'Missing required fields: name, value'}), 400
        
        name = data['name']
        value = float(data['value'])
        tags = data.get('tags', {})
        
        if monitoring_integration.is_service_enabled('observability'):
            observability_service = monitoring_integration.get_service('observability')
            observability_service.record_metric(name, value, tags=tags)
            return jsonify({'status': 'recorded', 'metric': name, 'value': value})
        else:
            return jsonify({'error': 'Observability service not available'}), 404
    
    except Exception as e:
        logger.error(f"Error recording metric: {e}")
        return jsonify({'error': str(e)}), 500


@monitoring_bp.route('/alerts', methods=['GET'])
def get_alerts():
    """
    Get active alerts and alert statistics.
    
    Returns:
        JSON response with alerts data
    """
    try:
        monitoring_integration = getattr(current_app, 'monitoring_integration', None)
        if not monitoring_integration:
            return jsonify({'error': 'Monitoring not initialized'}), 500
        
        if monitoring_integration.is_service_enabled('alerting'):
            alerting_service = monitoring_integration.get_service('alerting')
            alerts_data = alerting_service.get_dashboard_data()
            return jsonify(alerts_data)
        else:
            return jsonify({'error': 'Alerting service not available'}), 404
    
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        return jsonify({'error': str(e)}), 500


@monitoring_bp.route('/alerts/search', methods=['POST'])
def search_alerts():
    """
    Search alerts based on criteria.
    
    Request Body:
        {
            "severity": "high",
            "status": "active",
            "name": "search_term",
            "start_time": "2023-01-01T00:00:00",
            "end_time": "2023-01-02T00:00:00"
        }
    
    Returns:
        JSON response with matching alerts
    """
    try:
        monitoring_integration = getattr(current_app, 'monitoring_integration', None)
        if not monitoring_integration:
            return jsonify({'error': 'Monitoring not initialized'}), 500
        
        if monitoring_integration.is_service_enabled('alerting'):
            alerting_service = monitoring_integration.get_service('alerting')
            query = request.json or {}
            alerts = alerting_service.search_alerts(query)
            return jsonify({'alerts': alerts})
        else:
            return jsonify({'error': 'Alerting service not available'}), 404
    
    except Exception as e:
        logger.error(f"Error searching alerts: {e}")
        return jsonify({'error': str(e)}), 500


@monitoring_bp.route('/alerts/<alert_id>/acknowledge', methods=['POST'])
def acknowledge_alert(alert_id):
    """
    Acknowledge an alert.
    
    Request Body:
        {
            "user_id": "user123"
        }
    
    Returns:
        JSON response confirming acknowledgment
    """
    try:
        monitoring_integration = getattr(current_app, 'monitoring_integration', None)
        if not monitoring_integration:
            return jsonify({'error': 'Monitoring not initialized'}), 500
        
        if monitoring_integration.is_service_enabled('alerting'):
            alerting_service = monitoring_integration.get_service('alerting')
            user_id = request.json.get('user_id') if request.json else None
            success = alerting_service.acknowledge_alert(alert_id, user_id)
            
            if success:
                return jsonify({'status': 'acknowledged', 'alert_id': alert_id})
            else:
                return jsonify({'error': 'Alert not found'}), 404
        else:
            return jsonify({'error': 'Alerting service not available'}), 404
    
    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}")
        return jsonify({'error': str(e)}), 500


@monitoring_bp.route('/alerts/<alert_id>/suppress', methods=['POST'])
def suppress_alert(alert_id):
    """
    Suppress an alert for a specified duration.
    
    Request Body:
        {
            "duration_minutes": 60
        }
    
    Returns:
        JSON response confirming suppression
    """
    try:
        monitoring_integration = getattr(current_app, 'monitoring_integration', None)
        if not monitoring_integration:
            return jsonify({'error': 'Monitoring not initialized'}), 500
        
        if monitoring_integration.is_service_enabled('alerting'):
            alerting_service = monitoring_integration.get_service('alerting')
            duration = request.json.get('duration_minutes', 60) if request.json else 60
            success = alerting_service.suppress_alert(alert_id, duration)
            
            if success:
                return jsonify({'status': 'suppressed', 'alert_id': alert_id, 'duration_minutes': duration})
            else:
                return jsonify({'error': 'Alert not found'}), 404
        else:
            return jsonify({'error': 'Alerting service not available'}), 404
    
    except Exception as e:
        logger.error(f"Error suppressing alert: {e}")
        return jsonify({'error': str(e)}), 500


@monitoring_bp.route('/traces', methods=['GET'])
def get_traces():
    """
    Get APM traces.
    
    Query Parameters:
        trace_id: Specific trace ID to retrieve
    
    Returns:
        JSON response with trace data
    """
    try:
        monitoring_integration = getattr(current_app, 'monitoring_integration', None)
        if not monitoring_integration:
            return jsonify({'error': 'Monitoring not initialized'}), 500
        
        if monitoring_integration.is_service_enabled('apm'):
            apm_service = monitoring_integration.get_service('apm')
            trace_id = request.args.get('trace_id')
            
            if trace_id:
                trace = apm_service.get_trace_by_id(trace_id)
                if trace:
                    return jsonify(trace)
                else:
                    return jsonify({'error': 'Trace not found'}), 404
            else:
                # Get recent traces
                dashboard_data = apm_service.get_dashboard_data()
                return jsonify(dashboard_data['traces'])
        else:
            return jsonify({'error': 'APM service not available'}), 404
    
    except Exception as e:
        logger.error(f"Error getting traces: {e}")
        return jsonify({'error': str(e)}), 500


@monitoring_bp.route('/traces/search', methods=['POST'])
def search_traces():
    """
    Search traces based on criteria.
    
    Request Body:
        {
            "min_duration": 1.0,
            "max_duration": 10.0,
            "has_error": true,
            "operation_name": "database_query"
        }
    
    Returns:
        JSON response with matching traces
    """
    try:
        monitoring_integration = getattr(current_app, 'monitoring_integration', None)
        if not monitoring_integration:
            return jsonify({'error': 'Monitoring not initialized'}), 500
        
        if monitoring_integration.is_service_enabled('apm'):
            apm_service = monitoring_integration.get_service('apm')
            query = request.json or {}
            traces = apm_service.search_traces(query)
            return jsonify({'traces': traces})
        else:
            return jsonify({'error': 'APM service not available'}), 404
    
    except Exception as e:
        logger.error(f"Error searching traces: {e}")
        return jsonify({'error': str(e)}), 500


@monitoring_bp.route('/logs', methods=['GET'])
def get_logs():
    """
    Get log data.
    
    Query Parameters:
        level: Log level filter
        limit: Number of logs to return
    
    Returns:
        JSON response with log data
    """
    try:
        monitoring_integration = getattr(current_app, 'monitoring_integration', None)
        if not monitoring_integration:
            return jsonify({'error': 'Monitoring not initialized'}), 500
        
        if monitoring_integration.is_service_enabled('logging'):
            logging_service = monitoring_integration.get_service('logging')
            
            # Get query parameters
            level = request.args.get('level')
            limit = int(request.args.get('limit', 100))
            
            if level:
                logs = logging_service.aggregator.get_recent_logs(limit, level)
            else:
                logs = logging_service.get_dashboard_data()
            
            return jsonify(logs)
        else:
            return jsonify({'error': 'Logging service not available'}), 404
    
    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        return jsonify({'error': str(e)}), 500


@monitoring_bp.route('/logs/search', methods=['POST'])
def search_logs():
    """
    Search logs based on criteria.
    
    Request Body:
        {
            "level": "ERROR",
            "message": "search_term",
            "trace_id": "trace123",
            "start_time": "2023-01-01T00:00:00",
            "end_time": "2023-01-02T00:00:00"
        }
    
    Returns:
        JSON response with matching logs
    """
    try:
        monitoring_integration = getattr(current_app, 'monitoring_integration', None)
        if not monitoring_integration:
            return jsonify({'error': 'Monitoring not initialized'}), 500
        
        if monitoring_integration.is_service_enabled('logging'):
            logging_service = monitoring_integration.get_service('logging')
            query = request.json or {}
            logs = logging_service.search_logs(query)
            return jsonify({'logs': logs})
        else:
            return jsonify({'error': 'Logging service not available'}), 404
    
    except Exception as e:
        logger.error(f"Error searching logs: {e}")
        return jsonify({'error': str(e)}), 500


@monitoring_bp.route('/performance', methods=['GET'])
def get_performance():
    """
    Get performance monitoring data.
    
    Returns:
        JSON response with performance metrics
    """
    try:
        monitoring_integration = getattr(current_app, 'monitoring_integration', None)
        if not monitoring_integration:
            return jsonify({'error': 'Monitoring not initialized'}), 500
        
        if monitoring_integration.is_service_enabled('performance'):
            performance_service = monitoring_integration.get_service('performance')
            performance_data = performance_service.get_dashboard_data()
            return jsonify(performance_data)
        else:
            return jsonify({'error': 'Performance service not available'}), 404
    
    except Exception as e:
        logger.error(f"Error getting performance data: {e}")
        return jsonify({'error': str(e)}), 500


@monitoring_bp.route('/sla', methods=['GET'])
def get_sla():
    """
    Get SLA monitoring data.
    
    Returns:
        JSON response with SLA metrics and compliance
    """
    try:
        monitoring_integration = getattr(current_app, 'monitoring_integration', None)
        if not monitoring_integration:
            return jsonify({'error': 'Monitoring not initialized'}), 500
        
        if monitoring_integration.is_service_enabled('observability'):
            observability_service = monitoring_integration.get_service('observability')
            sla_data = observability_service.sla_monitor.get_sla_dashboard()
            return jsonify(sla_data)
        else:
            return jsonify({'error': 'Observability service not available'}), 404
    
    except Exception as e:
        logger.error(f"Error getting SLA data: {e}")
        return jsonify({'error': str(e)}), 500


@monitoring_bp.route('/dependencies', methods=['GET'])
def get_dependencies():
    """
    Get service dependency information.
    
    Returns:
        JSON response with dependency graph and health
    """
    try:
        monitoring_integration = getattr(current_app, 'monitoring_integration', None)
        if not monitoring_integration:
            return jsonify({'error': 'Monitoring not initialized'}), 500
        
        if monitoring_integration.is_service_enabled('observability'):
            observability_service = monitoring_integration.get_service('observability')
            dependencies = observability_service.dependency_mapper.get_dependency_graph()
            return jsonify({'dependencies': dependencies})
        else:
            return jsonify({'error': 'Observability service not available'}), 404
    
    except Exception as e:
        logger.error(f"Error getting dependencies: {e}")
        return jsonify({'error': str(e)}), 500


@monitoring_bp.route('/config', methods=['GET'])
def get_config():
    """
    Get monitoring configuration.
    
    Returns:
        JSON response with current configuration
    """
    try:
        monitoring_integration = getattr(current_app, 'monitoring_integration', None)
        if not monitoring_integration:
            return jsonify({'error': 'Monitoring not initialized'}), 500
        
        return jsonify(monitoring_integration.config.config)
    
    except Exception as e:
        logger.error(f"Error getting config: {e}")
        return jsonify({'error': str(e)}), 500


@monitoring_bp.route('/config', methods=['PUT'])
def update_config():
    """
    Update monitoring configuration.
    
    Request Body:
        Configuration object to update
    
    Returns:
        JSON response confirming update
    """
    try:
        monitoring_integration = getattr(current_app, 'monitoring_integration', None)
        if not monitoring_integration:
            return jsonify({'error': 'Monitoring not initialized'}), 500
        
        new_config = request.json
        if not new_config:
            return jsonify({'error': 'No configuration provided'}), 400
        
        monitoring_integration.config.config.update(new_config)
        monitoring_integration.config.save()
        
        return jsonify({'status': 'updated', 'timestamp': datetime.utcnow().isoformat()})
    
    except Exception as e:
        logger.error(f"Error updating config: {e}")
        return jsonify({'error': str(e)}), 500


@monitoring_bp.route('/status', methods=['GET'])
def get_status():
    """
    Get monitoring system status.
    
    Returns:
        JSON response with system status
    """
    try:
        monitoring_integration = getattr(current_app, 'monitoring_integration', None)
        if not monitoring_integration:
            return jsonify({'error': 'Monitoring not initialized'}), 500
        
        status = {
            'initialized': monitoring_integration.initialized,
            'services': {
                name: service is not None
                for name, service in monitoring_integration.services.items()
            },
            'config_loaded': monitoring_integration.config.config is not None,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify(status)
    
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({'error': str(e)}), 500


@monitoring_bp.route('/events', methods=['POST'])
def record_event():
    """
    Record a custom monitoring event.
    
    Request Body:
        {
            "type": "audit|security|performance",
            "event": "event_name",
            "details": {},
            "user_id": "user123"
        }
    
    Returns:
        JSON response confirming event recording
    """
    try:
        monitoring_integration = getattr(current_app, 'monitoring_integration', None)
        if not monitoring_integration:
            return jsonify({'error': 'Monitoring not initialized'}), 500
        
        data = request.json
        if not data or 'type' not in data or 'event' not in data:
            return jsonify({'error': 'Missing required fields: type, event'}), 400
        
        event_type = data['type']
        event = data['event']
        details = data.get('details', {})
        user_id = data.get('user_id')
        
        if monitoring_integration.is_service_enabled('logging'):
            logging_service = monitoring_integration.get_service('logging')
            
            if event_type == 'audit':
                logging_service.log_audit_event(event, details, user_id)
            elif event_type == 'security':
                logging_service.log_security_event(event, details)
            elif event_type == 'performance':
                logging_service.log_performance_event(event, details)
            else:
                return jsonify({'error': 'Invalid event type'}), 400
            
            return jsonify({'status': 'recorded', 'event': event, 'type': event_type})
        else:
            return jsonify({'error': 'Logging service not available'}), 404
    
    except Exception as e:
        logger.error(f"Error recording event: {e}")
        return jsonify({'error': str(e)}), 500


# Error handlers
@monitoring_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404


@monitoring_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500