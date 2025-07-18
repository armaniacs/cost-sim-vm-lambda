"""
Structured Logging Service for Enterprise Cost Management Platform.

This service provides:
- Structured JSON logging with consistent format
- Log centralization and aggregation
- Log parsing and analysis capabilities
- Log retention policies
- Correlation with APM traces
- Log level management
- Custom log formatters
"""

import json
import logging
import logging.handlers
import os
import sys
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
import threading
import gzip
import glob

from flask import Flask, g, request, current_app, has_request_context

from app.extensions import get_redis_client

# Custom log levels
AUDIT_LEVEL = 25
SECURITY_LEVEL = 35
PERFORMANCE_LEVEL = 15

logging.addLevelName(AUDIT_LEVEL, "AUDIT")
logging.addLevelName(SECURITY_LEVEL, "SECURITY")
logging.addLevelName(PERFORMANCE_LEVEL, "PERFORMANCE")


class StructuredFormatter(logging.Formatter):
    """Custom formatter that outputs structured JSON logs."""
    
    def __init__(self, include_trace_info: bool = True):
        super().__init__()
        self.include_trace_info = include_trace_info
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        # Base log structure
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'thread': record.thread,
            'process': record.process
        }
        
        # Add trace information if available
        if self.include_trace_info and has_request_context():
            try:
                if hasattr(g, 'trace_context'):
                    log_entry['trace_id'] = g.trace_context.trace_id
                
                if hasattr(g, 'current_span'):
                    log_entry['span_id'] = g.current_span.span_id
                
                # Add request context
                log_entry['request'] = {
                    'method': request.method,
                    'path': request.path,
                    'endpoint': request.endpoint,
                    'remote_addr': request.remote_addr,
                    'user_agent': request.headers.get('User-Agent', '')
                }
            except Exception:
                # Ignore errors when request context is not available
                pass
        
        # Add exception information
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': self.formatException(record.exc_info)
            }
        
        # Add custom fields from extra
        if hasattr(record, '__dict__'):
            for key, value in record.__dict__.items():
                if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                              'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                              'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                              'thread', 'threadName', 'processName', 'process', 'message']:
                    log_entry['extra'] = log_entry.get('extra', {})
                    log_entry['extra'][key] = value
        
        return json.dumps(log_entry, default=str)


class LogAggregator:
    """Aggregates and manages log entries."""
    
    def __init__(self, max_entries: int = 10000):
        self.max_entries = max_entries
        self.logs = deque(maxlen=max_entries)
        self.log_counts = defaultdict(int)
        self.error_patterns = defaultdict(list)
        self.lock = threading.Lock()
    
    def add_log(self, log_entry: Dict[str, Any]):
        """Add a log entry to the aggregator."""
        with self.lock:
            self.logs.append(log_entry)
            self.log_counts[log_entry['level']] += 1
            
            # Track error patterns
            if log_entry['level'] in ['ERROR', 'CRITICAL']:
                pattern = f"{log_entry['module']}.{log_entry['function']}"
                self.error_patterns[pattern].append(log_entry['timestamp'])
    
    def get_recent_logs(self, limit: int = 100, level: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get recent log entries."""
        with self.lock:
            logs = list(self.logs)
            
            if level:
                logs = [log for log in logs if log['level'] == level]
            
            return logs[-limit:]
    
    def search_logs(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search logs based on criteria."""
        results = []
        
        with self.lock:
            for log in self.logs:
                if self._matches_query(log, query):
                    results.append(log)
        
        return results
    
    def _matches_query(self, log: Dict[str, Any], query: Dict[str, Any]) -> bool:
        """Check if log matches search query."""
        if 'level' in query and log['level'] != query['level']:
            return False
        
        if 'logger' in query and query['logger'] not in log['logger']:
            return False
        
        if 'message' in query and query['message'].lower() not in log['message'].lower():
            return False
        
        if 'trace_id' in query and log.get('trace_id') != query['trace_id']:
            return False
        
        if 'start_time' in query:
            log_time = datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00'))
            start_time = datetime.fromisoformat(query['start_time'])
            if log_time < start_time:
                return False
        
        if 'end_time' in query:
            log_time = datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(query['end_time'])
            if log_time > end_time:
                return False
        
        return True
    
    def get_log_stats(self) -> Dict[str, Any]:
        """Get log statistics."""
        with self.lock:
            recent_logs = [
                log for log in self.logs
                if datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00')) > 
                datetime.utcnow() - timedelta(hours=1)
            ]
            
            return {
                'total_logs': len(self.logs),
                'recent_logs': len(recent_logs),
                'log_counts': dict(self.log_counts),
                'error_patterns': dict(self.error_patterns),
                'logs_per_minute': len([
                    log for log in self.logs
                    if datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00')) > 
                    datetime.utcnow() - timedelta(minutes=1)
                ])
            }


class LogRetentionManager:
    """Manages log retention policies."""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.retention_policies = {
            'debug': timedelta(days=1),
            'info': timedelta(days=7),
            'warning': timedelta(days=30),
            'error': timedelta(days=90),
            'critical': timedelta(days=365)
        }
    
    def cleanup_old_logs(self):
        """Remove old log files based on retention policies."""
        for level, retention_period in self.retention_policies.items():
            cutoff_time = datetime.utcnow() - retention_period
            
            # Find log files for this level
            pattern = self.log_dir / f"*{level}*.log*"
            for log_file in glob.glob(str(pattern)):
                file_path = Path(log_file)
                file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                
                if file_time < cutoff_time:
                    try:
                        file_path.unlink()
                        logging.info(f"Removed old log file: {log_file}")
                    except Exception as e:
                        logging.error(f"Failed to remove log file {log_file}: {e}")
    
    def compress_old_logs(self, days_old: int = 7):
        """Compress old log files to save space."""
        cutoff_time = datetime.utcnow() - timedelta(days=days_old)
        
        for log_file in self.log_dir.glob("*.log"):
            file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
            
            if file_time < cutoff_time and not log_file.name.endswith('.gz'):
                try:
                    with open(log_file, 'rb') as f_in:
                        with gzip.open(f"{log_file}.gz", 'wb') as f_out:
                            f_out.writelines(f_in)
                    
                    log_file.unlink()
                    logging.info(f"Compressed log file: {log_file}")
                except Exception as e:
                    logging.error(f"Failed to compress log file {log_file}: {e}")


class LogAnalyzer:
    """Analyzes log patterns and generates insights."""
    
    def __init__(self, aggregator: LogAggregator):
        self.aggregator = aggregator
    
    def analyze_error_patterns(self) -> Dict[str, Any]:
        """Analyze error patterns and frequency."""
        with self.aggregator.lock:
            error_logs = [
                log for log in self.aggregator.logs
                if log['level'] in ['ERROR', 'CRITICAL']
            ]
        
        if not error_logs:
            return {'total_errors': 0, 'patterns': []}
        
        # Group errors by pattern
        patterns = defaultdict(list)
        for log in error_logs:
            pattern = f"{log['logger']}: {log['message']}"
            patterns[pattern].append(log['timestamp'])
        
        # Sort by frequency
        sorted_patterns = sorted(
            patterns.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )
        
        return {
            'total_errors': len(error_logs),
            'patterns': [
                {
                    'pattern': pattern,
                    'count': len(timestamps),
                    'first_seen': min(timestamps),
                    'last_seen': max(timestamps)
                }
                for pattern, timestamps in sorted_patterns[:10]
            ]
        }
    
    def analyze_performance_logs(self) -> Dict[str, Any]:
        """Analyze performance-related logs."""
        with self.aggregator.lock:
            perf_logs = [
                log for log in self.aggregator.logs
                if log['level'] == 'PERFORMANCE'
            ]
        
        if not perf_logs:
            return {'total_performance_logs': 0, 'insights': []}
        
        insights = []
        
        # Analyze slow operations
        slow_operations = [log for log in perf_logs if 'slow' in log['message'].lower()]
        if slow_operations:
            insights.append({
                'type': 'slow_operations',
                'count': len(slow_operations),
                'recent': slow_operations[-5:]
            })
        
        return {
            'total_performance_logs': len(perf_logs),
            'insights': insights
        }


class EnhancedLogHandler(logging.Handler):
    """Enhanced log handler that integrates with log aggregator."""
    
    def __init__(self, aggregator: LogAggregator):
        super().__init__()
        self.aggregator = aggregator
        self.setFormatter(StructuredFormatter())
    
    def emit(self, record: logging.LogRecord):
        """Process log record and add to aggregator."""
        try:
            # Format the record
            formatted_msg = self.format(record)
            log_entry = json.loads(formatted_msg)
            
            # Add to aggregator
            self.aggregator.add_log(log_entry)
            
            # Store in Redis for centralized logging
            self._store_in_redis(log_entry)
            
        except Exception as e:
            # Fallback to avoid infinite recursion
            print(f"Error in log handler: {e}", file=sys.stderr)
    
    def _store_in_redis(self, log_entry: Dict[str, Any]):
        """Store log entry in Redis for centralized access."""
        try:
            redis_client = get_redis_client()
            if redis_client:
                # Store in a time-series key
                key = f"logs:{datetime.utcnow().strftime('%Y-%m-%d:%H')}"
                redis_client.lpush(key, json.dumps(log_entry))
                redis_client.expire(key, 86400)  # 24 hours
        except Exception:
            # Ignore Redis errors to avoid affecting application
            pass


class LoggingService:
    """Main logging service that orchestrates all logging components."""
    
    def __init__(self, app: Flask = None):
        self.app = app
        self.aggregator = LogAggregator()
        self.retention_manager = LogRetentionManager()
        self.analyzer = LogAnalyzer(self.aggregator)
        self.enhanced_handler = EnhancedLogHandler(self.aggregator)
        
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize logging service with Flask app."""
        self.app = app
        
        # Configure logging
        self._configure_logging()
        
        # Schedule cleanup tasks
        self._schedule_cleanup_tasks()
        
        # Store reference in app
        app.logging_service = self
    
    def _configure_logging(self):
        """Configure application logging."""
        # Create logs directory
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Root logger configuration
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        
        # Remove default handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Add enhanced handler
        root_logger.addHandler(self.enhanced_handler)
        
        # File handlers for different log levels
        self._add_file_handlers(root_logger, log_dir)
        
        # Console handler for development
        if self.app.config.get('DEBUG', False):
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(StructuredFormatter())
            console_handler.setLevel(logging.INFO)
            root_logger.addHandler(console_handler)
        
        # Flask app logger
        self.app.logger.setLevel(logging.INFO)
        self.app.logger.propagate = True
        
        # Custom loggers
        self._create_custom_loggers()
    
    def _add_file_handlers(self, logger: logging.Logger, log_dir: Path):
        """Add file handlers for different log levels."""
        handlers = [
            ('debug', logging.DEBUG),
            ('info', logging.INFO),
            ('warning', logging.WARNING),
            ('error', logging.ERROR),
            ('critical', logging.CRITICAL)
        ]
        
        for level_name, level in handlers:
            file_path = log_dir / f"{level_name}.log"
            
            # Rotating file handler
            handler = logging.handlers.RotatingFileHandler(
                file_path,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
            handler.setLevel(level)
            handler.setFormatter(StructuredFormatter())
            
            # Add filter to only log specific level
            handler.addFilter(lambda record, target_level=level: record.levelno >= target_level)
            
            logger.addHandler(handler)
    
    def _create_custom_loggers(self):
        """Create custom loggers for specific purposes."""
        # Audit logger
        audit_logger = logging.getLogger('audit')
        audit_logger.setLevel(AUDIT_LEVEL)
        
        # Security logger
        security_logger = logging.getLogger('security')
        security_logger.setLevel(SECURITY_LEVEL)
        
        # Performance logger
        performance_logger = logging.getLogger('performance')
        performance_logger.setLevel(PERFORMANCE_LEVEL)
        
        # API logger
        api_logger = logging.getLogger('api')
        api_logger.setLevel(logging.INFO)
    
    def _schedule_cleanup_tasks(self):
        """Schedule periodic cleanup tasks."""
        import threading
        import time
        
        def cleanup_worker():
            while True:
                try:
                    # Run cleanup every hour
                    time.sleep(3600)
                    self.retention_manager.cleanup_old_logs()
                    self.retention_manager.compress_old_logs()
                except Exception as e:
                    logging.error(f"Error in log cleanup: {e}")
        
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get logging dashboard data."""
        return {
            'stats': self.aggregator.get_log_stats(),
            'error_analysis': self.analyzer.analyze_error_patterns(),
            'performance_analysis': self.analyzer.analyze_performance_logs(),
            'recent_logs': self.aggregator.get_recent_logs(50),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def search_logs(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search logs based on criteria."""
        return self.aggregator.search_logs(query)
    
    def get_logs_by_trace(self, trace_id: str) -> List[Dict[str, Any]]:
        """Get all logs for a specific trace."""
        return self.aggregator.search_logs({'trace_id': trace_id})
    
    def log_audit_event(self, event: str, details: Dict[str, Any], user_id: str = None):
        """Log an audit event."""
        audit_logger = logging.getLogger('audit')
        audit_logger.log(AUDIT_LEVEL, event, extra={
            'event_type': 'audit',
            'details': details,
            'user_id': user_id
        })
    
    def log_security_event(self, event: str, details: Dict[str, Any], severity: str = 'medium'):
        """Log a security event."""
        security_logger = logging.getLogger('security')
        security_logger.log(SECURITY_LEVEL, event, extra={
            'event_type': 'security',
            'details': details,
            'severity': severity
        })
    
    def log_performance_event(self, event: str, metrics: Dict[str, Any]):
        """Log a performance event."""
        performance_logger = logging.getLogger('performance')
        performance_logger.log(PERFORMANCE_LEVEL, event, extra={
            'event_type': 'performance',
            'metrics': metrics
        })


# Logging decorators
def log_function_call(logger_name: str = None, level: int = logging.INFO):
    """Decorator to log function calls."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(logger_name or func.__module__)
            
            logger.log(level, f"Calling {func.__name__}", extra={
                'function': func.__name__,
                'args_count': len(args),
                'kwargs_count': len(kwargs)
            })
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                logger.log(level, f"Completed {func.__name__}", extra={
                    'function': func.__name__,
                    'duration': duration,
                    'success': True
                })
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                
                logger.error(f"Error in {func.__name__}: {e}", extra={
                    'function': func.__name__,
                    'duration': duration,
                    'success': False,
                    'error': str(e)
                })
                raise
        
        return wrapper
    return decorator


def log_api_call(include_request_data: bool = False, include_response_data: bool = False):
    """Decorator to log API calls."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = logging.getLogger('api')
            
            extra_data = {
                'endpoint': func.__name__,
                'method': request.method if has_request_context() else 'unknown'
            }
            
            if include_request_data and has_request_context():
                extra_data['request_data'] = {
                    'path': request.path,
                    'query_params': dict(request.args),
                    'headers': dict(request.headers)
                }
            
            logger.info(f"API call: {func.__name__}", extra=extra_data)
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                response_extra = {
                    'endpoint': func.__name__,
                    'duration': duration,
                    'success': True
                }
                
                if include_response_data:
                    response_extra['response_data'] = result
                
                logger.info(f"API response: {func.__name__}", extra=response_extra)
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                
                logger.error(f"API error: {func.__name__}", extra={
                    'endpoint': func.__name__,
                    'duration': duration,
                    'success': False,
                    'error': str(e)
                })
                raise
        
        return wrapper
    return decorator


# Global logging service instance
logging_service = LoggingService()