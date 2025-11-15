# Setup Guide

Complete guide for setting up the development environment for the E-Commerce AI Multi-Agent Assistant.

## Prerequisites

### Required Software

- **Python 3.11+**: [Download Python](https://www.python.org/downloads/)
- **Node.js 18+**: [Download Node.js](https://nodejs.org/)
- **PostgreSQL 16+**: [Download PostgreSQL](https://www.postgresql.org/download/)
- **Redis** (optional, for cache): [Download Redis](https://redis.io/download)
- **Poetry** (Python dependency manager): [Install Poetry](https://python-poetry.org/docs/#installation)
- **Docker and Docker Compose** (optional, for complete environment): [Download Docker](https://www.docker.com/get-started)

### Verify Installation

```bash
# Check versions
python3 --version    # Should be 3.11+
node --version       # Should be 18+
psql --version       # Should be 16+
poetry --version     # Should be installed
docker --version     # Optional
```

## Step-by-Step Installation

### 1. Clone Repository

```bash
git clone <repository-url>
cd ecommerce-ai-multiagent-assistant
```

### 2. Backend Configuration

#### 2.1. Install Dependencies

```bash
cd backend
poetry install
```

#### 2.2. Configure Environment Variables

Create a `.env` file in the `backend/` root. See [backend/app/config/settings.py](../../backend/app/config/settings.py) for all available settings:

```bash
cp .env.example .env
# Edit .env with your configurations
```

Required environment variables (see [backend/app/config/settings.py](../../backend/app/config/settings.py)):

```env
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ecommerce_ai

# Redis (optional)
REDIS_URL=redis://localhost:6379/0

# RabbitMQ (optional)
RABBITMQ_URL=amqp://guest:guest@localhost:5672/

# OpenAI
OPENAI_API_KEY=sk-...

# Application
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# API
API_HOST=0.0.0.0
API_PORT=8000

# Storage
STORAGE_PATH=./data/storage

# Observability
ENABLE_TRACING=true
ENABLE_METRICS=true
```

#### 2.3. Setup Database

The database setup script ([backend/scripts/setup_db.py](../../backend/scripts/setup_db.py)) creates all necessary extensions, schemas, and tables:

```bash
# Setup database (creates extensions, schemas, tables)
make db-setup

# Optional: Populate with sample data
make db-seed
```

### 3. Frontend Configuration

#### 3.1. Install Dependencies

```bash
cd frontend
npm install
```

#### 3.2. Configure Environment Variables

Create a `.env.local` file in the `frontend/` root:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

### 4. Start Services

#### Option A: Docker Compose (Recommended)

The Docker Compose configuration ([infrastructure/docker/docker-compose.yml](../../infrastructure/docker/docker-compose.yml)) provides a complete environment:

```bash
# In project root
make dev
```

This starts:

- PostgreSQL
- Redis
- Backend API (port 8000) - see [backend/app/api/main.py](../../backend/app/api/main.py)
- Frontend (port 3000)

#### Option B: Manual

**Terminal 1 - Backend**:

```bash
cd backend
make dev-backend
```

This starts the FastAPI server defined in [backend/app/api/main.py](../../backend/app/api/main.py).

**Terminal 2 - Frontend**:

```bash
cd frontend
make dev-frontend
```

**Terminal 3 - Services** (if not using Docker):

```bash
# PostgreSQL and Redis must be running
# Use docker-compose or local installation
```

## Verification

### 1. Verify Backend

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Should return: {"status":"ok"}
```

The health check endpoint is implemented in [backend/app/api/routes/health.py](../../backend/app/api/routes/health.py).

### 2. Verify Frontend

Open `http://localhost:3000` in your browser. The home page should load.

### 3. Verify Database

```bash
# Connect to database
psql -U postgres -d ecommerce_ai

# Check tables
\dt

# Check pgvector extension
\dx
```

## Initial Data Ingestion

### Knowledge Agent (PDFs)

The PDF ingestion script ([backend/scripts/ingest_pdfs.py](../../backend/scripts/ingest_pdfs.py)) processes documents for the Knowledge Agent:

```bash
# Ingest PDFs for knowledge base
make ingest-pdfs

# With options
cd backend
poetry run python scripts/ingest_pdfs.py \
  --directory data/docs \
  --recursive
```

This uses the [KnowledgeIngester](../../backend/app/agents/knowledge/ingester.py) to process documents and store them in the database.

### Analytics Agent (CSVs)

The CSV ingestion script ([backend/scripts/ingest_csvs.py](../../backend/scripts/ingest_csvs.py)) processes data for the Analytics Agent:

```bash
# Ingest CSVs for analytics
make ingest-csvs

# With options
cd backend
poetry run python scripts/ingest_csvs.py \
  --directory data/raw/analytics \
  --recursive
```

This uses the [AnalyticsSchemaBuilder](../../backend/app/agents/analytics/schema_builder.py) to process CSV files and create database tables.

## Useful Commands

### Development

```bash
# Start complete environment
make dev

# Backend only
make dev-backend

# Frontend only
make dev-frontend

# LangGraph Studio (for graph debugging)
make dev-studio
```

The LangGraph graph is defined in [backend/app/graph/build.py](../../backend/app/graph/build.py).

### Database

```bash
# Initial setup
make db-setup

# Populate with sample data
make db-seed

# Complete reset
make db-reset

# Migrations
make db-migrate-create MESSAGE="description"
make db-migrate
```

### Testing

```bash
# All tests
make test

# By type
make test-unit          # backend/tests/unit/
make test-integration   # backend/tests/integration/
make test-e2e           # backend/tests/e2e/

# With coverage
make test-coverage
```

### Linting and Formatting

```bash
# Linting
make lint

# Formatting
make format
```

## Troubleshooting

### Issue: Database Connection Error

**Solution**:

1. Verify PostgreSQL is running: `pg_isready`
2. Check `DATABASE_URL` in `.env` (see [backend/app/config/settings.py](../../backend/app/config/settings.py))
3. Verify PostgreSQL user permissions

### Issue: Python Dependency Installation Error

**Solution**:

1. Check Python version: `python3 --version` (should be 3.11+)
2. Update Poetry: `poetry self update`
3. Clear cache: `poetry cache clear pypi --all`

### Issue: Node Dependency Installation Error

**Solution**:

1. Check Node version: `node --version` (should be 18+)
2. Clear cache: `npm cache clean --force`
3. Delete `node_modules` and `package-lock.json`, then `npm install`

### Issue: Port Already in Use

**Solution**:

1. Backend (8000): Change `API_PORT` in `.env` (see [backend/app/config/settings.py](../../backend/app/config/settings.py))
2. Frontend (3000): Change in `frontend/package.json` scripts
3. Or stop the process using the port:

   ```bash
   # Linux/Mac
   lsof -ti:8000 | xargs kill
   ```

### Issue: Storage Permission Error

**Solution**:

```bash
# Create directory and set permissions
mkdir -p data/storage
chmod 755 data/storage
```

The storage path is configured in [backend/app/config/settings.py](../../backend/app/config/settings.py) and used by [backend/app/infrastructure/storage/local_storage.py](../../backend/app/infrastructure/storage/local_storage.py).

## Next Steps

After setting up the environment:

1. Explore the [API Documentation](../api/endpoints.md) to understand endpoints
2. See [Project Structure](../../README.md#architecture) to understand organization
3. Review [Troubleshooting](../operations/troubleshooting.md) for common issues

## Support

If you encounter problems:

1. Consult [Troubleshooting](../operations/troubleshooting.md)
2. Check logs: `make logs` or `docker-compose logs`
3. Open an issue in the repository

---

**← [Back to Documentation Index](../README.md)**
