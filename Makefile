.PHONY: help bootstrap bootstrap-backend bootstrap-frontend
.PHONY: dev dev-backend dev-frontend dev-studio
.PHONY: docker-up docker-down docker-build docker-logs docker-restart
.PHONY: db-setup db-seed db-reset db-migrate db-migrate-create
.PHONY: ingest-pdfs ingest-csvs
.PHONY: test test-backend test-frontend test-unit test-integration test-e2e test-coverage
.PHONY: lint lint-backend lint-frontend format format-backend format-frontend
.PHONY: build build-backend build-frontend
.PHONY: clean clean-backend clean-frontend clean-docker
.PHONY: logs logs-backend logs-frontend shell-backend shell-frontend shell-db

# Variables
PYTHON := python3
POETRY := poetry
NPM := npm
DOCKER_COMPOSE := docker-compose
BACKEND_DIR := backend
FRONTEND_DIR := frontend
DOCKER_COMPOSE_FILE := infrastructure/docker/docker-compose.yml

# Default target
.DEFAULT_GOAL := help

# Help target
help:
	@echo "E-Commerce AI Multi-Agent Assistant - Makefile"
	@echo ""
	@echo "Available commands:"
	@echo ""
	@echo "  Bootstrap:"
	@echo "    make bootstrap              - Bootstrap complete project (backend + frontend)"
	@echo "    make bootstrap-backend      - Bootstrap backend only"
	@echo "    make bootstrap-frontend     - Bootstrap frontend only"
	@echo ""
	@echo "  Development:"
	@echo "    make dev                    - Start complete development environment (Docker Compose)"
	@echo "    make dev-backend            - Start backend only (Poetry run)"
	@echo "    make dev-frontend           - Start frontend only (npm run dev)"
	@echo "    make dev-studio             - Start LangGraph Studio"
	@echo ""
	@echo "  Docker:"
	@echo "    make docker-up              - Start Docker containers"
	@echo "    make docker-down            - Stop Docker containers"
	@echo "    make docker-build           - Build Docker images"
	@echo "    make docker-logs            - Show Docker container logs"
	@echo "    make docker-restart         - Restart Docker containers"
	@echo ""
	@echo "  Database:"
	@echo "    make db-setup               - Setup database (create extensions, schemas, tables)"
	@echo "    make db-seed                - Seed database with sample data"
	@echo "    make db-reset               - Reset database (drop and recreate)"
	@echo "    make db-migrate             - Run database migrations"
	@echo "    make db-migrate-create      - Create new migration (usage: make db-migrate-create MESSAGE='migration name')"
	@echo ""
	@echo "  Ingestion:"
	@echo "    make ingest-pdfs            - Ingest PDFs (usage: make ingest-pdfs DIR=data/docs)"
	@echo "    make ingest-csvs            - Ingest CSVs (usage: make ingest-csvs DIR=data/raw/analytics)"
	@echo ""
	@echo "  Testing:"
	@echo "    make test                   - Run all tests"
	@echo "    make test-backend           - Run backend tests"
	@echo "    make test-frontend          - Run frontend tests"
	@echo "    make test-unit              - Run unit tests only"
	@echo "    make test-integration       - Run integration tests only"
	@echo "    make test-e2e               - Run end-to-end tests only"
	@echo "    make test-coverage          - Run tests with coverage report"
	@echo ""
	@echo "  Linting and Formatting:"
	@echo "    make lint                   - Run all linters (backend + frontend)"
	@echo "    make lint-backend           - Run backend linters (ruff, mypy)"
	@echo "    make lint-frontend          - Run frontend linters (eslint, tsc)"
	@echo "    make format                 - Format all code (backend + frontend)"
	@echo "    make format-backend         - Format backend code (ruff format)"
	@echo "    make format-frontend        - Format frontend code (prettier)"
	@echo ""
	@echo "  Build:"
	@echo "    make build                  - Build complete project (backend + frontend)"
	@echo "    make build-backend          - Build backend only"
	@echo "    make build-frontend         - Build frontend only"
	@echo ""
	@echo "  Cleanup:"
	@echo "    make clean                  - Clean all temporary files"
	@echo "    make clean-backend          - Clean backend temporary files"
	@echo "    make clean-frontend         - Clean frontend temporary files"
	@echo "    make clean-docker           - Clean Docker containers and volumes"
	@echo ""
	@echo "  Utilities:"
	@echo "    make logs                   - Show logs (backend + frontend)"
	@echo "    make logs-backend           - Show backend logs"
	@echo "    make logs-frontend          - Show frontend logs"
	@echo "    make shell-backend          - Open backend shell"
	@echo "    make shell-frontend         - Open frontend shell"
	@echo "    make shell-db               - Open database shell"

# Bootstrap targets
bootstrap: bootstrap-backend bootstrap-frontend
	@echo "✅ Bootstrap complete!"

bootstrap-backend:
	@echo "📦 Bootstrapping backend..."
	cd $(BACKEND_DIR) && $(POETRY) install
	@echo "✅ Backend bootstrap complete!"

bootstrap-frontend:
	@echo "📦 Bootstrapping frontend..."
	cd $(FRONTEND_DIR) && $(NPM) install
	@echo "✅ Frontend bootstrap complete!"

# Development targets
dev:
	@echo "🚀 Starting development environment..."
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) up

dev-backend:
	@echo "🚀 Starting backend..."
	cd $(BACKEND_DIR) && $(POETRY) run uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	@echo "🚀 Starting frontend..."
	cd $(FRONTEND_DIR) && $(NPM) run dev

dev-studio:
	@echo "🚀 Starting LangGraph Studio..."
	cd $(BACKEND_DIR) && $(POETRY) run langgraph dev

# Docker targets
docker-up:
	@echo "🐳 Starting Docker containers..."
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) up -d

docker-down:
	@echo "🐳 Stopping Docker containers..."
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) down

docker-build:
	@echo "🐳 Building Docker images..."
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) build

docker-logs:
	@echo "🐳 Showing Docker container logs..."
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) logs -f

docker-restart: docker-down docker-up
	@echo "🐳 Docker containers restarted"

# Database targets
db-setup:
	@echo "🗄️  Setting up database..."
	cd $(BACKEND_DIR) && $(POETRY) run $(PYTHON) scripts/setup_db.py

db-seed:
	@echo "🗄️  Seeding database..."
	cd $(BACKEND_DIR) && $(POETRY) run $(PYTHON) scripts/seed_data.py

db-reset:
	@echo "🗄️  Resetting database..."
	cd $(BACKEND_DIR) && $(POETRY) run $(PYTHON) scripts/setup_db.py --reset

db-migrate:
	@echo "🗄️  Running database migrations..."
	cd $(BACKEND_DIR) && $(POETRY) run alembic upgrade head

db-migrate-create:
	@if [ -z "$(MESSAGE)" ]; then \
		echo "❌ Error: MESSAGE is required. Usage: make db-migrate-create MESSAGE='migration name'"; \
		exit 1; \
	fi
	@echo "🗄️  Creating new migration: $(MESSAGE)"
	cd $(BACKEND_DIR) && $(POETRY) run alembic revision --autogenerate -m "$(MESSAGE)"

# Ingestion targets
ingest-pdfs:
	@if [ -z "$(DIR)" ]; then \
		echo "❌ Error: DIR is required. Usage: make ingest-pdfs DIR=data/docs"; \
		exit 1; \
	fi
	@echo "📄 Ingesting PDFs from: $(DIR)"
	cd $(BACKEND_DIR) && $(POETRY) run $(PYTHON) scripts/ingest_pdfs.py $(DIR)

ingest-csvs:
	@if [ -z "$(DIR)" ]; then \
		echo "❌ Error: DIR is required. Usage: make ingest-csvs DIR=data/raw/analytics"; \
		exit 1; \
	fi
	@echo "📊 Ingesting CSVs from: $(DIR)"
	cd $(BACKEND_DIR) && $(POETRY) run $(PYTHON) scripts/ingest_csvs.py $(DIR)

# Testing targets
test: test-backend test-frontend
	@echo "✅ All tests complete!"

test-backend:
	@echo "🧪 Running backend tests..."
	cd $(BACKEND_DIR) && $(POETRY) run pytest

test-frontend:
	@echo "🧪 Running frontend tests..."
	cd $(FRONTEND_DIR) && $(NPM) run test

test-unit:
	@echo "🧪 Running unit tests..."
	cd $(BACKEND_DIR) && $(POETRY) run pytest tests/unit/

test-integration:
	@echo "🧪 Running integration tests..."
	cd $(BACKEND_DIR) && $(POETRY) run pytest tests/integration/

test-e2e:
	@echo "🧪 Running end-to-end tests..."
	cd $(BACKEND_DIR) && $(POETRY) run pytest tests/e2e/

test-coverage:
	@echo "🧪 Running tests with coverage..."
	cd $(BACKEND_DIR) && $(POETRY) run pytest --cov=app --cov-report=html --cov-report=term

# Linting and formatting targets
lint: lint-backend lint-frontend
	@echo "✅ Linting complete!"

lint-backend:
	@echo "🔍 Linting backend..."
	cd $(BACKEND_DIR) && $(POETRY) run ruff check .
	cd $(BACKEND_DIR) && $(POETRY) run mypy app

lint-frontend:
	@echo "🔍 Linting frontend..."
	cd $(FRONTEND_DIR) && $(NPM) run lint
	cd $(FRONTEND_DIR) && $(NPM) run type-check

format: format-backend format-frontend
	@echo "✅ Formatting complete!"

format-backend:
	@echo "✨ Formatting backend..."
	cd $(BACKEND_DIR) && $(POETRY) run ruff format .

format-frontend:
	@echo "✨ Formatting frontend..."
	cd $(FRONTEND_DIR) && $(NPM) run format || echo "⚠️  Prettier not configured, skipping..."

# Build targets
build: build-backend build-frontend
	@echo "✅ Build complete!"

build-backend:
	@echo "🔨 Building backend..."
	cd $(BACKEND_DIR) && $(POETRY) build

build-frontend:
	@echo "🔨 Building frontend..."
	cd $(FRONTEND_DIR) && $(NPM) run build

# Cleanup targets
clean: clean-backend clean-frontend
	@echo "✅ Cleanup complete!"

clean-backend:
	@echo "🧹 Cleaning backend..."
	find $(BACKEND_DIR) -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
	find $(BACKEND_DIR) -type f -name "*.pyc" -delete 2>/dev/null || true
	find $(BACKEND_DIR) -type d -name ".pytest_cache" -exec rm -r {} + 2>/dev/null || true
	find $(BACKEND_DIR) -type d -name ".mypy_cache" -exec rm -r {} + 2>/dev/null || true
	find $(BACKEND_DIR) -type d -name ".ruff_cache" -exec rm -r {} + 2>/dev/null || true
	find $(BACKEND_DIR) -type f -name "*.egg-info" -exec rm -r {} + 2>/dev/null || true
	@echo "✅ Backend cleanup complete!"

clean-frontend:
	@echo "🧹 Cleaning frontend..."
	cd $(FRONTEND_DIR) && rm -rf node_modules .next out .cache .parcel-cache 2>/dev/null || true
	@echo "✅ Frontend cleanup complete!"

clean-docker:
	@echo "🧹 Cleaning Docker..."
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) down -v --remove-orphans
	docker system prune -f
	@echo "✅ Docker cleanup complete!"

# Utility targets
logs: logs-backend logs-frontend

logs-backend:
	@echo "📋 Showing backend logs..."
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) logs -f backend || \
	echo "⚠️  Backend container not running. Start with: make docker-up"

logs-frontend:
	@echo "📋 Showing frontend logs..."
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) logs -f frontend || \
	echo "⚠️  Frontend container not running. Start with: make docker-up"

shell-backend:
	@echo "🐚 Opening backend shell..."
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) exec backend /bin/bash || \
	cd $(BACKEND_DIR) && $(POETRY) shell || \
	echo "⚠️  Backend container not running. Start with: make docker-up"

shell-frontend:
	@echo "🐚 Opening frontend shell..."
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) exec frontend /bin/sh || \
	cd $(FRONTEND_DIR) && /bin/bash || \
	echo "⚠️  Frontend container not running. Start with: make docker-up"

shell-db:
	@echo "🐚 Opening database shell..."
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) exec postgres psql -U postgres -d ecommerce_db || \
	echo "⚠️  Database container not running. Start with: make docker-up"

