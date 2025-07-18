"""
Gunicorn Development Configuration
Optimized for development and testing
"""
import os
from pathlib import Path

# Server socket configuration
bind = "127.0.0.1:5001"
backlog = 64

# Worker processes configuration (minimal for development)
workers = 1
worker_class = "sync"
worker_connections = 100
threads = 1

# Timeout configuration (disabled for debugging)
timeout = 0  # No timeout for debugging
graceful_timeout = 30
keepalive = 2

# Worker restart configuration
max_requests = 0  # No auto-restart
max_requests_jitter = 0
preload_app = False

# Process naming
proc_name = "cost-simulator-dev"

# Logging configuration
log_dir = Path("./logs")
log_dir.mkdir(parents=True, exist_ok=True)

accesslog = str(log_dir / "gunicorn-access.log")
errorlog = str(log_dir / "gunicorn-error.log")
loglevel = "debug"
access_log_format = (
    '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" '
    'request_time:%(D)s'
)

# Development features
reload = True
reload_extra_files = [
    "app/",
    "app/templates/",
    "app/static/",
    "app/config.py",
    "app/main.py"
]

# Security configuration (relaxed for development)
limit_request_line = 8192
limit_request_fields = 200
limit_request_field_size = 16384

# Performance tuning (disabled for development)
sendfile = False
reuse_port = False

# Development hooks
def on_starting(server):
    """Called just before the master process is initialized."""
    server.log.info("Cost Simulator (DEV) starting up...")

def when_ready(server):
    """Called just after the server is started."""
    server.log.info("Cost Simulator (DEV) is ready. Listening on: %s", server.address)
    server.log.info("Auto-reload is enabled for development")

def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    server.log.info("Cost Simulator (DEV) reloading due to code changes...")

def on_exit(server):
    """Called just before exiting."""
    server.log.info("Cost Simulator (DEV) shutting down...")

def worker_int(worker):
    """Called when a worker receives the INT or QUIT signal."""
    worker.log.info("Worker %s received INT/QUIT signal", worker.pid)

def pre_request(worker, req):
    """Called before each request."""
    worker.log.debug("Processing request: %s %s", req.method, req.path)

def post_request(worker, req, environ, resp):
    """Called after each request."""
    worker.log.debug("Request completed: %s %s - Status: %s", 
                     req.method, req.path, resp.status_code)