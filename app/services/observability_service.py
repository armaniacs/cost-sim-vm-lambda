"""
Observability Service for Enterprise Cost Management Platform.

This service provides comprehensive observability infrastructure including:
- Metrics collection and storage
- Health checks and uptime monitoring
- Custom dashboards and visualization
- Distributed tracing integration
- Service dependency mapping
- SLA monitoring and reporting
"""

import logging
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import psutil
import requests
from flask import Flask

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health check status values."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class MetricType(Enum):
    """Metric types."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class MetricValue:
    """Represents a metric value with timestamp."""

    value: float
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class HealthCheck:
    """Represents a health check configuration."""

    name: str
    url: str
    method: str = "GET"
    timeout: int = 5
    interval: int = 60
    expected_status: int = 200
    expected_content: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)
    enabled: bool = True
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class ServiceDependency:
    """Represents a service dependency."""

    name: str
    type: str  # database, cache, api, etc.
    endpoint: str
    critical: bool = True
    health_check: Optional[HealthCheck] = None


class MetricsCollector:
    """Collects and stores metrics."""

    def __init__(self, retention_period: int = 86400):  # 24 hours
        self.metrics = defaultdict(lambda: deque(maxlen=1000))
        self.retention_period = retention_period
        self.lock = threading.Lock()

    def record_metric(
        self,
        name: str,
        value: float,
        metric_type: MetricType,
        tags: Optional[Dict[str, str]] = None,
    ):
        """Record a metric value."""
        with self.lock:
            metric_value = MetricValue(
                value=value, timestamp=datetime.utcnow(), tags=tags or {}
            )

            key = self._get_metric_key(name, tags)
            self.metrics[key].append(metric_value)

    def get_metric_values(
        self,
        name: str,
        tags: Optional[Dict[str, str]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[MetricValue]:
        """Get metric values."""
        with self.lock:
            key = self._get_metric_key(name, tags)
            values = list(self.metrics[key])

            # Filter by time range
            if start_time or end_time:
                filtered_values = []
                for value in values:
                    if start_time and value.timestamp < start_time:
                        continue
                    if end_time and value.timestamp > end_time:
                        continue
                    filtered_values.append(value)
                values = filtered_values

            return values

    def get_latest_metric_value(
        self, name: str, tags: Optional[Dict[str, str]] = None
    ) -> Optional[MetricValue]:
        """Get the latest metric value."""
        with self.lock:
            key = self._get_metric_key(name, tags)
            values = self.metrics[key]
            return values[-1] if values else None

    def get_metric_statistics(
        self,
        name: str,
        tags: Optional[Dict[str, str]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get metric statistics."""
        values = self.get_metric_values(name, tags, start_time, end_time)

        if not values:
            return {"count": 0, "min": 0, "max": 0, "avg": 0, "sum": 0}

        numeric_values = [v.value for v in values]

        return {
            "count": len(numeric_values),
            "min": min(numeric_values),
            "max": max(numeric_values),
            "avg": sum(numeric_values) / len(numeric_values),
            "sum": sum(numeric_values),
            "p50": self._percentile(numeric_values, 0.5),
            "p95": self._percentile(numeric_values, 0.95),
            "p99": self._percentile(numeric_values, 0.99),
        }

    def _get_metric_key(self, name: str, tags: Optional[Dict[str, str]] = None) -> str:
        """Generate a unique key for a metric with tags."""
        if not tags:
            return name
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}[{tag_str}]"

    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile."""
        if not values:
            return 0.0

        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile)
        return sorted_values[min(index, len(sorted_values) - 1)]

    def cleanup_old_metrics(self):
        """Clean up old metric values."""
        with self.lock:
            cutoff_time = datetime.utcnow() - timedelta(seconds=self.retention_period)

            for key in list(self.metrics.keys()):
                values = self.metrics[key]
                # Remove old values
                while values and values[0].timestamp < cutoff_time:
                    values.popleft()

                # Remove empty metric keys
                if not values:
                    del self.metrics[key]


class HealthChecker:
    """Performs health checks on services and dependencies."""

    def __init__(self):
        self.health_checks = {}
        self.health_results = defaultdict(lambda: deque(maxlen=100))
        self.lock = threading.Lock()

    def add_health_check(self, check: HealthCheck):
        """Add a health check."""
        with self.lock:
            self.health_checks[check.name] = check

    def remove_health_check(self, name: str):
        """Remove a health check."""
        with self.lock:
            if name in self.health_checks:
                del self.health_checks[name]

    def perform_health_check(self, check: HealthCheck) -> Dict[str, Any]:
        """Perform a single health check."""
        start_time = time.time()

        try:
            response = requests.request(
                method=check.method,
                url=check.url,
                headers=check.headers,
                timeout=check.timeout,
            )

            duration = time.time() - start_time

            # Check status code
            status_ok = response.status_code == check.expected_status

            # Check content if specified
            content_ok = True
            if check.expected_content:
                content_ok = check.expected_content in response.text

            # Determine overall health
            if status_ok and content_ok:
                health_status = HealthStatus.HEALTHY
            else:
                health_status = HealthStatus.UNHEALTHY

            result = {
                "name": check.name,
                "status": health_status.value,
                "response_time": duration,
                "status_code": response.status_code,
                "expected_status": check.expected_status,
                "content_check": content_ok,
                "timestamp": datetime.utcnow(),
                "error": None,
                "tags": check.tags,
            }

        except requests.RequestException as e:
            duration = time.time() - start_time
            result = {
                "name": check.name,
                "status": HealthStatus.UNHEALTHY.value,
                "response_time": duration,
                "status_code": None,
                "expected_status": check.expected_status,
                "content_check": False,
                "timestamp": datetime.utcnow(),
                "error": str(e),
                "tags": check.tags,
            }

        # Store result
        with self.lock:
            self.health_results[check.name].append(result)

        return result

    def perform_all_health_checks(self) -> Dict[str, Any]:
        """Perform all enabled health checks."""
        results = {}

        with self.lock:
            checks_to_perform = [
                check for check in self.health_checks.values() if check.enabled
            ]

        for check in checks_to_perform:
            results[check.name] = self.perform_health_check(check)

        return results

    def get_health_summary(self) -> Dict[str, Any]:
        """Get overall health summary."""
        with self.lock:
            total_checks = len(self.health_checks)
            healthy_count = 0
            degraded_count = 0
            unhealthy_count = 0

            service_health = {}

            for check_name, check in self.health_checks.items():
                if not check.enabled:
                    continue

                results = self.health_results[check_name]
                if results:
                    latest_result = results[-1]
                    service_health[check_name] = latest_result

                    if latest_result["status"] == HealthStatus.HEALTHY.value:
                        healthy_count += 1
                    elif latest_result["status"] == HealthStatus.DEGRADED.value:
                        degraded_count += 1
                    else:
                        unhealthy_count += 1

            # Determine overall health
            if unhealthy_count > 0:
                overall_status = HealthStatus.UNHEALTHY.value
            elif degraded_count > 0:
                overall_status = HealthStatus.DEGRADED.value
            else:
                overall_status = HealthStatus.HEALTHY.value

            return {
                "overall_status": overall_status,
                "total_checks": total_checks,
                "healthy_count": healthy_count,
                "degraded_count": degraded_count,
                "unhealthy_count": unhealthy_count,
                "service_health": service_health,
                "timestamp": datetime.utcnow().isoformat(),
            }

    def get_health_history(
        self, service_name: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get health check history for a service."""
        with self.lock:
            results = list(self.health_results.get(service_name, []))
            return results[-limit:]


class ServiceDependencyMapper:
    """Maps and monitors service dependencies."""

    def __init__(self):
        self.dependencies = {}
        self.dependency_graph = defaultdict(list)
        self.lock = threading.Lock()

    def add_dependency(self, service_name: str, dependency: ServiceDependency):
        """Add a service dependency."""
        with self.lock:
            if service_name not in self.dependencies:
                self.dependencies[service_name] = []

            self.dependencies[service_name].append(dependency)
            self.dependency_graph[service_name].append(dependency.name)

    def get_dependencies(self, service_name: str) -> List[ServiceDependency]:
        """Get dependencies for a service."""
        with self.lock:
            return self.dependencies.get(service_name, [])

    def get_dependency_graph(self) -> Dict[str, List[str]]:
        """Get the full dependency graph."""
        with self.lock:
            return dict(self.dependency_graph)

    def check_dependencies(
        self, service_name: str, health_checker: HealthChecker
    ) -> Dict[str, Any]:
        """Check health of all dependencies for a service."""
        dependencies = self.get_dependencies(service_name)
        results = {}

        for dependency in dependencies:
            if dependency.health_check:
                result = health_checker.perform_health_check(dependency.health_check)
                results[dependency.name] = {
                    "status": result["status"],
                    "critical": dependency.critical,
                    "type": dependency.type,
                    "response_time": result["response_time"],
                    "error": result.get("error"),
                }

        return results


class SLAMonitor:
    """Monitors SLA metrics and compliance."""

    def __init__(self):
        self.sla_targets = {}
        self.sla_metrics = defaultdict(lambda: deque(maxlen=1000))
        self.lock = threading.Lock()

    def add_sla_target(self, name: str, target: Dict[str, Any]):
        """Add an SLA target."""
        with self.lock:
            self.sla_targets[name] = target

    def record_sla_metric(
        self, name: str, value: float, timestamp: Optional[datetime] = None
    ):
        """Record an SLA metric value."""
        with self.lock:
            metric_entry = {"value": value, "timestamp": timestamp or datetime.utcnow()}
            self.sla_metrics[name].append(metric_entry)

    def calculate_sla_compliance(
        self, name: str, period_hours: int = 24
    ) -> Dict[str, Any]:
        """Calculate SLA compliance for a period."""
        with self.lock:
            if name not in self.sla_targets:
                return {"error": "SLA target not found"}

            target = self.sla_targets[name]
            metrics = self.sla_metrics[name]

            # Filter metrics for the period
            start_time = datetime.utcnow() - timedelta(hours=period_hours)
            period_metrics = [m for m in metrics if m["timestamp"] >= start_time]

            if not period_metrics:
                return {"error": "No metrics available for period"}

            values = [m["value"] for m in period_metrics]

            # Calculate compliance based on target type
            if target["type"] == "availability":
                # Availability: percentage of successful checks
                successful = sum(1 for v in values if v >= target["threshold"])
                compliance = (successful / len(values)) * 100
            elif target["type"] == "response_time":
                # Response time: percentage of requests under threshold
                under_threshold = sum(1 for v in values if v <= target["threshold"])
                compliance = (under_threshold / len(values)) * 100
            elif target["type"] == "error_rate":
                # Error rate: percentage of requests with low error rate
                low_error = sum(1 for v in values if v <= target["threshold"])
                compliance = (low_error / len(values)) * 100
            else:
                return {"error": "Unknown SLA type"}

            return {
                "name": name,
                "compliance": compliance,
                "target": target["target"],
                "met": compliance >= target["target"],
                "threshold": target["threshold"],
                "period_hours": period_hours,
                "data_points": len(values),
                "timestamp": datetime.utcnow().isoformat(),
            }

    def get_sla_dashboard(self) -> Dict[str, Any]:
        """Get SLA dashboard data."""
        dashboard = {}

        with self.lock:
            for name in self.sla_targets:
                dashboard[name] = self.calculate_sla_compliance(name)

        return dashboard


class ObservabilityService:
    """Main observability service that orchestrates all monitoring components."""

    def __init__(self, app: Flask = None):
        self.app = app
        self.metrics_collector = MetricsCollector()
        self.health_checker = HealthChecker()
        self.dependency_mapper = ServiceDependencyMapper()
        self.sla_monitor = SLAMonitor()
        self.custom_collectors = {}

        if app:
            self.init_app(app)

    def init_app(self, app: Flask):
        """Initialize observability service with Flask app."""
        self.app = app

        # Set up default health checks
        self._setup_default_health_checks()

        # Set up default dependencies
        self._setup_default_dependencies()

        # Set up default SLA targets
        self._setup_default_sla_targets()

        # Start background workers
        self._start_background_workers()

        # Store reference in app
        app.observability_service = self

    def _setup_default_health_checks(self):
        """Set up default health checks."""
        # Application health check
        app_health = HealthCheck(
            name="application",
            url="http://localhost:5001/health",
            method="GET",
            timeout=5,
            interval=30,
            expected_status=200,
            tags={"service": "application", "critical": "true"},
        )
        self.health_checker.add_health_check(app_health)

        # API health check
        api_health = HealthCheck(
            name="api",
            url="http://localhost:5001/api",
            method="GET",
            timeout=5,
            interval=60,
            expected_status=200,
            tags={"service": "api", "critical": "true"},
        )
        self.health_checker.add_health_check(api_health)

    def _setup_default_dependencies(self):
        """Set up default service dependencies."""
        # Database dependency
        db_dependency = ServiceDependency(
            name="database",
            type="database",
            endpoint="postgresql://localhost:5432",
            critical=True,
            health_check=HealthCheck(
                name="database",
                url="postgresql://localhost:5432",
                method="GET",
                timeout=10,
                interval=60,
                tags={"service": "database", "critical": "true"},
            ),
        )
        self.dependency_mapper.add_dependency("application", db_dependency)

        # Redis dependency
        redis_dependency = ServiceDependency(
            name="redis",
            type="cache",
            endpoint="redis://localhost:6379",
            critical=False,
            health_check=HealthCheck(
                name="redis",
                url="redis://localhost:6379",
                method="GET",
                timeout=5,
                interval=60,
                tags={"service": "redis", "critical": "false"},
            ),
        )
        self.dependency_mapper.add_dependency("application", redis_dependency)

    def _setup_default_sla_targets(self):
        """Set up default SLA targets."""
        # Application availability SLA
        self.sla_monitor.add_sla_target(
            "application_availability",
            {
                "type": "availability",
                "target": 99.9,  # 99.9% uptime
                "threshold": 1,  # 1 = healthy
                "description": "Application uptime SLA",
            },
        )

        # Response time SLA
        self.sla_monitor.add_sla_target(
            "response_time",
            {
                "type": "response_time",
                "target": 95.0,  # 95% of requests under threshold
                "threshold": 2.0,  # 2 seconds
                "description": "API response time SLA",
            },
        )

        # Error rate SLA
        self.sla_monitor.add_sla_target(
            "error_rate",
            {
                "type": "error_rate",
                "target": 99.5,  # 99.5% of requests with low error rate
                "threshold": 0.01,  # 1% error rate
                "description": "Application error rate SLA",
            },
        )

    def _start_background_workers(self):
        """Start background worker threads."""

        def health_check_worker():
            while True:
                try:
                    self.health_checker.perform_all_health_checks()
                    time.sleep(30)  # Check every 30 seconds
                except Exception as e:
                    logger.error(f"Error in health check worker: {e}")
                    time.sleep(60)

        def metrics_cleanup_worker():
            while True:
                try:
                    self.metrics_collector.cleanup_old_metrics()
                    time.sleep(3600)  # Clean up every hour
                except Exception as e:
                    logger.error(f"Error in metrics cleanup worker: {e}")
                    time.sleep(3600)

        def sla_monitoring_worker():
            while True:
                try:
                    # Collect SLA metrics
                    self._collect_sla_metrics()
                    time.sleep(300)  # Collect every 5 minutes
                except Exception as e:
                    logger.error(f"Error in SLA monitoring worker: {e}")
                    time.sleep(300)

        health_thread = threading.Thread(target=health_check_worker, daemon=True)
        cleanup_thread = threading.Thread(target=metrics_cleanup_worker, daemon=True)
        sla_thread = threading.Thread(target=sla_monitoring_worker, daemon=True)

        health_thread.start()
        cleanup_thread.start()
        sla_thread.start()

    def _collect_sla_metrics(self):
        """Collect SLA metrics from various sources."""
        # Application availability from health checks
        health_summary = self.health_checker.get_health_summary()
        if health_summary["overall_status"] == HealthStatus.HEALTHY.value:
            self.sla_monitor.record_sla_metric("application_availability", 1)
        else:
            self.sla_monitor.record_sla_metric("application_availability", 0)

        # Response time from APM
        try:
            from app.services.apm_service import apm_service

            dashboard_data = apm_service.get_dashboard_data()
            avg_response_time = dashboard_data["performance"]["function_stats"].get(
                "avg_time", 0
            )
            self.sla_monitor.record_sla_metric("response_time", avg_response_time)
        except Exception as e:
            logger.error(f"Error collecting response time SLA metric: {e}")

        # Error rate from APM
        try:
            from app.services.apm_service import apm_service

            dashboard_data = apm_service.get_dashboard_data()
            error_stats = dashboard_data["errors"]
            error_rate = (
                error_stats.get("error_rate_per_hour", 0) / 100
            )  # Convert to percentage
            self.sla_monitor.record_sla_metric("error_rate", error_rate)
        except Exception as e:
            logger.error(f"Error collecting error rate SLA metric: {e}")

    def record_metric(
        self,
        name: str,
        value: float,
        metric_type: MetricType = MetricType.GAUGE,
        tags: Optional[Dict[str, str]] = None,
    ):
        """Record a metric."""
        self.metrics_collector.record_metric(name, value, metric_type, tags)

    def get_metric_statistics(
        self,
        name: str,
        tags: Optional[Dict[str, str]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get metric statistics."""
        return self.metrics_collector.get_metric_statistics(
            name, tags, start_time, end_time
        )

    def add_custom_collector(
        self, name: str, collector_func: Callable[[], Dict[str, Any]]
    ):
        """Add a custom metrics collector."""
        self.custom_collectors[name] = collector_func

    def get_observability_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive observability dashboard."""
        try:
            # Get data from all components
            health_summary = self.health_checker.get_health_summary()
            sla_dashboard = self.sla_monitor.get_sla_dashboard()
            dependency_graph = self.dependency_mapper.get_dependency_graph()

            # Get system metrics
            system_metrics = self._get_system_metrics()

            # Get application metrics
            app_metrics = self._get_application_metrics()

            # Get custom metrics
            custom_metrics = {}
            for name, collector in self.custom_collectors.items():
                try:
                    custom_metrics[name] = collector()
                except Exception as e:
                    logger.error(f"Error collecting custom metrics '{name}': {e}")
                    custom_metrics[name] = {"error": str(e)}

            return {
                "health": health_summary,
                "sla": sla_dashboard,
                "dependencies": dependency_graph,
                "system_metrics": system_metrics,
                "application_metrics": app_metrics,
                "custom_metrics": custom_metrics,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting observability dashboard: {e}")
            return {"error": str(e), "timestamp": datetime.utcnow().isoformat()}

    def _get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics."""
        try:
            return {
                "cpu_usage": psutil.cpu_percent(interval=1),
                "memory": {
                    "usage": psutil.virtual_memory().percent,
                    "available": psutil.virtual_memory().available,
                    "total": psutil.virtual_memory().total,
                },
                "disk": {
                    "usage": psutil.disk_usage("/").percent,
                    "free": psutil.disk_usage("/").free,
                    "total": psutil.disk_usage("/").total,
                },
                "network": {
                    "bytes_sent": psutil.net_io_counters().bytes_sent,
                    "bytes_recv": psutil.net_io_counters().bytes_recv,
                },
            }
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {"error": str(e)}

    def _get_application_metrics(self) -> Dict[str, Any]:
        """Get current application metrics."""
        try:
            # Get metrics from various sources
            metrics = {}

            # Performance metrics
            try:
                from app.services.performance_monitor import performance_monitor

                metrics["performance"] = performance_monitor.get_dashboard_data()
            except Exception as e:
                logger.error(f"Error getting performance metrics: {e}")
                metrics["performance"] = {"error": str(e)}

            # APM metrics
            try:
                from app.services.apm_service import apm_service

                metrics["apm"] = apm_service.get_dashboard_data()
            except Exception as e:
                logger.error(f"Error getting APM metrics: {e}")
                metrics["apm"] = {"error": str(e)}

            # Logging metrics
            try:
                from app.services.logging_service import logging_service

                metrics["logging"] = logging_service.get_dashboard_data()
            except Exception as e:
                logger.error(f"Error getting logging metrics: {e}")
                metrics["logging"] = {"error": str(e)}

            # Alerting metrics
            try:
                from app.services.alerting_service import alerting_service

                metrics["alerting"] = alerting_service.get_dashboard_data()
            except Exception as e:
                logger.error(f"Error getting alerting metrics: {e}")
                metrics["alerting"] = {"error": str(e)}

            return metrics

        except Exception as e:
            logger.error(f"Error getting application metrics: {e}")
            return {"error": str(e)}

    def get_service_health(self, service_name: str) -> Dict[str, Any]:
        """Get health status for a specific service."""
        # Check direct health
        health_summary = self.health_checker.get_health_summary()
        service_health = health_summary["service_health"].get(service_name, {})

        # Check dependencies
        dependencies = self.dependency_mapper.check_dependencies(
            service_name, self.health_checker
        )

        return {
            "service": service_name,
            "health": service_health,
            "dependencies": dependencies,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def get_metrics_for_dashboard(
        self, metric_names: List[str], time_range: int = 3600
    ) -> Dict[str, Any]:
        """Get metrics for dashboard visualization."""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(seconds=time_range)

        metrics_data = {}

        for metric_name in metric_names:
            try:
                values = self.metrics_collector.get_metric_values(
                    metric_name, start_time=start_time, end_time=end_time
                )

                metrics_data[metric_name] = {
                    "values": [
                        {"timestamp": v.timestamp.isoformat(), "value": v.value}
                        for v in values
                    ],
                    "statistics": self.metrics_collector.get_metric_statistics(
                        metric_name, start_time=start_time, end_time=end_time
                    ),
                }
            except Exception as e:
                logger.error(f"Error getting metric '{metric_name}': {e}")
                metrics_data[metric_name] = {"error": str(e)}

        return metrics_data


# Global observability service instance
observability_service = ObservabilityService()
