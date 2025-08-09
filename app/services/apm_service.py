"""
Application Performance Monitoring (APM) Service.

This service provides comprehensive APM capabilities including:
- Distributed tracing with request/response tracking
- Request profiling with detailed performance metrics
- Custom metrics collection and analysis
- Error tracking and analysis
- Performance bottleneck identification
"""

import logging
import threading
import time
import traceback
import uuid
from collections import defaultdict, deque
from contextlib import contextmanager
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Dict, List, Optional, Union

from flask import Flask, current_app, g, request

logger = logging.getLogger(__name__)


class TraceContext:
    """Represents a single trace context for request tracking."""

    def __init__(self, trace_id: str, parent_span_id: Optional[str] = None):
        self.trace_id = trace_id
        self.parent_span_id = parent_span_id
        self.spans = []
        self.start_time = time.time()
        self.end_time = None
        self.metadata = {}

    def add_span(self, span: "Span"):
        """Add a span to this trace."""
        self.spans.append(span)

    def finish(self):
        """Mark trace as finished."""
        self.end_time = time.time()

    def get_duration(self) -> float:
        """Get total trace duration."""
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time

    def to_dict(self) -> Dict[str, Any]:
        """Convert trace to dictionary for storage/serialization."""
        return {
            "trace_id": self.trace_id,
            "parent_span_id": self.parent_span_id,
            "spans": [span.to_dict() for span in self.spans],
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.get_duration(),
            "metadata": self.metadata,
        }


class Span:
    """Represents a single operation span within a trace."""

    def __init__(
        self, span_id: str, operation_name: str, parent_span_id: Optional[str] = None
    ):
        self.span_id = span_id
        self.operation_name = operation_name
        self.parent_span_id = parent_span_id
        self.start_time = time.time()
        self.end_time = None
        self.tags = {}
        self.logs = []
        self.error = None

    def set_tag(self, key: str, value: Any):
        """Set a tag on this span."""
        self.tags[key] = value

    def log(self, message: str, level: str = "info"):
        """Add a log entry to this span."""
        self.logs.append({"timestamp": time.time(), "level": level, "message": message})

    def set_error(self, error: Exception):
        """Mark span as having an error."""
        self.error = {
            "type": type(error).__name__,
            "message": str(error),
            "traceback": traceback.format_exc(),
        }
        self.set_tag("error", True)

    def finish(self):
        """Mark span as finished."""
        self.end_time = time.time()

    def get_duration(self) -> float:
        """Get span duration."""
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time

    def to_dict(self) -> Dict[str, Any]:
        """Convert span to dictionary for storage/serialization."""
        return {
            "span_id": self.span_id,
            "operation_name": self.operation_name,
            "parent_span_id": self.parent_span_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.get_duration(),
            "tags": self.tags,
            "logs": self.logs,
            "error": self.error,
        }


class PerformanceProfiler:
    """Profiles performance of operations and functions."""

    def __init__(self):
        self.profiles = deque(maxlen=1000)
        self.function_stats = defaultdict(
            lambda: {
                "call_count": 0,
                "total_time": 0.0,
                "min_time": float("inf"),
                "max_time": 0.0,
                "avg_time": 0.0,
                "last_called": None,
            }
        )

    def profile_function(self, func_name: str, duration: float):
        """Record function performance profile."""
        stats = self.function_stats[func_name]
        stats["call_count"] += 1
        stats["total_time"] += duration
        stats["min_time"] = min(stats["min_time"], duration)
        stats["max_time"] = max(stats["max_time"], duration)
        stats["avg_time"] = stats["total_time"] / stats["call_count"]
        stats["last_called"] = datetime.utcnow()

        # Store individual profile
        self.profiles.append(
            {
                "function": func_name,
                "duration": duration,
                "timestamp": datetime.utcnow(),
                "thread_id": threading.current_thread().ident,
            }
        )

    def get_function_stats(self, func_name: str = None) -> Dict[str, Any]:
        """Get function performance statistics."""
        if func_name:
            return dict(self.function_stats.get(func_name, {}))
        return {k: dict(v) for k, v in self.function_stats.items()}

    def get_slowest_functions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the slowest functions by average time."""
        sorted_funcs = sorted(
            self.function_stats.items(), key=lambda x: x[1]["avg_time"], reverse=True
        )
        return [{"function": func, **stats} for func, stats in sorted_funcs[:limit]]


class CustomMetrics:
    """Collects and manages custom application metrics."""

    def __init__(self):
        self.counters = defaultdict(int)
        self.gauges = defaultdict(float)
        self.histograms = defaultdict(list)
        self.timers = defaultdict(list)
        self.lock = threading.Lock()

    def increment_counter(
        self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None
    ):
        """Increment a counter metric."""
        with self.lock:
            key = self._get_metric_key(name, tags)
            self.counters[key] += value

    def set_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Set a gauge metric value."""
        with self.lock:
            key = self._get_metric_key(name, tags)
            self.gauges[key] = value

    def record_histogram(
        self, name: str, value: float, tags: Optional[Dict[str, str]] = None
    ):
        """Record a value in a histogram metric."""
        with self.lock:
            key = self._get_metric_key(name, tags)
            self.histograms[key].append(value)
            # Keep only last 1000 values
            if len(self.histograms[key]) > 1000:
                self.histograms[key] = self.histograms[key][-1000:]

    def record_timer(
        self, name: str, duration: float, tags: Optional[Dict[str, str]] = None
    ):
        """Record a timer metric."""
        with self.lock:
            key = self._get_metric_key(name, tags)
            self.timers[key].append({"duration": duration, "timestamp": time.time()})
            # Keep only last 1000 values
            if len(self.timers[key]) > 1000:
                self.timers[key] = self.timers[key][-1000:]

    def _get_metric_key(self, name: str, tags: Optional[Dict[str, str]] = None) -> str:
        """Generate a unique key for a metric with tags."""
        if not tags:
            return name
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}[{tag_str}]"

    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all metrics data."""
        with self.lock:
            return {
                "counters": dict(self.counters),
                "gauges": dict(self.gauges),
                "histograms": {
                    k: self._analyze_histogram(v) for k, v in self.histograms.items()
                },
                "timers": {k: self._analyze_timer(v) for k, v in self.timers.items()},
                "timestamp": datetime.utcnow().isoformat(),
            }

    def _analyze_histogram(self, values: List[float]) -> Dict[str, Any]:
        """Analyze histogram values."""
        if not values:
            return {"count": 0, "min": 0, "max": 0, "avg": 0, "p95": 0, "p99": 0}

        sorted_values = sorted(values)
        count = len(sorted_values)

        return {
            "count": count,
            "min": sorted_values[0],
            "max": sorted_values[-1],
            "avg": sum(sorted_values) / count,
            "p95": sorted_values[int(count * 0.95)] if count > 0 else 0,
            "p99": sorted_values[int(count * 0.99)] if count > 0 else 0,
        }

    def _analyze_timer(self, values: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze timer values."""
        if not values:
            return {"count": 0, "min": 0, "max": 0, "avg": 0, "p95": 0, "p99": 0}

        durations = [v["duration"] for v in values]
        return self._analyze_histogram(durations)


class ErrorTracker:
    """Tracks and analyzes application errors."""

    def __init__(self):
        self.errors = deque(maxlen=1000)
        self.error_counts = defaultdict(int)
        self.error_patterns = defaultdict(list)
        self.lock = threading.Lock()

    def record_error(self, error: Exception, context: Optional[Dict[str, Any]] = None):
        """Record an error occurrence."""
        with self.lock:
            error_info = {
                "type": type(error).__name__,
                "message": str(error),
                "traceback": traceback.format_exc(),
                "timestamp": datetime.utcnow(),
                "context": context or {},
            }

            self.errors.append(error_info)
            self.error_counts[error_info["type"]] += 1

            # Track error patterns
            error_pattern = f"{error_info['type']}:{error_info['message']}"
            self.error_patterns[error_pattern].append(error_info["timestamp"])

    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics."""
        with self.lock:
            recent_errors = [
                error
                for error in self.errors
                if error["timestamp"] > datetime.utcnow() - timedelta(hours=24)
            ]

            return {
                "total_errors": len(self.errors),
                "recent_errors": len(recent_errors),
                "error_counts": dict(self.error_counts),
                "most_frequent_errors": self._get_most_frequent_errors(),
                "error_rate_per_hour": self._calculate_error_rate(),
                "last_error": self.errors[-1] if self.errors else None,
            }

    def _get_most_frequent_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most frequent error types."""
        sorted_errors = sorted(
            self.error_counts.items(), key=lambda x: x[1], reverse=True
        )
        return [
            {"error_type": error_type, "count": count}
            for error_type, count in sorted_errors[:limit]
        ]

    def _calculate_error_rate(self) -> float:
        """Calculate error rate per hour."""
        if not self.errors:
            return 0.0

        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        recent_errors = [
            error for error in self.errors if error["timestamp"] > one_hour_ago
        ]

        return len(recent_errors)


class APMService:
    """Main APM service that orchestrates all monitoring components."""

    def __init__(self, app: Flask = None):
        self.app = app
        self.traces = deque(maxlen=1000)
        self.active_traces = {}
        self.profiler = PerformanceProfiler()
        self.metrics = CustomMetrics()
        self.error_tracker = ErrorTracker()
        self.lock = threading.Lock()

        if app:
            self.init_app(app)

    def init_app(self, app: Flask):
        """Initialize APM service with Flask app."""
        self.app = app

        # Register request handlers
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        app.teardown_appcontext(self.teardown_handler)

        # Register error handler
        app.errorhandler(Exception)(self.handle_error)

        # Store reference in app
        app.apm_service = self

    def before_request(self):
        """Start tracing for incoming request."""
        trace_id = str(uuid.uuid4())
        parent_span_id = request.headers.get("X-Trace-Parent-Span-Id")

        # Create trace context
        trace_context = TraceContext(trace_id, parent_span_id)

        # Create root span for request
        root_span = Span(
            span_id=str(uuid.uuid4()),
            operation_name=f"{request.method} {request.endpoint or request.path}",
            parent_span_id=parent_span_id,
        )

        # Set request tags
        root_span.set_tag("http.method", request.method)
        root_span.set_tag("http.url", request.url)
        root_span.set_tag("http.path", request.path)
        root_span.set_tag("user_agent", request.headers.get("User-Agent", ""))

        trace_context.add_span(root_span)

        # Store in request context
        g.trace_context = trace_context
        g.current_span = root_span
        g.request_start_time = time.time()

        # Store in active traces
        with self.lock:
            self.active_traces[trace_id] = trace_context

    def after_request(self, response):
        """Finish tracing for request."""
        if hasattr(g, "trace_context") and hasattr(g, "current_span"):
            # Finish root span
            g.current_span.set_tag("http.status_code", response.status_code)
            g.current_span.finish()

            # Finish trace
            g.trace_context.finish()

            # Store completed trace
            with self.lock:
                self.traces.append(g.trace_context)
                if g.trace_context.trace_id in self.active_traces:
                    del self.active_traces[g.trace_context.trace_id]

            # Record metrics
            duration = g.trace_context.get_duration()
            self.metrics.record_timer(
                "request.duration",
                duration,
                {
                    "method": request.method,
                    "endpoint": request.endpoint or "unknown",
                    "status_code": str(response.status_code),
                },
            )

            # Record in profiler
            self.profiler.profile_function(
                f"{request.method} {request.endpoint or request.path}", duration
            )

            # Add tracing headers to response
            response.headers["X-Trace-Id"] = g.trace_context.trace_id
            response.headers["X-Span-Id"] = g.current_span.span_id

        return response

    def teardown_handler(self, exception):
        """Handle request teardown."""
        if exception and hasattr(g, "current_span"):
            g.current_span.set_error(exception)

            # Safely get request information with fallbacks
            try:
                endpoint = request.endpoint
                method = request.method
            except RuntimeError:
                # Request context is not available
                endpoint = None
                method = None

            self.error_tracker.record_error(
                exception,
                {
                    "trace_id": (
                        g.trace_context.trace_id
                        if hasattr(g, "trace_context")
                        else None
                    ),
                    "span_id": g.current_span.span_id,
                    "endpoint": endpoint,
                    "method": method,
                },
            )

    def handle_error(self, error):
        """Handle application errors."""
        # Safely get request information with fallbacks
        try:
            endpoint = request.endpoint
            method = request.method
        except RuntimeError:
            # Request context is not available
            endpoint = None
            method = None

        self.error_tracker.record_error(
            error,
            {
                "trace_id": (
                    g.trace_context.trace_id if hasattr(g, "trace_context") else None
                ),
                "span_id": (
                    g.current_span.span_id if hasattr(g, "current_span") else None
                ),
                "endpoint": endpoint,
                "method": method,
            },
        )

        # Re-raise the error
        raise error

    @contextmanager
    def create_span(self, operation_name: str, tags: Optional[Dict[str, Any]] = None):
        """Create a new span for an operation."""
        span_id = str(uuid.uuid4())
        parent_span_id = g.current_span.span_id if hasattr(g, "current_span") else None

        span = Span(span_id, operation_name, parent_span_id)

        if tags:
            for key, value in tags.items():
                span.set_tag(key, value)

        # Add to trace context
        if hasattr(g, "trace_context"):
            g.trace_context.add_span(span)

        # Set as current span
        previous_span = getattr(g, "current_span", None)
        g.current_span = span

        try:
            yield span
        except Exception as e:
            span.set_error(e)
            raise
        finally:
            span.finish()
            g.current_span = previous_span

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive APM dashboard data."""
        with self.lock:
            return {
                "traces": {
                    "total": len(self.traces),
                    "active": len(self.active_traces),
                    "recent": [trace.to_dict() for trace in list(self.traces)[-10:]],
                },
                "performance": {
                    "function_stats": self.profiler.get_function_stats(),
                    "slowest_functions": self.profiler.get_slowest_functions(),
                },
                "metrics": self.metrics.get_all_metrics(),
                "errors": self.error_tracker.get_error_stats(),
                "timestamp": datetime.utcnow().isoformat(),
            }

    def get_trace_by_id(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """Get specific trace by ID."""
        with self.lock:
            # Check active traces first
            if trace_id in self.active_traces:
                return self.active_traces[trace_id].to_dict()

            # Check completed traces
            for trace in self.traces:
                if trace.trace_id == trace_id:
                    return trace.to_dict()

        return None

    def search_traces(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search traces based on criteria."""
        results = []

        with self.lock:
            for trace in self.traces:
                if self._matches_query(trace, query):
                    results.append(trace.to_dict())

        return results

    def _matches_query(self, trace: TraceContext, query: Dict[str, Any]) -> bool:
        """Check if trace matches search query."""
        if "min_duration" in query and trace.get_duration() < query["min_duration"]:
            return False

        if "max_duration" in query and trace.get_duration() > query["max_duration"]:
            return False

        if "has_error" in query and query["has_error"]:
            has_error = any(span.error for span in trace.spans)
            if not has_error:
                return False

        if "operation_name" in query:
            operation_names = [span.operation_name for span in trace.spans]
            if query["operation_name"] not in operation_names:
                return False

        return True


# APM decorators
def trace_function(operation_name: str = None, tags: Optional[Dict[str, Any]] = None):
    """Decorator to trace function execution."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            op_name = operation_name or f"{func.__module__}.{func.__name__}"

            # Get APM service
            apm_service = getattr(current_app, "apm_service", None)
            if not apm_service:
                return func(*args, **kwargs)

            with apm_service.create_span(op_name, tags) as span:
                span.set_tag("function.name", func.__name__)
                span.set_tag("function.module", func.__module__)

                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    span.set_tag("function.result_type", type(result).__name__)
                    return result
                finally:
                    duration = time.time() - start_time
                    apm_service.profiler.profile_function(op_name, duration)

        return wrapper

    return decorator


def record_custom_metric(
    metric_name: str,
    value: Union[int, float],
    metric_type: str = "counter",
    tags: Optional[Dict[str, str]] = None,
):
    """Record a custom metric."""
    apm_service = getattr(current_app, "apm_service", None)
    if not apm_service:
        return

    if metric_type == "counter":
        apm_service.metrics.increment_counter(metric_name, int(value), tags)
    elif metric_type == "gauge":
        apm_service.metrics.set_gauge(metric_name, float(value), tags)
    elif metric_type == "histogram":
        apm_service.metrics.record_histogram(metric_name, float(value), tags)
    elif metric_type == "timer":
        apm_service.metrics.record_timer(metric_name, float(value), tags)


# Global APM service instance
apm_service = APMService()
