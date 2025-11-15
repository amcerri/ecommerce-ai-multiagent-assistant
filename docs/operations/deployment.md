# Deployment Guide

Complete guide for deploying the E-Commerce AI Multi-Agent Assistant to production.

## Prerequisites

### System Requirements

- **Server**: Linux (Ubuntu 22.04+ recommended) or similar
- **Docker**: 20.10+ and Docker Compose 2.0+
- **PostgreSQL**: 16+ (or use Docker)
- **Redis**: 7.0+ (optional, for cache)
- **Memory**: Minimum 4GB RAM (8GB+ recommended)
- **Disk**: Minimum 20GB free space

### Environment Variables

Configure the following environment variables (see [backend/app/config/settings.py](../../backend/app/config/settings.py)):

```env
# Database
DATABASE_URL=postgresql://user:password@host:5432/database

# Redis (optional)
REDIS_URL=redis://host:6379/0

# RabbitMQ (optional)
RABBITMQ_URL=amqp://user:password@host:5672//

# OpenAI
OPENAI_API_KEY=sk-...

# Application
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# API
API_HOST=0.0.0.0
API_PORT=8000

# Storage
STORAGE_PATH=/app/data/storage

# Observability
ENABLE_TRACING=true
ENABLE_METRICS=true

# CORS (adjust for your domain)
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

## Docker Compose Deployment

### 1. Prepare Files

```bash
# Clone repository
git clone <repository-url>
cd ecommerce-ai-multiagent-assistant

# Configure environment variables
cp .env.example .env
# Edit .env with production values
```

### 2. Build Images

The Docker Compose configuration is in [infrastructure/docker/docker-compose.yml](../../infrastructure/docker/docker-compose.yml):

```bash
# Build all images
docker-compose -f infrastructure/docker/docker-compose.yml build

# Or just backend/frontend
docker-compose -f infrastructure/docker/docker-compose.yml build backend
docker-compose -f infrastructure/docker/docker-compose.yml build frontend
```

### 3. Start Services

```bash
# Start all services
docker-compose -f infrastructure/docker/docker-compose.yml up -d

# Check status
docker-compose -f infrastructure/docker/docker-compose.yml ps

# View logs
docker-compose -f infrastructure/docker/docker-compose.yml logs -f
```

### 4. Database Setup

The database setup script ([backend/scripts/setup_db.py](../../backend/scripts/setup_db.py)) creates all necessary tables:

```bash
# Run database setup
docker-compose -f infrastructure/docker/docker-compose.yml exec backend \
  poetry run python scripts/setup_db.py

# Optional: Populate with initial data
docker-compose -f infrastructure/docker/docker-compose.yml exec backend \
  poetry run python scripts/seed_data.py
```

### 5. Verify Deployment

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Readiness check
curl http://localhost:8000/api/v1/health/ready

# Verify frontend
curl http://localhost:3000
```

## Manual Deployment

### 1. Backend

#### 1.1. Install Dependencies

```bash
cd backend
poetry install --no-dev
```

#### 1.2. Configure Environment

```bash
# Create .env
cp .env.example .env
# Edit .env (see backend/app/config/settings.py for all options)
```

#### 1.3. Database Setup

```bash
poetry run python scripts/setup_db.py
```

#### 1.4. Run Migrations

```bash
poetry run alembic upgrade head
```

#### 1.5. Start Server

The FastAPI application is defined in [backend/app/api/main.py](../../backend/app/api/main.py):

```bash
# Development
poetry run uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000

# Production (with gunicorn)
poetry run gunicorn app.api.main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

### 2. Frontend

#### 2.1. Build

```bash
cd frontend
npm install
npm run build
```

#### 2.2. Start Server

```bash
# Development
npm run dev

# Production
npm start
```

## Service Configuration

### Nginx (Reverse Proxy)

Example Nginx configuration:

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket
    location /api/v1/chat/stream {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

### Systemd (Service)

Create file `/etc/systemd/system/ecommerce-ai.service`:

```ini
[Unit]
Description=E-Commerce AI Multi-Agent Assistant
After=network.target postgresql.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/ecommerce-ai-multiagent-assistant/backend
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/uvicorn app.api.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable ecommerce-ai
sudo systemctl start ecommerce-ai
sudo systemctl status ecommerce-ai
```

## Monitoring

### Health Checks

Configure health checks for monitoring (see [backend/app/api/routes/health.py](../../backend/app/api/routes/health.py)):

```bash
# Basic health check
curl http://localhost:8000/api/v1/health

# Readiness check (verifies dependencies)
curl http://localhost:8000/api/v1/health/ready

# Liveness check
curl http://localhost:8000/api/v1/health/live
```

### Prometheus Metrics

Metrics endpoint (see [backend/app/infrastructure/metrics/collector.py](../../backend/app/infrastructure/metrics/collector.py)):

```
http://localhost:8000/metrics
```

Configure Prometheus to collect metrics:

```yaml
scrape_configs:
  - job_name: 'ecommerce-ai'
    scrape_interval: 15s
    static_configs:
      - targets: ['localhost:8000']
```

### Logs

Structured logs in JSON (see [backend/app/infrastructure/logging/logger.py](../../backend/app/infrastructure/logging/logger.py)):

```bash
# View backend logs
docker-compose logs -f backend

# Or if running manually
tail -f /var/log/ecommerce-ai/app.log
```

## Security

### Recommendations

1. **HTTPS**: Use HTTPS in production (Let's Encrypt, etc.)
2. **Secrets**: Never commit secrets in code
3. **Firewall**: Configure firewall to allow only necessary ports
4. **Rate Limiting**: Rate limiting is already implemented (see [backend/app/config/constants.py](../../backend/app/config/constants.py))
5. **CORS**: Configure `ALLOWED_ORIGINS` correctly (see [backend/app/config/settings.py](../../backend/app/config/settings.py))
6. **Database**: Use strong passwords and SSL connections

### Sensitive Environment Variables

Never expose these variables:

- `OPENAI_API_KEY`
- `DATABASE_URL` (contains password)
- `REDIS_URL` (may contain password)
- `RABBITMQ_URL` (contains password)

## Backup

### Database

```bash
# Backup
pg_dump -U postgres ecommerce_ai > backup_$(date +%Y%m%d).sql

# Restore
psql -U postgres ecommerce_ai < backup_20240115.sql
```

### Storage

```bash
# Backup files
tar -czf storage_backup_$(date +%Y%m%d).tar.gz data/storage/
```

The storage path is configured in [backend/app/config/settings.py](../../backend/app/config/settings.py).

## Updates

### Update Code

```bash
# Pull latest
git pull origin main

# Rebuild (Docker)
docker-compose -f infrastructure/docker/docker-compose.yml build
docker-compose -f infrastructure/docker/docker-compose.yml up -d

# Migrations (if any)
docker-compose -f infrastructure/docker/docker-compose.yml exec backend \
  poetry run alembic upgrade head
```

### Rollback

```bash
# Revert to previous commit
git checkout <previous-commit>

# Rebuild
docker-compose -f infrastructure/docker/docker-compose.yml build
docker-compose -f infrastructure/docker/docker-compose.yml up -d
```

## Post-Deployment Verification

After deployment, verify:

- [ ] Health checks return "ok"
- [ ] Readiness check returns "ready"
- [ ] API responds correctly
- [ ] Frontend loads
- [ ] WebSocket works
- [ ] Logs show no critical errors
- [ ] Metrics are being collected

## Next Steps

After successful deployment:

1. Configure monitoring (Prometheus, Grafana)
2. Configure alerts
3. Configure automatic backups
4. Document rollback procedures
5. Configure CI/CD for automatic deployments

---

**← [Back to Documentation Index](../README.md)**
