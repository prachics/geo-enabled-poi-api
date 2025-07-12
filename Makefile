.PHONY: help build up down logs test clean load-data benchmark

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build: ## Build Docker images
	docker-compose build

up: ## Start services
	docker-compose up -d

down: ## Stop services
	docker-compose down

logs: ## View logs
	docker-compose logs -f

test: ## Run tests
	docker-compose exec web python manage.py test

test-coverage: ## Run tests with coverage
	docker-compose exec web python -m pytest --cov=pois tests/

lint: ## Run linting
	docker-compose exec web flake8 geoapi pois tests
	docker-compose exec web black --check geoapi pois tests
	docker-compose exec web isort --check-only geoapi pois tests

format: ## Format code
	docker-compose exec web black geoapi pois tests
	docker-compose exec web isort geoapi pois tests

migrate: ## Run migrations
	docker-compose exec web python manage.py migrate

load-data: ## Load sample data
	docker-compose exec web python manage.py load_sample_data

shell: ## Open Django shell
	docker-compose exec web python manage.py shell

db-shell: ## Open database shell
	docker-compose exec db psql -U geoapi_user -d geoapi

benchmark: ## Run performance benchmarks
	./scripts/bench.sh

clean: ## Clean up containers and volumes
	docker-compose down -v
	docker system prune -f

restart: down up ## Restart services

dev: up load-data ## Start development environment 