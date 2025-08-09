"""
Performance Monitoring API Endpoints.

This module provides REST API endpoints for:
- Performance metrics dashboard
- Database performance monitoring
- Cache performance statistics
- System resource monitoring
- Query optimization reports
"""

import logging
from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_cors import cross_origin

from app.services.cache_service import cache_service
from app.services.database_service import db_service
from app.services.performance_monitor import performance_monitor
from app.services.query_optimizer import query_optimizer

logger = logging.getLogger(__name__)

# Create blueprint
performance_bp = Blueprint("performance", __name__, url_prefix="/api/v1/performance")


@performance_bp.route("/dashboard", methods=["GET"])
@cross_origin()
def get_performance_dashboard():
    """
    Get comprehensive performance dashboard data.

    Returns:
        JSON response with performance metrics
    """
    try:
        # Get dashboard data from performance monitor
        dashboard_data = performance_monitor.get_dashboard_data()

        # Add database metrics
        db_metrics = db_service.get_performance_metrics()
        dashboard_data["database"] = db_metrics

        # Add cache metrics
        cache_metrics = cache_service.get_performance_stats()
        dashboard_data["cache"] = cache_metrics

        return jsonify(
            {
                "success": True,
                "data": dashboard_data,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Error getting performance dashboard: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@performance_bp.route("/metrics", methods=["GET"])
@cross_origin()
def get_performance_metrics():
    """
    Get detailed performance metrics.

    Query parameters:
        - metric_type: Type of metrics to retrieve (database, cache, system)
        - timeframe: Time frame for metrics (1h, 24h, 7d, 30d)

    Returns:
        JSON response with performance metrics
    """
    try:
        metric_type = request.args.get("metric_type", "all")
        timeframe = request.args.get("timeframe", "1h")

        metrics = {}

        if metric_type in ["all", "database"]:
            metrics["database"] = db_service.get_performance_metrics()

        if metric_type in ["all", "cache"]:
            metrics["cache"] = cache_service.get_performance_stats()

        if metric_type in ["all", "system"]:
            metrics["system"] = performance_monitor.system_monitor.get_cpu_usage()
            metrics["memory"] = performance_monitor.system_monitor.get_memory_usage()
            metrics["disk"] = performance_monitor.system_monitor.get_disk_usage()

        return jsonify(
            {
                "success": True,
                "data": metrics,
                "timeframe": timeframe,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@performance_bp.route("/database/health", methods=["GET"])
@cross_origin()
def get_database_health():
    """
    Get database health check results.

    Returns:
        JSON response with database health status
    """
    try:
        health_status = db_service.health_check()

        return jsonify(
            {
                "success": True,
                "data": health_status,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Error getting database health: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@performance_bp.route("/database/pool", methods=["GET"])
@cross_origin()
def get_connection_pool_status():
    """
    Get database connection pool status.

    Returns:
        JSON response with connection pool metrics
    """
    try:
        pool_status = db_service.get_connection_pool_status()

        return jsonify(
            {
                "success": True,
                "data": pool_status,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Error getting connection pool status: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@performance_bp.route("/cache/health", methods=["GET"])
@cross_origin()
def get_cache_health():
    """
    Get cache health check results.

    Returns:
        JSON response with cache health status
    """
    try:
        health_status = cache_service.health_check()

        return jsonify(
            {
                "success": True,
                "data": health_status,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Error getting cache health: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@performance_bp.route("/cache/stats", methods=["GET"])
@cross_origin()
def get_cache_stats():
    """
    Get detailed cache statistics.

    Returns:
        JSON response with cache statistics
    """
    try:
        cache_stats = cache_service.get_performance_stats()

        return jsonify(
            {
                "success": True,
                "data": cache_stats,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@performance_bp.route("/cache/invalidate", methods=["POST"])
@cross_origin()
def invalidate_cache():
    """
    Invalidate cache entries by pattern.

    Request body:
        {
            "pattern": "pricing_data"  # Cache pattern to invalidate
        }

    Returns:
        JSON response with invalidation result
    """
    try:
        data = request.get_json()
        pattern = data.get("pattern")

        if not pattern:
            return jsonify({"success": False, "error": "Pattern is required"}), 400

        success = cache_service.invalidate_pattern(pattern)

        return jsonify(
            {
                "success": success,
                "message": (
                    f"Cache pattern {pattern} invalidated"
                    if success
                    else "Invalidation failed"
                ),
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Error invalidating cache: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@performance_bp.route("/query/analyze", methods=["POST"])
@cross_origin()
def analyze_query():
    """
    Analyze query performance and get optimization suggestions.

    Request body:
        {
            "query": "SELECT * FROM table WHERE condition",
            "params": {}  # Optional query parameters
        }

    Returns:
        JSON response with query analysis
    """
    try:
        data = request.get_json()
        query = data.get("query")
        params = data.get("params", {})

        if not query:
            return jsonify({"success": False, "error": "Query is required"}), 400

        # Analyze query
        analysis = query_optimizer.optimize_query(query, params)

        return jsonify(
            {
                "success": True,
                "data": analysis,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Error analyzing query: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@performance_bp.route("/query/profile", methods=["POST"])
@cross_origin()
def profile_query():
    """
    Profile query execution performance.

    Request body:
        {
            "query": "SELECT * FROM table WHERE condition",
            "params": {}  # Optional query parameters
        }

    Returns:
        JSON response with query profiling results
    """
    try:
        data = request.get_json()
        query = data.get("query")
        params = data.get("params", {})

        if not query:
            return jsonify({"success": False, "error": "Query is required"}), 400

        # Profile query
        profiling_result = query_optimizer.profiler.profile_query(query, params)

        return jsonify(
            {
                "success": True,
                "data": profiling_result,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Error profiling query: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@performance_bp.route("/index/recommendations", methods=["GET"])
@cross_origin()
def get_index_recommendations():
    """
    Get database index recommendations.

    Query parameters:
        - table_name: Name of table to analyze (optional)

    Returns:
        JSON response with index recommendations
    """
    try:
        table_name = request.args.get("table_name")

        if table_name:
            # Get recommendations for specific table
            report = query_optimizer.get_table_optimization_report(table_name)

            return jsonify(
                {
                    "success": True,
                    "data": report,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
        else:
            # Get recommendations for all tables
            tables = [
                "pricing_snapshots",
                "calculation_history",
                "cost_optimization_recommendations",
            ]
            recommendations = {}

            for table in tables:
                try:
                    report = query_optimizer.get_table_optimization_report(table)
                    recommendations[table] = report
                except Exception as e:
                    logger.warning(f"Error getting recommendations for {table}: {e}")
                    recommendations[table] = {"error": str(e)}

            return jsonify(
                {
                    "success": True,
                    "data": recommendations,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

    except Exception as e:
        logger.error(f"Error getting index recommendations: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@performance_bp.route("/alerts", methods=["GET"])
@cross_origin()
def get_performance_alerts():
    """
    Get current performance alerts.

    Returns:
        JSON response with active alerts
    """
    try:
        alerts = performance_monitor.alert_manager.check_alerts()

        return jsonify(
            {
                "success": True,
                "data": {
                    "alerts": alerts,
                    "alert_count": len(alerts),
                    "high_priority_count": len(
                        [a for a in alerts if a["severity"] == "high"]
                    ),
                    "medium_priority_count": len(
                        [a for a in alerts if a["severity"] == "medium"]
                    ),
                },
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Error getting performance alerts: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@performance_bp.route("/endpoints", methods=["GET"])
@cross_origin()
def get_endpoint_metrics():
    """
    Get performance metrics for individual endpoints.

    Returns:
        JSON response with endpoint performance metrics
    """
    try:
        endpoint_metrics = {}

        # Get metrics for each endpoint
        for endpoint, times in performance_monitor.metrics.endpoint_times.items():
            endpoint_metrics[endpoint] = performance_monitor.get_endpoint_metrics(
                endpoint
            )

        return jsonify(
            {
                "success": True,
                "data": endpoint_metrics,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Error getting endpoint metrics: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@performance_bp.route("/reports/performance", methods=["GET"])
@cross_origin()
def get_performance_report():
    """
    Get comprehensive performance report.

    Query parameters:
        - format: Report format (json, csv)
        - period: Report period (daily, weekly, monthly)

    Returns:
        JSON response with performance report
    """
    try:
        format_type = request.args.get("format", "json")
        period = request.args.get("period", "daily")

        # Generate comprehensive report
        report = {
            "report_period": period,
            "generated_at": datetime.utcnow().isoformat(),
            "summary": {
                "total_requests": len(performance_monitor.metrics.request_times),
                "average_response_time": (
                    performance_monitor.metrics.get_average_response_time()
                ),
                "p95_response_time": (
                    performance_monitor.metrics.get_95th_percentile_response_time()
                ),
                "error_rate": performance_monitor.metrics.get_error_rate(),
                "cache_hit_ratio": performance_monitor.metrics.get_cache_hit_ratio(),
            },
            "database_metrics": db_service.get_performance_metrics(),
            "cache_metrics": cache_service.get_performance_stats(),
            "alerts": performance_monitor.alert_manager.check_alerts(),
        }

        if format_type == "json":
            return jsonify(
                {
                    "success": True,
                    "data": report,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
        else:
            # Generate CSV format report
            import csv
            import io

            from flask import make_response

            output = io.StringIO()
            writer = csv.writer(output)

            # Write CSV headers
            writer.writerow(["Metric", "Value", "Threshold", "Status", "Timestamp"])

            # Write performance data
            system_metrics = report.get("summary", {})
            for metric, value in system_metrics.items():
                if isinstance(value, (int, float)):
                    status = (
                        "OK" if value < 80 else "WARNING" if value < 95 else "CRITICAL"
                    )
                    threshold = (
                        80
                        if metric == "cpu_usage"
                        else 85 if metric == "memory_usage" else 90
                    )
                    writer.writerow(
                        [
                            metric.replace("_", " ").title(),
                            f"{value:.2f}%",
                            f"{threshold}%",
                            status,
                            datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                        ]
                    )

            # Write database performance data
            db_metrics = report.get("database_metrics", {})
            if db_metrics:
                writer.writerow([])  # Empty row for separation
                writer.writerow(["Database Metrics", "", "", "", ""])
                for metric, value in db_metrics.items():
                    status = (
                        "OK"
                        if value < 100
                        else "WARNING" if value < 500 else "CRITICAL"
                    )
                    writer.writerow(
                        [
                            metric.replace("_", " ").title(),
                            f"{value:.2f}ms" if "time" in metric else str(value),
                            "100ms" if "time" in metric else "N/A",
                            status,
                            datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                        ]
                    )

            # Create CSV response
            output.seek(0)
            response = make_response(output.getvalue())
            response.headers["Content-Type"] = "text/csv"
            response.headers["Content-Disposition"] = (
                f"attachment; filename=performance_report_"
                f'{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.csv'
            )

            return response

    except Exception as e:
        logger.error(f"Error generating performance report: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@performance_bp.route("/config", methods=["GET"])
@cross_origin()
def get_performance_config():
    """
    Get performance monitoring configuration.

    Returns:
        JSON response with configuration settings
    """
    try:
        config = {
            "alert_thresholds": performance_monitor.alert_manager.alert_thresholds,
            "metrics_history_size": performance_monitor.metrics.max_history_size,
            "database_pool_config": db_service.get_connection_pool_status(),
            "cache_config": {
                "redis_enabled": cache_service.cache.redis_cache.redis_client
                is not None,
                "memory_cache_size": cache_service.cache.memory_cache.max_size,
                "cache_patterns": cache_service.cache_patterns,
            },
        }

        return jsonify(
            {
                "success": True,
                "data": config,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Error getting performance config: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@performance_bp.route("/config", methods=["POST"])
@cross_origin()
def update_performance_config():
    """
    Update performance monitoring configuration.

    Request body:
        {
            "alert_thresholds": {...},
            "metrics_history_size": 1000
        }

    Returns:
        JSON response with updated configuration
    """
    try:
        data = request.get_json()

        # Update alert thresholds
        if "alert_thresholds" in data:
            performance_monitor.alert_manager.alert_thresholds.update(
                data["alert_thresholds"]
            )

        # Update metrics history size
        if "metrics_history_size" in data:
            performance_monitor.metrics.max_history_size = data["metrics_history_size"]

        return jsonify(
            {
                "success": True,
                "message": "Configuration updated successfully",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Error updating performance config: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@performance_bp.route("/reset", methods=["POST"])
@cross_origin()
def reset_metrics():
    """
    Reset performance metrics (for testing/debugging).

    Returns:
        JSON response with reset confirmation
    """
    try:
        performance_monitor.reset_metrics()

        return jsonify(
            {
                "success": True,
                "message": "Performance metrics reset successfully",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Error resetting metrics: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# Error handlers
@performance_bp.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({"success": False, "error": "Endpoint not found"}), 404


@performance_bp.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({"success": False, "error": "Internal server error"}), 500


# Add CORS headers to all responses
@performance_bp.after_request
def after_request(response):
    """Add CORS headers to all responses."""
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS")
    return response
