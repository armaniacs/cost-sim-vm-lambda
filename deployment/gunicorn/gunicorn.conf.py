"""
Gunicorn Production Configuration
Enterprise-grade WSGI server configuration for AWS Lambda vs VM Cost Simulator
"""
import multiprocessing
import os
from pathlib import Path

# Server socket configuration
bind = os.getenv("GUNICORN_BIND", "0.0.0.0:5001")
backlog = int(os.getenv("GUNICORN_BACKLOG", "2048"))

# Worker processes configuration
workers = int(os.getenv("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))
worker_class = os.getenv("GUNICORN_WORKER_CLASS", "sync")
worker_connections = int(os.getenv("GUNICORN_WORKER_CONNECTIONS", "1000"))
threads = int(os.getenv("GUNICORN_THREADS", "2"))

# Timeout configuration
timeout = int(os.getenv("GUNICORN_TIMEOUT", "30"))
graceful_timeout = int(os.getenv("GUNICORN_GRACEFUL_TIMEOUT", "30"))
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", "2"))

# Worker restart configuration
max_requests = int(os.getenv("GUNICORN_MAX_REQUESTS", "1000"))
max_requests_jitter = int(os.getenv("GUNICORN_MAX_REQUESTS_JITTER", "50"))
preload_app = os.getenv("GUNICORN_PRELOAD_APP", "true").lower() == "true"

# Process naming
proc_name = "cost-simulator"

# User/Group (for security)
user = os.getenv("GUNICORN_USER", "appuser")
group = os.getenv("GUNICORN_GROUP", "appuser")

# Logging configuration
log_dir = Path(os.getenv("LOG_DIR", "/var/log/gunicorn"))
log_dir.mkdir(parents=True, exist_ok=True)

accesslog = str(log_dir / "access.log")
errorlog = str(log_dir / "error.log")
loglevel = os.getenv("GUNICORN_LOG_LEVEL", "info")
access_log_format = (
    '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" '
    'request_time:%(D)s response_length:%(B)s'
)

# Security configuration
limit_request_line = int(os.getenv("GUNICORN_LIMIT_REQUEST_LINE", "4096"))
limit_request_fields = int(os.getenv("GUNICORN_LIMIT_REQUEST_FIELDS", "100"))
limit_request_field_size = int(os.getenv("GUNICORN_LIMIT_REQUEST_FIELD_SIZE", "8190"))

# SSL configuration (if enabled)
keyfile = os.getenv("GUNICORN_SSL_KEYFILE")
certfile = os.getenv("GUNICORN_SSL_CERTFILE")
ca_certs = os.getenv("GUNICORN_SSL_CA_CERTS")
ssl_version = 2  # TLS 1.2+
ciphers = "ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS"
do_handshake_on_connect = True

# Performance tuning
sendfile = True
reuse_port = True

# Monitoring hooks
def on_starting(server):
    """Called just before the master process is initialized."""
    server.log.info("Cost Simulator starting up...")

def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    server.log.info("Cost Simulator reloading...")

def when_ready(server):
    """Called just after the server is started."""
    server.log.info("Cost Simulator is ready. Listening on: %s", server.address)

def on_exit(server):
    """Called just before exiting."""
    server.log.info("Cost Simulator shutting down...")

def worker_int(worker):
    """Called when a worker receives the INT or QUIT signal."""
    worker.log.info("Worker %s received INT/QUIT signal", worker.pid)

def pre_fork(server, worker):
    """Called just before a worker is forked."""
    server.log.info("Worker %s spawned", worker.pid)

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.info("Worker %s ready", worker.pid)

def worker_abort(worker):
    """Called when a worker receives the SIGABRT signal."""
    worker.log.error("Worker %s aborted", worker.pid)

# Health check configuration
def healthcheck():
    """Custom health check function."""
    try:
        import requests
        response = requests.get("http://localhost:5001/health", timeout=5)
        return response.status_code == 200
    except Exception:
        return False

# Environment-specific configurations
if os.getenv("FLASK_ENV") == "production":
    # Production optimizations
    workers = max(2, multiprocessing.cpu_count())
    worker_class = "gevent"
    worker_connections = 1000
    timeout = 120
    keepalive = 5
    max_requests = 10000
    max_requests_jitter = 1000
    preload_app = True
    
elif os.getenv("FLASK_ENV") == "development":
    # Development settings
    workers = 1
    worker_class = "sync"
    timeout = 0  # No timeout for debugging
    reload = True
    reload_extra_files = [
        "app/templates/",
        "app/static/",
        "app/config.py"
    ]
    
# Memory monitoring
def pre_request(worker, req):
    """Called before each request."""
    worker.log.debug("Processing request: %s %s", req.method, req.path)

def post_request(worker, req, environ, resp):
    """Called after each request."""
    worker.log.debug("Request completed: %s %s - Status: %s", 
                     req.method, req.path, resp.status_code)

# Custom configuration validation
def validate_config():
    """Validate configuration settings."""
    errors = []
    
    if workers < 1:
        errors.append("workers must be at least 1")
    
    if timeout < 0:
        errors.append("timeout must be non-negative")
    
    if max_requests < 0:
        errors.append("max_requests must be non-negative")
    
    if errors:
        raise ValueError("Configuration errors: " + ", ".join(errors))

# Run validation
validate_config()