.PHONY: install test integration fmt lint up down migrate clean help

# Default target
.DEFAULT_GOAL := help

# Colors for output
CYAN := \033[36m
GREEN := \033[32m
RESET := \033[0m

help: ## Show this help message
	@echo "$(CYAN)Available commands:$(RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(RESET) %s\n", $$1, $$2}'

install: ## Install dependencies
	uv pip install -e ".[dev]"

test: ## Run unit tests with coverage
	pytest tests/unit -v --cov=src --cov-report=term-missing -m "not integration"

integration: ## Run integration tests (requires docker services)
	pytest tests/integration -v --cov=src --cov-report=term-missing -m integration

test-all: ## Run all tests
	pytest tests -v --cov=src --cov-report=term-missing --cov-report=html

fmt: ## Format code with Ruff
	ruff format src tests

lint: ## Run linters (Ruff + MyPy)
	ruff check src tests --fix
	ruff format --check src tests
	mypy src --ignore-missing-imports

lint-check: ## Run linters without fixing
	ruff check src tests
	ruff format --check src tests
	mypy src --ignore-missing-imports

up: ## Start all Docker services
	docker compose up -d

up-build: ## Build and start all Docker services
	docker compose up -d --build

down: ## Stop all Docker services
	docker compose down

down-v: ## Stop all Docker services and remove volumes
	docker compose down -v

migrate: ## Run database migrations
	alembic upgrade head

migrate-down: ## Rollback last migration
	alembic downgrade -1

migrate-new: ## Create a new migration (usage: make migrate-new MSG="migration message")
	alembic revision --autogenerate -m "$(MSG)"

logs: ## Show Docker logs
	docker compose logs -f

logs-app: ## Show app container logs
	docker compose logs -f app

shell: ## Open shell in app container
	docker compose exec app bash

psql: ## Connect to PostgreSQL
	docker compose exec postgres psql -U postgres -d dropshipping

clean: ## Clean up cache and build artifacts
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf build dist htmlcov .coverage coverage.xml

# Development workflow shortcuts
dev: up migrate ## Start development environment (up + migrate)

reset: down-v up migrate ## Reset development environment (clean slate)
