# Troubleshooting

Guide for solving common problems with the E-Commerce AI Multi-Agent Assistant.

## Common Issues

### Backend won't start

**Symptoms**: Error starting backend server.

**Solutions**:

1. **Check environment variables** (see [backend/app/config/settings.py](../../backend/app/config/settings.py)):

```bash
cd backend
cat .env
# Verify all required variables are configured
```

2. **Check database connection**:

```bash
psql $DATABASE_URL -c "SELECT 1"
# If it fails, check DATABASE_URL
```

3. **Check dependencies**:

```bash
cd backend
poetry install
```

4. **Check logs**:

```bash
# Docker
docker-compose logs backend

# Manual
tail -f logs/app.log
```

The logging configuration is in [backend/app/infrastructure/logging/logger.py](../../backend/app/infrastructure/logging/logger.py).

### Database connection error

**Symptoms**: `Connection refused`, `timeout`, or authentication errors.

**Solutions**:

1. **Check if PostgreSQL is running**:

```bash
# Docker
docker-compose ps postgres

# Local
pg_isready
```

2. **Check DATABASE_URL** (see [backend/app/config/settings.py](../../backend/app/config/settings.py)):

```bash
echo $DATABASE_URL
# Format: postgresql://user:password@host:5432/database
```

3. **Check permissions**:

```bash
psql -U postgres -c "SELECT 1"
```

4. **Check firewall**:

```bash
# If using Docker, verify port is exposed
docker-compose ps
```

### Error processing message

**Symptoms**: 500 error when sending message via API.

**Solutions**:

1. **Check logs**:

```bash
docker-compose logs backend | grep ERROR
```

2. **Check LLM client** (see [backend/app/infrastructure/llm/client.py](../../backend/app/infrastructure/llm/client.py)):

```bash
# Check OPENAI_API_KEY
echo $OPENAI_API_KEY | cut -c1-10
```

3. **Check database**:

```bash
curl http://localhost:8000/api/v1/health/ready
```

4. **Test endpoint directly**:

```bash
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'
```

The chat endpoint is implemented in [backend/app/api/routes/chat.py](../../backend/app/api/routes/chat.py).

### Frontend won't load

**Symptoms**: Blank page or console errors.

**Solutions**:

1. **Check if frontend is running**:

```bash
curl http://localhost:3000
```

2. **Check environment variables**:

```bash
cd frontend
cat .env.local
# Check NEXT_PUBLIC_API_URL
```

3. **Check browser console**:
- Open DevTools (F12)
- Check errors in Console
- Check errors in Network tab

4. **Rebuild**:

```bash
cd frontend
rm -rf .next node_modules
npm install
npm run build
```

### Cache error (Redis)

**Symptoms**: Cache-related errors, but system continues to work.

**Solutions**:

1. **Check if Redis is running**:

```bash
# Docker
docker-compose ps redis

# Local
redis-cli ping
# Should return: PONG
```

2. **System works without cache**:
- Cache is optional (graceful degradation) - see [backend/app/infrastructure/cache/cache_manager.py](../../backend/app/infrastructure/cache/cache_manager.py)
- System continues to work, just without cache

3. **Check REDIS_URL** (see [backend/app/config/settings.py](../../backend/app/config/settings.py)):

```bash
echo $REDIS_URL
# Format: redis://host:6379/0
```

### Document upload error

**Symptoms**: 400 or 422 error when uploading.

**Solutions**:

1. **Check file type** (see [backend/app/config/constants.py](../../backend/app/config/constants.py) - `SUPPORTED_FILE_TYPES`):

```bash
# Supported types: pdf, docx, txt, png, jpg, jpeg, tiff
file document.pdf
```

2. **Check size** (see [backend/app/config/constants.py](../../backend/app/config/constants.py) - `MAX_FILE_SIZE_MB`):

```bash
# Maximum: 10MB
ls -lh document.pdf
```

3. **Check storage path** (see [backend/app/infrastructure/storage/local_storage.py](../../backend/app/infrastructure/storage/local_storage.py)):

```bash
# Verify directory exists and has permissions
ls -ld data/storage
chmod 755 data/storage
```

4. **Check logs**:

```bash
docker-compose logs backend | grep "upload"
```

The document upload endpoint is in [backend/app/api/routes/documents.py](../../backend/app/api/routes/documents.py).

### Incorrect routing error

**Symptoms**: Query routed to wrong agent.

**Solutions**:

1. **Verify routing is semantic**:
- Routing does NOT use keywords - see [backend/app/routing/router.py](../../backend/app/routing/router.py)
- Uses embeddings + LLM for classification - see [backend/app/routing/classifier.py](../../backend/app/routing/classifier.py)

2. **Check routing cache**:

```bash
# Clear cache
docker-compose exec redis redis-cli FLUSHDB
```

3. **Check routing logs**:

```bash
docker-compose logs backend | grep "routing"
```

### Slow performance

**Symptoms**: Very slow responses.

**Solutions**:

1. **Check metrics** (see [backend/app/infrastructure/metrics/collector.py](../../backend/app/infrastructure/metrics/collector.py)):

```bash
curl http://localhost:8000/metrics | grep http_request_duration
```

2. **Check cache** (see [backend/app/infrastructure/cache/cache_manager.py](../../backend/app/infrastructure/cache/cache_manager.py)):

```bash
# Verify cache is working
docker-compose exec redis redis-cli INFO stats
```

3. **Check database**:

```bash
# Check slow queries
psql $DATABASE_URL -c "SELECT * FROM pg_stat_activity WHERE state = 'active'"
```

4. **Check resources**:

```bash
# CPU and memory
docker stats
# or
top
```

### Memory error

**Symptoms**: `MemoryError` or OOM (Out of Memory).

**Solutions**:

1. **Increase memory**:

```bash
# Docker
docker-compose down
# Increase memory in docker-compose.yml or Docker settings
docker-compose up -d
```

2. **Check memory usage**:

```bash
docker stats
```

3. **Limit file sizes**:
- Already configured: MAX_FILE_SIZE_MB = 10 (see [backend/app/config/constants.py](../../backend/app/config/constants.py))
- Verify it's being respected

## Useful Commands

### Check Status

```bash
# Status of all services
docker-compose ps

# Health checks
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/health/ready

# Logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Debug

```bash
# Shell in backend container
docker-compose exec backend bash

# Shell in database
docker-compose exec postgres psql -U postgres -d ecommerce_db

# Shell in Redis
docker-compose exec redis redis-cli

# Check environment variables
docker-compose exec backend env | grep DATABASE
```

### Cleanup

```bash
# Clear Redis cache
docker-compose exec redis redis-cli FLUSHDB

# Clear logs
docker-compose logs --tail=0 -f

# Clear volumes (WARNING: deletes data)
docker-compose down -v
```

### Testing

```bash
# Test API
curl http://localhost:8000/api/v1/health

# Test chat
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'

# Test upload
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -F "file=@test.pdf" \
  -F "type=commerce"
```

## Important Logs

### Backend

```bash
# All logs
docker-compose logs backend

# Errors only
docker-compose logs backend | grep ERROR

# Last 100 lines
docker-compose logs --tail=100 backend

# Follow logs in real-time
docker-compose logs -f backend
```

Logging is configured in [backend/app/infrastructure/logging/logger.py](../../backend/app/infrastructure/logging/logger.py).

### Frontend

```bash
# Frontend logs
docker-compose logs frontend

# Follow logs
docker-compose logs -f frontend
```

### Database

```bash
# PostgreSQL logs
docker-compose logs postgres

# Check slow queries
docker-compose exec postgres psql -U postgres -d ecommerce_db \
  -c "SELECT * FROM pg_stat_activity WHERE state = 'active'"
```

## Support Contact

If problems persist:

1. **Collect information**:
   - Relevant logs
   - Versions (Python, Node, Docker)
   - Configuration (without secrets)
   - Steps to reproduce

2. **Open issue**:
   - Descriptive title
   - Problem description
   - Logs and configuration (without secrets)
   - Steps to reproduce

3. **Check documentation**:
   - [Setup](../development/setup.md)
   - [Deployment](deployment.md)
   - [API Documentation](../api/endpoints.md)

## Troubleshooting Checklist

Before asking for help, verify:

- [ ] Logs have been checked
- [ ] Health checks have been tested
- [ ] Environment variables are correct (see [backend/app/config/settings.py](../../backend/app/config/settings.py))
- [ ] Services are running (PostgreSQL, Redis, etc.)
- [ ] Ports are not in use by other processes
- [ ] File permissions are correct
- [ ] Documentation has been consulted
- [ ] Problem has been reproduced in a clean environment

---

**← [Back to Documentation Index](../README.md)**
