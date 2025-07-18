#!/bin/bash
"""
Gunicorn Production Startup Script
Enterprise-grade WSGI server startup with comprehensive health checks
"""

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
APP_MODULE="app.main:create_app('production')"
GUNICORN_CONFIG="$SCRIPT_DIR/gunicorn.conf.py"
PID_FILE="${PID_FILE:-/var/run/gunicorn/cost-simulator.pid}"
LOG_DIR="${LOG_DIR:-/var/log/gunicorn}"

# Environment variables
export FLASK_ENV="${FLASK_ENV:-production}"
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1" >&2
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" >&2
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

# Check if running as root
check_user() {
    if [[ $EUID -eq 0 ]]; then
        log_warn "Running as root. Consider using a dedicated user for security."
    fi
}

# Create necessary directories
setup_directories() {
    log_info "Setting up directories..."
    
    # Create log directory
    mkdir -p "$LOG_DIR"
    
    # Create PID directory
    mkdir -p "$(dirname "$PID_FILE")"
    
    # Set permissions
    if [[ -n "${GUNICORN_USER:-}" ]]; then
        chown -R "${GUNICORN_USER}:${GUNICORN_GROUP:-$GUNICORN_USER}" "$LOG_DIR"
        chown -R "${GUNICORN_USER}:${GUNICORN_GROUP:-$GUNICORN_USER}" "$(dirname "$PID_FILE")"
    fi
}

# Pre-flight checks
preflight_checks() {
    log_info "Running pre-flight checks..."
    
    # Check if Python is available
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed or not in PATH"
        exit 1
    fi
    
    # Check if gunicorn is available
    if ! command -v gunicorn &> /dev/null; then
        log_error "Gunicorn is not installed or not in PATH"
        exit 1
    fi
    
    # Check if configuration file exists
    if [[ ! -f "$GUNICORN_CONFIG" ]]; then
        log_error "Gunicorn configuration file not found: $GUNICORN_CONFIG"
        exit 1
    fi
    
    # Check if application module can be imported
    cd "$PROJECT_ROOT"
    if ! python3 -c "from $APP_MODULE; print('Application module imported successfully')" &> /dev/null; then
        log_error "Failed to import application module: $APP_MODULE"
        exit 1
    fi
    
    # Check if required environment variables are set
    required_vars=("FLASK_ENV")
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            log_error "Required environment variable $var is not set"
            exit 1
        fi
    done
    
    log_info "Pre-flight checks passed"
}

# Health check function
health_check() {
    local max_attempts=30
    local attempt=1
    
    log_info "Performing health check..."
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -s -f "http://localhost:5001/health" > /dev/null 2>&1; then
            log_info "Health check passed"
            return 0
        fi
        
        log_warn "Health check attempt $attempt/$max_attempts failed, retrying in 2s..."
        sleep 2
        ((attempt++))
    done
    
    log_error "Health check failed after $max_attempts attempts"
    return 1
}

# Start Gunicorn
start_gunicorn() {
    log_info "Starting Gunicorn with configuration: $GUNICORN_CONFIG"
    
    cd "$PROJECT_ROOT"
    
    # Start Gunicorn with configuration
    exec gunicorn \
        --config "$GUNICORN_CONFIG" \
        --pid "$PID_FILE" \
        --daemon \
        "$APP_MODULE"
}

# Stop Gunicorn
stop_gunicorn() {
    if [[ -f "$PID_FILE" ]]; then
        local pid=$(cat "$PID_FILE")
        log_info "Stopping Gunicorn (PID: $pid)..."
        
        if kill -0 "$pid" 2>/dev/null; then
            kill -TERM "$pid"
            
            # Wait for graceful shutdown
            local timeout=30
            local count=0
            while kill -0 "$pid" 2>/dev/null && [[ $count -lt $timeout ]]; do
                sleep 1
                ((count++))
            done
            
            # Force kill if still running
            if kill -0 "$pid" 2>/dev/null; then
                log_warn "Graceful shutdown timed out, forcing kill..."
                kill -KILL "$pid"
            fi
            
            rm -f "$PID_FILE"
            log_info "Gunicorn stopped"
        else
            log_warn "PID file exists but process is not running"
            rm -f "$PID_FILE"
        fi
    else
        log_warn "PID file not found"
    fi
}

# Restart Gunicorn
restart_gunicorn() {
    log_info "Restarting Gunicorn..."
    stop_gunicorn
    sleep 2
    start_gunicorn
}

# Reload Gunicorn
reload_gunicorn() {
    if [[ -f "$PID_FILE" ]]; then
        local pid=$(cat "$PID_FILE")
        log_info "Reloading Gunicorn (PID: $pid)..."
        
        if kill -0 "$pid" 2>/dev/null; then
            kill -HUP "$pid"
            log_info "Gunicorn reloaded"
        else
            log_error "Gunicorn is not running"
            exit 1
        fi
    else
        log_error "PID file not found"
        exit 1
    fi
}

# Status check
status_gunicorn() {
    if [[ -f "$PID_FILE" ]]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            log_info "Gunicorn is running (PID: $pid)"
            return 0
        else
            log_warn "PID file exists but process is not running"
            return 1
        fi
    else
        log_warn "Gunicorn is not running"
        return 1
    fi
}

# Main function
main() {
    local command="${1:-start}"
    
    case "$command" in
        start)
            check_user
            setup_directories
            preflight_checks
            start_gunicorn
            sleep 5
            health_check
            ;;
        stop)
            stop_gunicorn
            ;;
        restart)
            restart_gunicorn
            sleep 5
            health_check
            ;;
        reload)
            reload_gunicorn
            ;;
        status)
            status_gunicorn
            ;;
        health)
            health_check
            ;;
        *)
            echo "Usage: $0 {start|stop|restart|reload|status|health}"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"