# Deployment & Production Guide

## Overview

This guide covers deployment strategies, production configurations, and operational considerations for the AWS Lambda vs VM Cost Simulator.

## Production Architecture

### Application Stack

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │    │   Web Server    │    │   Application   │
│   (nginx/ALB)   │◄──►│   (nginx/WSG)   │◄──►│   (Flask App)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Static Files  │    │   Log Storage   │
                       │   (CDN/S3)      │    │   (Files/Cloud) │
                       └─────────────────┘    └─────────────────┘
```

### Container Architecture

**Multi-stage Docker Build**:
```dockerfile
# Build stage
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Production stage  
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY app/ ./app/
COPY *.py ./

ENV PATH=/root/.local/bin:$PATH
ENV FLASK_ENV=production
EXPOSE 5001

CMD ["python", "main.py"]
```

## Deployment Options

### 1. Docker Deployment (Recommended)

#### Quick Docker Deployment

```bash
# Build and run with make commands
make docker-build    # Build production image
make docker-run      # Run container with production config
make docker-stop     # Stop running container
```

#### Manual Docker Commands

```bash
# Build production image
docker build -t cost-simulator:latest .

# Run with production configuration
docker run -d \
  --name cost-simulator \
  -p 80:5001 \
  -e FLASK_ENV=production \
  -e HOST=0.0.0.0 \
  -e PORT=5001 \
  --restart unless-stopped \
  cost-simulator:latest

# Check container status
docker logs cost-simulator
docker ps
```

#### Docker Compose Deployment

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "80:5001"
    environment:
      - FLASK_ENV=production
      - HOST=0.0.0.0
      - PORT=5001
    restart: unless-stopped
    volumes:
      - ./logs:/app/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5001/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app
    restart: unless-stopped
```

### 2. Cloud Platform Deployments

#### AWS Deployment

**ECS Fargate Deployment**:
```json
{
  "family": "cost-simulator",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "cost-simulator",
      "image": "your-account.dkr.ecr.region.amazonaws.com/cost-simulator:latest",
      "portMappings": [
        {
          "containerPort": 5001,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "FLASK_ENV",
          "value": "production"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/cost-simulator",
          "awslogs-region": "ap-northeast-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

**Application Load Balancer Configuration**:
- Health check: `/health`
- Port: 80 → 5001
- Target group: ECS service
- SSL termination at ALB

#### Google Cloud Run Deployment

```yaml
# cloudrun.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: cost-simulator
  annotations:
    run.googleapis.com/ingress: all
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/maxScale: "10"
        run.googleapis.com/cpu-throttling: "false"
    spec:
      containerConcurrency: 100
      containers:
      - image: gcr.io/project/cost-simulator:latest
        ports:
        - containerPort: 5001
        env:
        - name: FLASK_ENV
          value: production
        - name: PORT
          value: "5001"
        resources:
          limits:
            cpu: "1"
            memory: "512Mi"
```

Deploy command:
```bash
gcloud run deploy cost-simulator \
  --image gcr.io/project/cost-simulator:latest \
  --platform managed \
  --region asia-northeast1 \
  --allow-unauthenticated \
  --port 5001
```

#### Azure Container Instances

```bash
az container create \
  --resource-group cost-simulator-rg \
  --name cost-simulator \
  --image your-registry.azurecr.io/cost-simulator:latest \
  --ports 5001 \
  --environment-variables FLASK_ENV=production \
  --cpu 1 \
  --memory 1 \
  --restart-policy Always
```

### 3. Traditional Server Deployment

#### systemd Service Configuration

```ini
# /etc/systemd/system/cost-simulator.service
[Unit]
Description=Cost Simulator Flask Application
After=network.target

[Service]
User=appuser
Group=appuser
WorkingDirectory=/opt/cost-simulator
Environment=FLASK_ENV=production
Environment=HOST=127.0.0.1
Environment=PORT=5001
ExecStart=/opt/cost-simulator/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start service:
```bash
sudo systemctl enable cost-simulator
sudo systemctl start cost-simulator
sudo systemctl status cost-simulator
```

#### nginx Reverse Proxy

```nginx
# /etc/nginx/sites-available/cost-simulator
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /opt/cost-simulator/app/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}

# SSL configuration
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/ssl/certs/your-domain.crt;
    ssl_certificate_key /etc/ssl/private/your-domain.key;
    
    # SSL best practices
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    
    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Production Configuration

### Environment Variables

```bash
# Production environment configuration
export FLASK_ENV=production
export HOST=0.0.0.0
export PORT=5001
export DEBUG=False

# Security settings
export SECRET_KEY=your-secret-key-here
export SECURE_HEADERS=True

# Performance settings
export WORKERS=4
export THREADS=2
export TIMEOUT=30

# Logging settings
export LOG_LEVEL=INFO
export LOG_FILE=/var/log/cost-simulator/app.log
```

### Configuration File (`config.py`)

```python
import os

class ProductionConfig:
    """Production configuration"""
    DEBUG = False
    TESTING = False
    
    # Server configuration
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5001))
    
    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY', 'production-secret-key')
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    
    # Performance
    JSON_SORT_KEYS = False
    JSONIFY_PRETTYPRINT_REGULAR = False
    
    # CORS settings
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '').split(',')
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', '/var/log/app.log')
```

### Security Hardening

#### Application Security

```python
# Security headers middleware
from flask import Flask
from flask_talisman import Talisman

def create_app():
    app = Flask(__name__)
    
    # Security headers
    Talisman(app, {
        'force_https': True,
        'force_https_permanent': True,
        'content_security_policy': {
            'default-src': "'self'",
            'script-src': "'self' 'unsafe-inline' cdn.jsdelivr.net",
            'style-src': "'self' 'unsafe-inline' cdn.jsdelivr.net",
            'img-src': "'self' data:",
        },
        'referrer_policy': 'strict-origin-when-cross-origin',
        'feature_policy': {
            'geolocation': "'none'",
            'camera': "'none'",
            'microphone': "'none'",
        }
    })
    
    return app
```

#### Input Validation

```python
from marshmallow import Schema, fields, validate

class LambdaConfigSchema(Schema):
    memory_mb = fields.Integer(
        required=True,
        validate=validate.OneOf([128, 512, 1024, 2048])
    )
    execution_time_seconds = fields.Integer(
        required=True,
        validate=validate.Range(min=1, max=60)
    )
    monthly_executions = fields.Integer(
        required=True,
        validate=validate.Range(min=0, max=1000000000)
    )
```

## Monitoring & Observability

### Health Checks

```python
@app.route('/health')
def health_check():
    """Comprehensive health check endpoint"""
    try:
        # Test critical components
        lambda_calc = LambdaCalculator()
        vm_calc = VMCalculator()
        
        # Basic calculation test
        test_result = lambda_calc.calculate_cost(test_config)
        
        return {
            'status': 'healthy',
            'version': '1.0.0',
            'timestamp': datetime.utcnow().isoformat(),
            'components': {
                'lambda_calculator': 'ok',
                'vm_calculator': 'ok',
                'egress_calculator': 'ok'
            }
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }, 503
```

### Logging Configuration

```python
import logging
import logging.handlers

def setup_logging(app):
    """Configure production logging"""
    if not app.debug:
        # File handler for application logs
        file_handler = logging.handlers.RotatingFileHandler(
            'logs/cost-simulator.log',
            maxBytes=10485760,  # 10MB
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        # Console handler for critical errors
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.ERROR)
        app.logger.addHandler(console_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('Cost Simulator startup')
```

### Metrics Collection

```python
import time
from functools import wraps

def track_performance(f):
    """Decorator to track API performance"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = f(*args, **kwargs)
            duration = time.time() - start_time
            
            # Log performance metrics
            app.logger.info(f"API {f.__name__} completed in {duration:.3f}s")
            
            # Could send to monitoring system
            # metrics.histogram('api.duration', duration, tags=[f'endpoint:{f.__name__}'])
            
            return result
        except Exception as e:
            duration = time.time() - start_time
            app.logger.error(f"API {f.__name__} failed after {duration:.3f}s: {e}")
            raise
    return wrapper
```

## Performance Optimization

### Production WSGI Server

**Gunicorn Configuration** (`gunicorn.conf.py`):
```python
# Server socket
bind = "0.0.0.0:5001"
backlog = 2048

# Worker processes
workers = 4
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers
max_requests = 1000
max_requests_jitter = 50
preload_app = True

# Logging
accesslog = "/var/log/gunicorn/access.log"
errorlog = "/var/log/gunicorn/error.log"
loglevel = "info"

# Process naming
proc_name = "cost-simulator"

# Security
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190
```

Run with Gunicorn:
```bash
gunicorn --config gunicorn.conf.py "app.main:create_app('production')"
```

### Caching Strategy

```python
from flask_caching import Cache

# Configure caching
cache = Cache(app, config={
    'CACHE_TYPE': 'simple',  # Use Redis for production
    'CACHE_DEFAULT_TIMEOUT': 300
})

@app.route('/api/v1/calculator/lambda')
@cache.cached(timeout=60, query_string=True)
def calculate_lambda():
    """Cache identical requests for 1 minute"""
    return calculation_result
```

### Static File Optimization

```nginx
# nginx static file caching
location /static/ {
    alias /opt/cost-simulator/app/static/;
    expires 1y;
    add_header Cache-Control "public, immutable";
    add_header Vary Accept-Encoding;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_types
        text/css
        text/javascript
        text/xml
        text/plain
        application/javascript
        application/xml+rss
        application/json;
}
```

## Backup & Recovery

### Data Backup (Future - when database is added)

```bash
#!/bin/bash
# backup-script.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/cost-simulator"
DB_FILE="/app/data/calculations.db"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
cp $DB_FILE $BACKUP_DIR/calculations_$DATE.db

# Compress and clean old backups
gzip $BACKUP_DIR/calculations_$DATE.db
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete

echo "Backup completed: calculations_$DATE.db.gz"
```

### Configuration Backup

```bash
# Backup critical configuration files
tar -czf /backups/config_$(date +%Y%m%d).tar.gz \
  /etc/nginx/sites-available/cost-simulator \
  /etc/systemd/system/cost-simulator.service \
  /opt/cost-simulator/.env \
  /opt/cost-simulator/gunicorn.conf.py
```

## Disaster Recovery

### Recovery Procedures

1. **Application Recovery**:
   ```bash
   # Pull latest image
   docker pull your-registry/cost-simulator:latest
   
   # Restart service
   docker-compose up -d
   
   # Verify health
   curl http://localhost/health
   ```

2. **Configuration Recovery**:
   ```bash
   # Restore from backup
   tar -xzf /backups/config_latest.tar.gz -C /
   
   # Restart services
   systemctl restart nginx cost-simulator
   ```

3. **Data Recovery** (Future):
   ```bash
   # Restore database from backup
   gunzip -c /backups/calculations_latest.db.gz > /app/data/calculations.db
   
   # Restart application
   systemctl restart cost-simulator
   ```

## Scaling Considerations

### Horizontal Scaling

**Load Balancer Configuration**:
```nginx
upstream cost_simulator {
    server app1:5001 weight=1;
    server app2:5001 weight=1;
    server app3:5001 weight=1;
    
    # Health check
    keepalive 32;
}

server {
    listen 80;
    
    location / {
        proxy_pass http://cost_simulator;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Docker Swarm Scaling**:
```bash
# Scale to 3 replicas
docker service scale cost-simulator=3

# Auto-scaling based on CPU
docker service update --replicas-max-per-node 2 cost-simulator
```

### Kubernetes Deployment

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cost-simulator
spec:
  replicas: 3
  selector:
    matchLabels:
      app: cost-simulator
  template:
    metadata:
      labels:
        app: cost-simulator
    spec:
      containers:
      - name: cost-simulator
        image: your-registry/cost-simulator:latest
        ports:
        - containerPort: 5001
        env:
        - name: FLASK_ENV
          value: production
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 5001
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 5001
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: cost-simulator-service
spec:
  selector:
    app: cost-simulator
  ports:
  - port: 80
    targetPort: 5001
  type: LoadBalancer
```

### Performance Targets

**Production SLAs**:
- **Availability**: 99.9% uptime
- **Response Time**: 95th percentile < 200ms
- **Throughput**: 1000 requests/minute
- **Error Rate**: < 0.1% of requests