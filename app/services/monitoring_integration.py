"""
Monitoring Integration Service.

This service provides:
- Configuration management for all monitoring components
- Integration layer that ties together APM, logging, alerting, and observability
- Unified initialization and management of monitoring services
- API endpoints for monitoring data
- Environment-specific configuration
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional
from pathlib import Path
from datetime import datetime

from flask import Flask, current_app

from app.services.apm_service import APMService
from app.services.logging_service import LoggingService
from app.services.alerting_service import AlertingService
from app.services.observability_service import ObservabilityService
from app.services.performance_monitor import PerformanceMonitor

logger = logging.getLogger(__name__)


class MonitoringConfig:
    """Configuration management for monitoring services."""
    
    def __init__(self, config_path: str = "monitoring_config.json"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load monitoring configuration."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading monitoring config: {e}")
        
        return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default monitoring configuration."""
        return {
            "apm": {
                "enabled": True,
                "trace_retention_hours": 24,
                "max_traces": 1000,
                "max_spans_per_trace": 100,
                "sampling_rate": 1.0
            },
            "logging": {
                "enabled": True,
                "log_level": "INFO",
                "structured_logging": True,
                "log_retention_days": 30,
                "max_log_size_mb": 100,
                "compression_enabled": True
            },
            "alerting": {
                "enabled": True,
                "default_notification_channels": ["email"],
                "escalation_enabled": True,
                "alert_correlation_enabled": True,
                "alert_retention_days": 90
            },
            "observability": {
                "enabled": True,
                "metrics_retention_hours": 24,
                "health_check_interval_seconds": 30,
                "sla_monitoring_enabled": True,
                "dependency_mapping_enabled": True
            },
            "performance": {
                "enabled": True,
                "performance_monitoring_enabled": True,
                "slow_request_threshold_seconds": 1.0,
                "cache_monitoring_enabled": True,
                "system_monitoring_enabled": True
            },
            "notifications": {
                "email": {
                    "enabled": True,
                    "smtp_server": "smtp.gmail.com",
                    "smtp_port": 587,
                    "username": "",
                    "password": "",
                    "from_email": "alerts@company.com",
                    "to_emails": ["team@company.com"]
                },
                "slack": {
                    "enabled": False,
                    "webhook_url": "",
                    "channel": "#alerts"
                },
                "webhook": {
                    "enabled": False,
                    "url": "",
                    "headers": {},
                    "timeout": 10
                }
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """Set configuration value."""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def save(self):
        """Save configuration to file."""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving monitoring config: {e}")
    
    def reload(self):
        """Reload configuration from file."""
        self.config = self._load_config()


class MonitoringIntegration:
    """Main monitoring integration service."""
    
    def __init__(self, app: Flask = None):
        self.app = app
        self.config = MonitoringConfig()
        self.services = {}
        self.initialized = False
        
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize monitoring integration with Flask app."""
        self.app = app
        
        # Initialize all monitoring services
        self._initialize_services()
        
        # Register API endpoints
        self._register_endpoints()
        
        # Store reference in app
        app.monitoring_integration = self
        
        self.initialized = True
        logger.info("Monitoring integration initialized successfully")
    
    def _initialize_services(self):
        """Initialize all monitoring services."""
        try:
            # Initialize APM service
            if self.config.get('apm.enabled', True):
                apm_service = APMService(self.app)
                self.services['apm'] = apm_service
                logger.info("APM service initialized")
            
            # Initialize logging service
            if self.config.get('logging.enabled', True):
                logging_service = LoggingService(self.app)
                self.services['logging'] = logging_service
                logger.info("Logging service initialized")
            
            # Initialize alerting service
            if self.config.get('alerting.enabled', True):
                alerting_service = AlertingService(self.app)
                self.services['alerting'] = alerting_service
                logger.info("Alerting service initialized")
            
            # Initialize observability service
            if self.config.get('observability.enabled', True):
                observability_service = ObservabilityService(self.app)
                self.services['observability'] = observability_service
                logger.info("Observability service initialized")
            
            # Initialize performance monitor
            if self.config.get('performance.enabled', True):
                performance_monitor = PerformanceMonitor(self.app)
                self.services['performance'] = performance_monitor
                logger.info("Performance monitor initialized")
            
            # Set up integrations between services
            self._setup_service_integrations()
            
        except Exception as e:
            logger.error(f"Error initializing monitoring services: {e}")
            raise
    
    def _setup_service_integrations(self):
        """Set up integrations between monitoring services."""
        # Integrate APM with alerting
        if 'apm' in self.services and 'alerting' in self.services:
            apm_service = self.services['apm']
            alerting_service = self.services['alerting']
            
            # Add custom metrics collector to observability
            if 'observability' in self.services:
                observability_service = self.services['observability']
                observability_service.add_custom_collector(
                    'apm_metrics',
                    lambda: apm_service.get_dashboard_data()
                )
        
        # Integrate logging with alerting
        if 'logging' in self.services and 'alerting' in self.services:
            logging_service = self.services['logging']
            alerting_service = self.services['alerting']
            
            # Add log-based alerting rules
            self._setup_log_based_alerts(logging_service, alerting_service)
        
        # Integrate performance monitoring with observability
        if 'performance' in self.services and 'observability' in self.services:
            performance_monitor = self.services['performance']
            observability_service = self.services['observability']
            
            observability_service.add_custom_collector(
                'performance_metrics',
                lambda: performance_monitor.get_dashboard_data()
            )
    
    def _setup_log_based_alerts(self, logging_service, alerting_service):
        """Set up log-based alerting rules."""
        from app.services.alerting_service import AlertRule, AlertSeverity, NotificationChannel
        
        # High error rate alert based on logs
        error_rate_rule = AlertRule(
            id="log_error_rate",
            name="High Error Rate (Logs)",
            description="High error rate detected in logs",
            metric_name="log.error_rate",
            condition=">=",
            threshold=0.1,  # 10% error rate
            severity=AlertSeverity.HIGH,
            evaluation_period=300,
            notification_channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK],
            escalation_rules=[],
            tags={"source": "logs", "category": "errors"}
        )
        
        alerting_service.add_alert_rule(error_rate_rule)
    
    def _register_endpoints(self):
        """Register monitoring API endpoints."""
        from flask import Blueprint, jsonify, request
        
        # Create monitoring blueprint
        monitoring_bp = Blueprint('monitoring', __name__, url_prefix='/api/v1/monitoring')
        
        @monitoring_bp.route('/health', methods=['GET'])
        def health_check():
            """Get overall health status."""
            try:
                if 'observability' in self.services:
                    health_data = self.services['observability'].health_checker.get_health_summary()
                    return jsonify(health_data)
                else:
                    return jsonify({'status': 'healthy', 'message': 'Monitoring services running'})
            except Exception as e:
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        @monitoring_bp.route('/dashboard', methods=['GET'])
        def get_dashboard():
            """Get comprehensive monitoring dashboard."""
            try:
                dashboard_data = self.get_unified_dashboard()
                return jsonify(dashboard_data)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @monitoring_bp.route('/metrics', methods=['GET'])
        def get_metrics():
            """Get metrics data."""
            try:
                metric_names = request.args.getlist('metrics')
                time_range = int(request.args.get('time_range', 3600))
                
                if 'observability' in self.services:
                    metrics = self.services['observability'].get_metrics_for_dashboard(
                        metric_names, time_range
                    )
                    return jsonify(metrics)
                else:
                    return jsonify({'error': 'Observability service not available'}), 404
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @monitoring_bp.route('/alerts', methods=['GET'])
        def get_alerts():
            """Get active alerts."""
            try:
                if 'alerting' in self.services:
                    alerts_data = self.services['alerting'].get_dashboard_data()
                    return jsonify(alerts_data)
                else:
                    return jsonify({'error': 'Alerting service not available'}), 404
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @monitoring_bp.route('/alerts/<alert_id>/acknowledge', methods=['POST'])
        def acknowledge_alert(alert_id):
            """Acknowledge an alert."""
            try:
                if 'alerting' in self.services:
                    user_id = request.json.get('user_id')
                    success = self.services['alerting'].acknowledge_alert(alert_id, user_id)
                    if success:
                        return jsonify({'status': 'acknowledged'})
                    else:
                        return jsonify({'error': 'Alert not found'}), 404
                else:
                    return jsonify({'error': 'Alerting service not available'}), 404
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @monitoring_bp.route('/traces', methods=['GET'])
        def get_traces():
            """Get APM traces."""
            try:
                if 'apm' in self.services:
                    trace_id = request.args.get('trace_id')
                    if trace_id:
                        trace = self.services['apm'].get_trace_by_id(trace_id)
                        return jsonify(trace)
                    else:
                        # Get recent traces
                        dashboard_data = self.services['apm'].get_dashboard_data()
                        return jsonify(dashboard_data['traces'])
                else:
                    return jsonify({'error': 'APM service not available'}), 404
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @monitoring_bp.route('/logs', methods=['GET'])
        def get_logs():
            """Get log data."""
            try:
                if 'logging' in self.services:
                    query = request.args.to_dict()
                    if query:
                        logs = self.services['logging'].search_logs(query)
                    else:
                        logs = self.services['logging'].get_dashboard_data()
                    return jsonify(logs)
                else:
                    return jsonify({'error': 'Logging service not available'}), 404
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @monitoring_bp.route('/config', methods=['GET'])
        def get_config():
            """Get monitoring configuration."""
            try:
                return jsonify(self.config.config)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @monitoring_bp.route('/config', methods=['PUT'])
        def update_config():
            """Update monitoring configuration."""
            try:
                new_config = request.json
                self.config.config.update(new_config)
                self.config.save()
                return jsonify({'status': 'updated'})
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @monitoring_bp.route('/status', methods=['GET'])
        def get_status():
            """Get monitoring system status."""
            try:
                status = {
                    'initialized': self.initialized,
                    'services': {
                        name: service is not None
                        for name, service in self.services.items()
                    },
                    'config_loaded': self.config.config is not None,
                    'timestamp': datetime.utcnow().isoformat()
                }
                return jsonify(status)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        # Register blueprint
        self.app.register_blueprint(monitoring_bp)
        logger.info("Monitoring API endpoints registered")
    
    def get_unified_dashboard(self) -> Dict[str, Any]:
        """Get unified dashboard data from all monitoring services."""
        dashboard = {
            'timestamp': datetime.utcnow().isoformat(),
            'services': {}
        }
        
        # Get data from each service
        for service_name, service in self.services.items():
            try:
                if hasattr(service, 'get_dashboard_data'):
                    dashboard['services'][service_name] = service.get_dashboard_data()
                else:
                    dashboard['services'][service_name] = {'status': 'no_dashboard_data'}
            except Exception as e:
                logger.error(f"Error getting dashboard data from {service_name}: {e}")
                dashboard['services'][service_name] = {'error': str(e)}
        
        # Add aggregated metrics
        dashboard['summary'] = self._generate_summary_metrics()
        
        return dashboard
    
    def _generate_summary_metrics(self) -> Dict[str, Any]:
        """Generate summary metrics across all services."""
        summary = {
            'overall_health': 'unknown',
            'active_alerts': 0,
            'error_rate': 0.0,
            'average_response_time': 0.0,
            'system_load': 0.0
        }
        
        try:
            # Overall health from observability
            if 'observability' in self.services:
                health_summary = self.services['observability'].health_checker.get_health_summary()
                summary['overall_health'] = health_summary['overall_status']
            
            # Active alerts from alerting
            if 'alerting' in self.services:
                alerts_data = self.services['alerting'].get_dashboard_data()
                summary['active_alerts'] = alerts_data['statistics']['total_active']
            
            # Performance metrics
            if 'performance' in self.services:
                perf_data = self.services['performance'].get_dashboard_data()
                summary['error_rate'] = perf_data['performance']['error_rate']
                summary['average_response_time'] = perf_data['performance']['average_response_time']
                summary['system_load'] = perf_data['system']['cpu_usage']
        
        except Exception as e:
            logger.error(f"Error generating summary metrics: {e}")
        
        return summary
    
    def get_service(self, service_name: str):
        """Get a specific monitoring service."""
        return self.services.get(service_name)
    
    def is_service_enabled(self, service_name: str) -> bool:
        """Check if a monitoring service is enabled."""
        return service_name in self.services
    
    def reload_config(self):
        """Reload monitoring configuration."""
        self.config.reload()
        logger.info("Monitoring configuration reloaded")
    
    def shutdown(self):
        """Shutdown all monitoring services."""
        for service_name, service in self.services.items():
            try:
                if hasattr(service, 'shutdown'):
                    service.shutdown()
                logger.info(f"Shut down {service_name} service")
            except Exception as e:
                logger.error(f"Error shutting down {service_name} service: {e}")
        
        logger.info("Monitoring integration shutdown complete")


# Initialize monitoring integration
monitoring_integration = MonitoringIntegration()


# Convenience functions for easy access
def get_monitoring_dashboard():
    """Get unified monitoring dashboard."""
    return monitoring_integration.get_unified_dashboard()


def get_monitoring_service(service_name: str):
    """Get a specific monitoring service."""
    return monitoring_integration.get_service(service_name)


def is_monitoring_enabled():
    """Check if monitoring is enabled."""
    return monitoring_integration.initialized


def record_custom_metric(name: str, value: float, tags: Optional[Dict[str, str]] = None):
    """Record a custom metric."""
    if monitoring_integration.is_service_enabled('observability'):
        observability_service = monitoring_integration.get_service('observability')
        observability_service.record_metric(name, value, tags=tags)


def log_audit_event(event: str, details: Dict[str, Any], user_id: str = None):
    """Log an audit event."""
    if monitoring_integration.is_service_enabled('logging'):
        logging_service = monitoring_integration.get_service('logging')
        logging_service.log_audit_event(event, details, user_id)


def trigger_custom_alert(name: str, description: str, severity: str, metadata: Optional[Dict[str, Any]] = None):
    """Trigger a custom alert."""
    if monitoring_integration.is_service_enabled('alerting'):
        from app.services.alerting_service import Alert, AlertSeverity, AlertStatus
        import uuid
        
        alerting_service = monitoring_integration.get_service('alerting')
        
        # Create custom alert
        alert = Alert(
            id=str(uuid.uuid4()),
            rule_id="custom",
            name=name,
            description=description,
            severity=AlertSeverity(severity),
            status=AlertStatus.ACTIVE,
            value=0.0,
            threshold=0.0,
            condition="custom",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            metadata=metadata or {}
        )
        
        # Add to active alerts
        alerting_service.active_alerts["custom"] = alert
        alerting_service.alert_history.append(alert)