"""
Performance Monitoring Service for Enterprise Cost Management Platform.

This service provides:
- Real-time performance metrics collection
- Response time monitoring
- Database performance tracking
- Cache performance monitoring
- System resource monitoring
- Alert generation for performance issues
"""

import logging
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Any, Dict, List

import psutil
from flask import Flask, g, request

from app.extensions import get_redis_client

logger = logging.getLogger(__name__)


class PerformanceMetrics:
    """Collects and stores performance metrics."""

    def __init__(self, max_history_size: int = 1000):
        self.max_history_size = max_history_size
        self.request_times = deque(maxlen=max_history_size)
        self.endpoint_times = defaultdict(lambda: deque(maxlen=max_history_size))
        self.error_counts = defaultdict(int)
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "errors": 0,
        }
        self.database_stats = {
            "query_count": 0,
            "slow_queries": 0,
            "connection_errors": 0,
            "total_query_time": 0.0,
        }

    def record_request(
        self, endpoint: str, method: str, duration: float, status_code: int
    ):
        """Record request metrics."""
        self.request_times.append(
            {
                "timestamp": datetime.utcnow(),
                "endpoint": endpoint,
                "method": method,
                "duration": duration,
                "status_code": status_code,
            }
        )

        self.endpoint_times[f"{method} {endpoint}"].append(duration)

        if status_code >= 400:
            self.error_counts[f"{method} {endpoint}"] += 1

    def record_cache_hit(self):
        """Record cache hit."""
        self.cache_stats["hits"] += 1

    def record_cache_miss(self):
        """Record cache miss."""
        self.cache_stats["misses"] += 1

    def record_cache_set(self):
        """Record cache set operation."""
        self.cache_stats["sets"] += 1

    def record_cache_delete(self):
        """Record cache delete operation."""
        self.cache_stats["deletes"] += 1

    def record_cache_error(self):
        """Record cache error."""
        self.cache_stats["errors"] += 1

    def get_cache_hit_ratio(self) -> float:
        """Calculate cache hit ratio."""
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        if total_requests == 0:
            return 0.0
        return self.cache_stats["hits"] / total_requests

    def get_average_response_time(self, endpoint: str = None) -> float:
        """Get average response time for endpoint or overall."""
        if endpoint:
            times = self.endpoint_times.get(endpoint, [])
        else:
            times = [req["duration"] for req in self.request_times]

        if not times:
            return 0.0

        return sum(times) / len(times)

    def get_95th_percentile_response_time(self, endpoint: str = None) -> float:
        """Get 95th percentile response time."""
        if endpoint:
            times = list(self.endpoint_times.get(endpoint, []))
        else:
            times = [req["duration"] for req in self.request_times]

        if not times:
            return 0.0

        times.sort()
        index = int(len(times) * 0.95)
        return times[index] if index < len(times) else times[-1]

    def get_error_rate(self, endpoint: str = None) -> float:
        """Calculate error rate."""
        if endpoint:
            total_requests = len(self.endpoint_times.get(endpoint, []))
            errors = self.error_counts.get(endpoint, 0)
        else:
            total_requests = len(self.request_times)
            errors = sum(self.error_counts.values())

        if total_requests == 0:
            return 0.0

        return errors / total_requests

    def get_requests_per_minute(self) -> float:
        """Calculate requests per minute."""
        if not self.request_times:
            return 0.0

        one_minute_ago = datetime.utcnow() - timedelta(minutes=1)
        recent_requests = [
            req for req in self.request_times if req["timestamp"] > one_minute_ago
        ]

        return len(recent_requests)


class SystemMonitor:
    """Monitors system resources."""

    def get_cpu_usage(self) -> float:
        """Get current CPU usage percentage."""
        return psutil.cpu_percent(interval=1)

    def get_memory_usage(self) -> Dict[str, Any]:
        """Get memory usage statistics."""
        memory = psutil.virtual_memory()
        return {
            "total": memory.total,
            "available": memory.available,
            "used": memory.used,
            "percentage": memory.percent,
        }

    def get_disk_usage(self) -> Dict[str, Any]:
        """Get disk usage statistics."""
        disk = psutil.disk_usage("/")
        return {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percentage": (disk.used / disk.total) * 100,
        }

    def get_network_stats(self) -> Dict[str, Any]:
        """Get network statistics."""
        net_io = psutil.net_io_counters()
        return {
            "bytes_sent": net_io.bytes_sent,
            "bytes_recv": net_io.bytes_recv,
            "packets_sent": net_io.packets_sent,
            "packets_recv": net_io.packets_recv,
        }


class AlertManager:
    """Manages performance alerts."""

    def __init__(self, metrics: PerformanceMetrics):
        self.metrics = metrics
        self.alert_thresholds = {
            "response_time": 5.0,  # seconds
            "error_rate": 0.05,  # 5%
            "cpu_usage": 80.0,  # percentage
            "memory_usage": 85.0,  # percentage
            "disk_usage": 90.0,  # percentage
            "cache_hit_ratio": 0.8,  # 80%
        }
        self.active_alerts = set()

    def check_alerts(self) -> List[Dict[str, Any]]:
        """Check for performance issues and generate alerts."""
        alerts = []

        # Check response time
        avg_response_time = self.metrics.get_average_response_time()
        if avg_response_time > self.alert_thresholds["response_time"]:
            alert = {
                "type": "response_time",
                "severity": "high",
                "message": f"Average response time is {avg_response_time:.2f}s",
                "threshold": self.alert_thresholds["response_time"],
                "current_value": avg_response_time,
            }
            alerts.append(alert)

        # Check error rate
        error_rate = self.metrics.get_error_rate()
        if error_rate > self.alert_thresholds["error_rate"]:
            alert = {
                "type": "error_rate",
                "severity": "medium",
                "message": f"Error rate is {error_rate:.2%}",
                "threshold": self.alert_thresholds["error_rate"],
                "current_value": error_rate,
            }
            alerts.append(alert)

        # Check cache hit ratio
        cache_hit_ratio = self.metrics.get_cache_hit_ratio()
        if cache_hit_ratio < self.alert_thresholds["cache_hit_ratio"]:
            alert = {
                "type": "cache_hit_ratio",
                "severity": "medium",
                "message": f"Cache hit ratio is {cache_hit_ratio:.2%}",
                "threshold": self.alert_thresholds["cache_hit_ratio"],
                "current_value": cache_hit_ratio,
            }
            alerts.append(alert)

        # Check system resources
        system_monitor = SystemMonitor()

        cpu_usage = system_monitor.get_cpu_usage()
        if cpu_usage > self.alert_thresholds["cpu_usage"]:
            alert = {
                "type": "cpu_usage",
                "severity": "high",
                "message": f"CPU usage is {cpu_usage:.1f}%",
                "threshold": self.alert_thresholds["cpu_usage"],
                "current_value": cpu_usage,
            }
            alerts.append(alert)

        memory_usage = system_monitor.get_memory_usage()
        if memory_usage["percentage"] > self.alert_thresholds["memory_usage"]:
            alert = {
                "type": "memory_usage",
                "severity": "high",
                "message": f'Memory usage is {memory_usage["percentage"]:.1f}%',
                "threshold": self.alert_thresholds["memory_usage"],
                "current_value": memory_usage["percentage"],
            }
            alerts.append(alert)

        return alerts


class PerformanceMonitor:
    """Main performance monitoring service."""

    def __init__(self, app: Flask = None):
        self.app = app
        self.metrics = PerformanceMetrics()
        self.system_monitor = SystemMonitor()
        self.alert_manager = AlertManager(self.metrics)

        if app:
            self.init_app(app)

    def init_app(self, app: Flask):
        """Initialize with Flask app."""
        self.app = app

        # Register request handlers
        app.before_request(self.before_request)
        app.after_request(self.after_request)

        # Register teardown handler
        app.teardown_appcontext(self.teardown_handler)

    def before_request(self):
        """Record request start time."""
        g.start_time = time.time()

    def after_request(self, response):
        """Record request metrics."""
        if hasattr(g, "start_time"):
            duration = time.time() - g.start_time

            self.metrics.record_request(
                endpoint=request.endpoint or "unknown",
                method=request.method,
                duration=duration,
                status_code=response.status_code,
            )

            # Log slow requests
            if duration > 1.0:
                logger.warning(
                    f"Slow request: {request.method} {request.endpoint} "
                    f"took {duration:.3f}s"
                )

        return response

    def teardown_handler(self, exception):
        """Handle request teardown."""
        if exception:
            logger.error(f"Request ended with exception: {exception}")

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive performance dashboard data."""
        system_stats = {
            "cpu_usage": self.system_monitor.get_cpu_usage(),
            "memory_usage": self.system_monitor.get_memory_usage(),
            "disk_usage": self.system_monitor.get_disk_usage(),
            "network_stats": self.system_monitor.get_network_stats(),
        }

        cache_stats = {
            "hit_ratio": self.metrics.get_cache_hit_ratio(),
            "operations": self.metrics.cache_stats,
        }

        performance_stats = {
            "average_response_time": self.metrics.get_average_response_time(),
            "p95_response_time": self.metrics.get_95th_percentile_response_time(),
            "error_rate": self.metrics.get_error_rate(),
            "requests_per_minute": self.metrics.get_requests_per_minute(),
        }

        alerts = self.alert_manager.check_alerts()

        return {
            "system": system_stats,
            "cache": cache_stats,
            "performance": performance_stats,
            "alerts": alerts,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def get_endpoint_metrics(self, endpoint: str) -> Dict[str, Any]:
        """Get metrics for specific endpoint."""
        return {
            "endpoint": endpoint,
            "average_response_time": self.metrics.get_average_response_time(endpoint),
            "p95_response_time": self.metrics.get_95th_percentile_response_time(
                endpoint
            ),
            "error_rate": self.metrics.get_error_rate(endpoint),
            "request_count": len(self.metrics.endpoint_times.get(endpoint, [])),
            "error_count": self.metrics.error_counts.get(endpoint, 0),
        }

    def reset_metrics(self):
        """Reset all metrics (for testing)."""
        self.metrics = PerformanceMetrics()
        self.alert_manager = AlertManager(self.metrics)


# Enhanced cache decorator with performance monitoring
def cached_with_monitoring(timeout: int = 3600, key_prefix: str = "cache"):
    """Cache decorator with performance monitoring."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"

            # Try to get from cache
            redis_client = get_redis_client()
            if redis_client:
                try:
                    cached_result = redis_client.get(cache_key)
                    if cached_result:
                        performance_monitor.metrics.record_cache_hit()
                        return cached_result
                    else:
                        performance_monitor.metrics.record_cache_miss()
                except Exception as e:
                    performance_monitor.metrics.record_cache_error()
                    logger.error(f"Cache error: {e}")

            # Execute function
            result = func(*args, **kwargs)

            # Cache result
            if redis_client:
                try:
                    redis_client.setex(cache_key, timeout, result)
                    performance_monitor.metrics.record_cache_set()
                except Exception as e:
                    performance_monitor.metrics.record_cache_error()
                    logger.error(f"Cache set error: {e}")

            return result

        return wrapper

    return decorator


# Global performance monitor instance
performance_monitor = PerformanceMonitor()
