"""
Unit tests for APM (Application Performance Monitoring) Service
Tests the core APM functionality with proper implementation matching
"""

import threading
import time

import pytest
from flask import Flask

# Import what we can from the actual implementation
try:
    from app.services.apm_service import (
        APMService,
        CustomMetrics,
        ErrorTracker,
        PerformanceProfiler,
        Span,
        TraceContext,
    )
except ImportError:
    # Skip tests if imports fail
    pytest.skip("APM Service module not available", allow_module_level=True)


class TestTraceContext:
    """Test TraceContext functionality"""

    def test_trace_context_creation(self):
        """Test TraceContext initialization"""
        trace_id = "test-trace-123"
        context = TraceContext(trace_id)

        assert context.trace_id == trace_id
        assert context.spans == []
        assert context.start_time is not None
        assert context.end_time is None
        assert context.metadata == {}

    def test_trace_context_with_parent_span_id(self):
        """Test TraceContext with parent span ID"""
        trace_id = "test-trace-123"
        parent_span_id = "parent-span-456"
        context = TraceContext(trace_id, parent_span_id=parent_span_id)

        assert context.trace_id == trace_id
        assert context.parent_span_id == parent_span_id
        assert context.metadata == {}

    def test_add_span(self):
        """Test adding span to trace context"""
        context = TraceContext("test-trace")
        span = Span("span-123", "test-operation")

        context.add_span(span)

        assert len(context.spans) == 1
        assert context.spans[0] == span

    def test_finish_trace(self):
        """Test finishing trace context"""
        context = TraceContext("test-trace")
        assert context.end_time is None

        context.finish()
        assert context.end_time is not None

    def test_get_duration(self):
        """Test getting trace duration"""
        context = TraceContext("test-trace")
        time.sleep(0.01)

        duration = context.get_duration()
        assert duration > 0

        context.finish()
        final_duration = context.get_duration()
        assert final_duration >= duration

    def test_to_dict(self):
        """Test converting trace to dictionary"""
        context = TraceContext("test-trace")
        span = Span("span-1", "test-op")
        context.add_span(span)

        result = context.to_dict()

        assert result["trace_id"] == "test-trace"
        assert "spans" in result
        assert "start_time" in result
        assert "duration" in result
        assert "metadata" in result


class TestSpan:
    """Test Span functionality"""

    def test_span_creation(self):
        """Test Span initialization"""
        span_id = "span-123"
        operation_name = "database_query"
        span = Span(span_id, operation_name)

        assert span.span_id == span_id
        assert span.operation_name == operation_name
        assert span.parent_span_id is None
        assert span.start_time is not None
        assert span.end_time is None
        assert span.tags == {}
        assert span.logs == []
        assert span.error is None

    def test_span_with_parent_span_id(self):
        """Test Span with parent span ID"""
        span_id = "child-span"
        operation_name = "query"
        parent_span_id = "parent-span"
        span = Span(span_id, operation_name, parent_span_id=parent_span_id)

        assert span.parent_span_id == parent_span_id

    def test_set_tag(self):
        """Test setting tags on span"""
        span = Span("span-123", "test-op")

        span.set_tag("key1", "value1")
        span.set_tag("key2", 42)

        assert span.tags["key1"] == "value1"
        assert span.tags["key2"] == 42

    def test_log_message(self):
        """Test logging message to span"""
        span = Span("span-123", "test-op")

        span.log("Test message")
        span.log("Error occurred", "error")

        assert len(span.logs) == 2
        assert span.logs[0]["message"] == "Test message"
        assert span.logs[0]["level"] == "info"
        assert span.logs[1]["message"] == "Error occurred"
        assert span.logs[1]["level"] == "error"

    def test_set_error(self):
        """Test setting error on span"""
        span = Span("span-123", "test-op")
        error = ValueError("Test error")

        span.set_error(error)

        assert span.error is not None
        assert span.error["type"] == "ValueError"
        assert span.error["message"] == "Test error"
        assert span.tags["error"] is True

    def test_finish_span(self):
        """Test finishing span"""
        span = Span("span-123", "test-op")
        time.sleep(0.01)

        span.finish()

        assert span.end_time is not None
        duration = span.get_duration()
        assert duration > 0

    def test_to_dict(self):
        """Test converting span to dictionary"""
        span = Span("span-123", "test-op")
        span.set_tag("test", "value")
        span.log("test message")

        result = span.to_dict()

        assert result["span_id"] == "span-123"
        assert result["operation_name"] == "test-op"
        assert "start_time" in result
        assert "tags" in result
        assert "logs" in result


class TestPerformanceProfiler:
    """Test PerformanceProfiler functionality"""

    def test_profiler_initialization(self):
        """Test profiler initialization"""
        profiler = PerformanceProfiler()

        assert len(profiler.profiles) == 0
        assert len(profiler.function_stats) == 0

    def test_profile_function(self):
        """Test profiling a function"""
        profiler = PerformanceProfiler()

        profiler.profile_function("test_function", 0.15)
        profiler.profile_function("test_function", 0.25)

        assert len(profiler.profiles) == 2

        stats = profiler.get_function_stats("test_function")
        assert stats["call_count"] == 2
        assert stats["total_time"] == 0.4
        assert stats["min_time"] == 0.15
        assert stats["max_time"] == 0.25
        assert pytest.approx(stats["avg_time"], rel=1e-9) == 0.2

    def test_get_function_stats_all(self):
        """Test getting all function stats"""
        profiler = PerformanceProfiler()

        profiler.profile_function("func1", 0.1)
        profiler.profile_function("func2", 0.2)

        all_stats = profiler.get_function_stats()

        assert "func1" in all_stats
        assert "func2" in all_stats
        assert all_stats["func1"]["call_count"] == 1
        assert all_stats["func2"]["call_count"] == 1

    def test_get_slowest_functions(self):
        """Test getting slowest functions"""
        profiler = PerformanceProfiler()

        profiler.profile_function("fast_func", 0.01)
        profiler.profile_function("slow_func", 0.5)
        profiler.profile_function("medium_func", 0.1)

        slowest = profiler.get_slowest_functions(limit=2)

        assert len(slowest) == 2
        assert slowest[0]["function"] == "slow_func"
        assert slowest[1]["function"] == "medium_func"


class TestCustomMetrics:
    """Test CustomMetrics functionality"""

    def test_metrics_initialization(self):
        """Test metrics initialization"""
        metrics = CustomMetrics()

        assert len(metrics.counters) == 0
        assert len(metrics.gauges) == 0
        assert len(metrics.histograms) == 0
        assert len(metrics.timers) == 0

    def test_increment_counter(self):
        """Test incrementing counter metric"""
        metrics = CustomMetrics()

        metrics.increment_counter("requests")
        metrics.increment_counter("requests", 5)
        metrics.increment_counter("errors", 1)

        assert metrics.counters["requests"] == 6
        assert metrics.counters["errors"] == 1

    def test_set_gauge(self):
        """Test setting gauge metric"""
        metrics = CustomMetrics()

        metrics.set_gauge("cpu_usage", 75.5)
        metrics.set_gauge("memory_usage", 85.2)

        assert metrics.gauges["cpu_usage"] == 75.5
        assert metrics.gauges["memory_usage"] == 85.2

    def test_record_histogram(self):
        """Test recording histogram values"""
        metrics = CustomMetrics()

        metrics.record_histogram("response_time", 150)
        metrics.record_histogram("response_time", 200)
        metrics.record_histogram("response_time", 100)

        assert "response_time" in metrics.histograms
        assert len(metrics.histograms["response_time"]) == 3

    def test_record_timer(self):
        """Test recording timer values"""
        metrics = CustomMetrics()

        metrics.record_timer("operation_duration", 0.5)
        metrics.record_timer("operation_duration", 1.2)

        assert "operation_duration" in metrics.timers
        assert len(metrics.timers["operation_duration"]) == 2
        assert metrics.timers["operation_duration"][0]["duration"] == 0.5

    def test_get_all_metrics(self):
        """Test getting all metrics"""
        metrics = CustomMetrics()

        metrics.increment_counter("requests", 10)
        metrics.set_gauge("cpu", 80)
        metrics.record_histogram("latency", 50)
        metrics.record_timer("duration", 1.5)

        all_metrics = metrics.get_all_metrics()

        assert "counters" in all_metrics
        assert "gauges" in all_metrics
        assert "histograms" in all_metrics
        assert "timers" in all_metrics
        assert all_metrics["counters"]["requests"] == 10
        assert all_metrics["gauges"]["cpu"] == 80


class TestErrorTracker:
    """Test ErrorTracker functionality"""

    def test_error_tracker_initialization(self):
        """Test error tracker initialization"""
        tracker = ErrorTracker()

        assert len(tracker.errors) == 0
        assert len(tracker.error_counts) == 0
        assert len(tracker.error_patterns) == 0

    def test_record_error(self):
        """Test recording error"""
        tracker = ErrorTracker()
        error = ValueError("Test error")
        context = {"function": "test_func", "line": 42}

        tracker.record_error(error, context)

        assert len(tracker.errors) == 1
        recorded = tracker.errors[0]
        assert recorded["type"] == "ValueError"
        assert recorded["message"] == "Test error"
        assert recorded["context"] == context
        assert "timestamp" in recorded
        assert "traceback" in recorded

    def test_error_counts_tracking(self):
        """Test that error counts are properly tracked"""
        tracker = ErrorTracker()

        tracker.record_error(ValueError("Error 1"))
        tracker.record_error(RuntimeError("Error 2"))
        tracker.record_error(ValueError("Error 3"))

        assert tracker.error_counts["ValueError"] == 2
        assert tracker.error_counts["RuntimeError"] == 1

    def test_get_error_stats(self):
        """Test getting error statistics"""
        tracker = ErrorTracker()

        tracker.record_error(ValueError("Error 1"))
        tracker.record_error(RuntimeError("Error 2"))
        tracker.record_error(ValueError("Error 3"))

        stats = tracker.get_error_stats()

        assert stats["total_errors"] == 3
        assert "recent_errors" in stats
        assert "error_counts" in stats
        assert "most_frequent_errors" in stats
        assert "error_rate_per_hour" in stats
        assert stats["error_counts"]["ValueError"] == 2
        assert stats["error_counts"]["RuntimeError"] == 1


class TestAPMService:
    """Test APMService functionality"""

    @pytest.fixture
    def app(self):
        """Create test Flask application"""
        app = Flask(__name__)
        app.config["TESTING"] = True
        return app

    def test_apm_service_initialization(self):
        """Test APM service initialization"""
        service = APMService()

        assert service.app is None
        assert len(service.traces) == 0
        assert len(service.active_traces) == 0
        assert service.profiler is not None
        assert service.metrics is not None
        assert service.error_tracker is not None

    def test_apm_service_with_app(self, app):
        """Test APM service with Flask app"""
        service = APMService(app)

        assert service.app == app
        assert hasattr(app, "apm_service")
        assert app.apm_service == service

    def test_init_app(self, app):
        """Test init_app method"""
        service = APMService()
        service.init_app(app)

        assert service.app == app
        assert hasattr(app, "apm_service")

    def test_get_dashboard_data(self):
        """Test getting dashboard data"""
        service = APMService()

        # Add some test data
        service.metrics.increment_counter("requests", 100)
        service.metrics.set_gauge("cpu_usage", 75)
        service.error_tracker.record_error(Exception("Test"))

        data = service.get_dashboard_data()

        assert "traces" in data
        assert "performance" in data
        assert "metrics" in data
        assert "errors" in data
        assert "timestamp" in data

    def test_search_traces(self):
        """Test searching traces"""
        service = APMService()

        # Create test trace
        trace = TraceContext("test-trace")
        span = Span("span-1", "test-operation")
        span.set_error(ValueError("Test error"))
        trace.add_span(span)
        trace.finish()

        service.traces.append(trace)

        # Search for traces with errors
        results = service.search_traces({"has_error": True})

        assert len(results) == 1
        assert results[0]["trace_id"] == "test-trace"

    def test_get_trace_by_id(self):
        """Test getting trace by ID"""
        service = APMService()

        # Create test trace
        trace = TraceContext("test-trace-123")
        service.traces.append(trace)

        # Get trace
        result = service.get_trace_by_id("test-trace-123")

        assert result is not None
        assert result["trace_id"] == "test-trace-123"

    def test_get_trace_by_id_not_found(self):
        """Test getting non-existent trace"""
        service = APMService()

        result = service.get_trace_by_id("non-existent")

        assert result is None

    def test_matches_query_duration(self):
        """Test _matches_query for duration filtering"""
        service = APMService()

        # Create trace with known duration
        trace = TraceContext("test-trace")
        trace.start_time = time.time() - 0.5  # 0.5 seconds ago
        trace.finish()

        # Test min_duration filter
        assert service._matches_query(trace, {"min_duration": 0.1})
        assert not service._matches_query(trace, {"min_duration": 1.0})

        # Test max_duration filter
        assert service._matches_query(trace, {"max_duration": 1.0})
        assert not service._matches_query(trace, {"max_duration": 0.1})

    def test_matches_query_operation_name(self):
        """Test _matches_query for operation name filtering"""
        service = APMService()

        # Create trace with span
        trace = TraceContext("test-trace")
        span = Span("span-1", "database_query")
        trace.add_span(span)

        # Test operation name filter
        assert service._matches_query(trace, {"operation_name": "database_query"})
        assert not service._matches_query(trace, {"operation_name": "nonexistent"})

    def test_thread_safety(self):
        """Test basic thread safety"""
        service = APMService()

        def add_traces():
            for i in range(10):
                trace = TraceContext(f"trace-{i}")
                with service.lock:
                    service.traces.append(trace)

        # Create multiple threads
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=add_traces)
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Check results
        assert len(service.traces) == 30


class TestIntegrationScenarios:
    """Test integration scenarios"""

    def test_full_apm_workflow(self):
        """Test complete APM workflow without Flask context"""
        service = APMService()

        # Create trace manually (simulating request)
        trace = TraceContext("integration-trace")

        # Create spans
        root_span = Span("root-span", "HTTP GET /api/test")
        db_span = Span("db-span", "SELECT users", parent_span_id=root_span.span_id)

        # Add metadata and tags
        root_span.set_tag("http.method", "GET")
        root_span.set_tag("http.status", 200)
        db_span.set_tag("db.table", "users")

        # Add spans to trace
        trace.add_span(root_span)
        trace.add_span(db_span)

        # Finish spans
        time.sleep(0.01)
        db_span.finish()
        root_span.finish()
        trace.finish()

        # Store in service
        service.traces.append(trace)

        # Record metrics
        duration = trace.get_duration()
        service.metrics.record_timer("request.duration", duration)
        service.profiler.profile_function("GET /api/test", duration)

        # Verify results
        dashboard = service.get_dashboard_data()
        assert dashboard["traces"]["total"] == 1
        assert len(dashboard["metrics"]["timers"]) > 0
        assert len(dashboard["performance"]["function_stats"]) > 0

    def test_error_handling_workflow(self):
        """Test error handling workflow"""
        service = APMService()

        # Create trace with error
        trace = TraceContext("error-trace")
        span = Span("error-span", "failing_operation")

        # Simulate error
        error = ValueError("Something went wrong")
        span.set_error(error)
        service.error_tracker.record_error(
            error, {"trace_id": trace.trace_id, "span_id": span.span_id}
        )

        trace.add_span(span)
        span.finish()
        trace.finish()

        service.traces.append(trace)

        # Verify error tracking
        dashboard = service.get_dashboard_data()
        assert dashboard["errors"]["total_errors"] == 1
        assert "ValueError" in dashboard["errors"]["error_counts"]

        # Search for traces with errors
        error_traces = service.search_traces({"has_error": True})
        assert len(error_traces) == 1
        assert error_traces[0]["trace_id"] == "error-trace"


class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_empty_service(self):
        """Test service with no data"""
        service = APMService()

        dashboard = service.get_dashboard_data()
        assert dashboard["traces"]["total"] == 0
        assert dashboard["traces"]["active"] == 0

        # Should not crash on empty searches
        results = service.search_traces({"has_error": True})
        assert results == []

        result = service.get_trace_by_id("nonexistent")
        assert result is None

    def test_deque_maxlen_behavior(self):
        """Test that deques respect maxlen"""
        service = APMService()

        # Add more traces than maxlen (1000)
        for i in range(1500):
            trace = TraceContext(f"trace-{i}")
            service.traces.append(trace)

        # Should only keep last 1000
        assert len(service.traces) == 1000
        # First trace should be trace-500 (1500 - 1000)
        assert service.traces[0].trace_id == "trace-500"

    def test_concurrent_metrics_updates(self):
        """Test concurrent metrics updates"""
        service = APMService()

        def update_metrics():
            for i in range(100):
                service.metrics.increment_counter("test_counter")
                service.metrics.set_gauge("test_gauge", i)
                service.metrics.record_histogram("test_histogram", i * 0.1)

        # Run concurrent updates
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=update_metrics)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Verify final state
        assert (
            service.metrics.counters["test_counter"] == 500
        )  # 5 threads * 100 increments
        assert len(service.metrics.histograms["test_histogram"]) == 500


# Performance and stress tests
class TestPerformance:
    """Performance and stress tests"""

    def test_large_trace_handling(self):
        """Test handling of large traces"""
        service = APMService()

        # Create trace with many spans
        trace = TraceContext("large-trace")
        for i in range(100):
            span = Span(f"span-{i}", f"operation-{i}")
            span.set_tag("iteration", i)
            span.finish()
            trace.add_span(span)

        trace.finish()
        service.traces.append(trace)

        # Should handle conversion to dict
        trace_dict = service.get_trace_by_id("large-trace")
        assert trace_dict is not None
        assert len(trace_dict["spans"]) == 100

    def test_metrics_memory_usage(self):
        """Test metrics don't grow unbounded"""
        service = APMService()

        # Add many histogram values
        for i in range(2000):
            service.metrics.record_histogram("test_metric", i * 0.1)

        # Should be limited to 1000 values
        assert len(service.metrics.histograms["test_metric"]) == 1000

        # Should keep most recent values
        values = service.metrics.histograms["test_metric"]
        assert max(values) >= 100.0  # Should include recent high values
