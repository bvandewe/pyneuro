# Makefile for Neuroglia Python Framework
#
# This Makefile provides convenient commands for building, testing, and managing
# the Neuroglia Python framework and its sample applications.

.PHONY: help install dev-install build test test-coverage lint format clean docs docs-serve docs-build publish sample-mario sample-openbank sample-gateway mario-start mario-stop mario-restart mario-status mario-logs mario-clean mario-reset mario-open mario-test-data mario-clean-orders mario-create-menu mario-remove-validation

# Default target
help: ## Show this help message
	@echo "🐍 Neuroglia Python Framework - Build System"
	@echo ""
	@echo "Available commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""

# Python and Poetry commands
PYTHON := python3
POETRY := poetry
PIP := pip

# Project directories
SRC_DIR := src
DOCS_DIR := docs
SAMPLES_DIR := samples
TESTS_DIR := tests
SCRIPTS_DIR := scripts

# Sample applications
MARIO_PIZZERIA := $(SAMPLES_DIR)/mario-pizzeria
OPENBANK := $(SAMPLES_DIR)/openbank
API_GATEWAY := $(SAMPLES_DIR)/api-gateway
DESKTOP_CONTROLLER := $(SAMPLES_DIR)/desktop-controller
LAB_RESOURCE_MANAGER := $(SAMPLES_DIR)/lab_resource_manager

##@ Installation & Setup

install: ## Install production dependencies and pre-commit hooks
	@echo "📦 Installing production dependencies..."
	$(POETRY) install --only=main
	@echo "🪝 Installing pre-commit hooks..."
	$(POETRY) run pre-commit install

dev-install: ## Install development dependencies
	@echo "🔧 Installing development dependencies..."
	$(POETRY) install
	@echo "✅ Development environment ready!"

setup-path: ## Add pyneuroctl to system PATH
	@echo "🔧 Setting up pyneuroctl in PATH..."
	@chmod +x $(SCRIPTS_DIR)/setup/add_to_path.sh
	@$(SCRIPTS_DIR)/setup/add_to_path.sh

##@ Building & Packaging

build: ## Build the package
	@echo "🏗️  Building package..."
	$(POETRY) build
	@echo "✅ Package built successfully!"

clean: ## Clean build artifacts and cache files
	@echo "🧹 Cleaning build artifacts..."
	@rm -rf dist/
	@rm -rf build/
	@rm -rf *.egg-info/
	@find . -type d -name __pycache__ -delete
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@find . -type d -name ".pytest_cache" -delete
	@find . -type d -name ".coverage" -delete
	@rm -rf site/
	@echo "✅ Cleanup completed!"

##@ Testing

test: ## Run all tests
	@echo "🧪 Running all tests..."
	$(POETRY) run pytest $(TESTS_DIR)/ -v --tb=short

test-coverage: ## Run tests with coverage report
	@echo "🧪 Running tests with coverage..."
	$(POETRY) run pytest $(TESTS_DIR)/ --cov=$(SRC_DIR)/neuroglia --cov-report=html --cov-report=term --cov-report=xml
	@echo "📊 Coverage report generated in htmlcov/"

test-unit: ## Run unit tests only
	@echo "🧪 Running unit tests..."
	$(POETRY) run pytest $(TESTS_DIR)/unit/ -v

test-integration: ## Run integration tests only
	@echo "🧪 Running integration tests..."
	$(POETRY) run pytest $(TESTS_DIR)/integration/ -v

test-mario: ## Test Mario's Pizzeria sample
	@echo "🍕 Testing Mario's Pizzeria..."
	$(POETRY) run pytest $(TESTS_DIR)/ -k mario_pizzeria -v

test-samples: ## Test all sample applications
	@echo "🧪 Testing all samples..."
	$(POETRY) run pytest $(TESTS_DIR)/ -k "mario_pizzeria or openbank or api_gateway or desktop_controller" -v

##@ Code Quality

lint: ## Run linting (flake8, pylint)
	@echo "🔍 Running linting..."
	$(POETRY) run flake8 $(SRC_DIR)/ $(SAMPLES_DIR)/ $(TESTS_DIR)/
	$(POETRY) run pylint $(SRC_DIR)/neuroglia/

format: ## Format code with black and isort
	@echo "🎨 Formatting code..."
	$(POETRY) run black $(SRC_DIR)/ $(SAMPLES_DIR)/ $(TESTS_DIR)/
	$(POETRY) run isort $(SRC_DIR)/ $(SAMPLES_DIR)/ $(TESTS_DIR)/
	@echo "✅ Code formatting completed!"

format-check: ## Check code formatting without making changes
	@echo "🔍 Checking code formatting..."
	$(POETRY) run black --check $(SRC_DIR)/ $(SAMPLES_DIR)/ $(TESTS_DIR)/
	$(POETRY) run isort --check-only $(SRC_DIR)/ $(SAMPLES_DIR)/ $(TESTS_DIR)/

##@ Documentation

docs: ## Build documentation
	@echo "📚 Building documentation..."
	$(POETRY) run mkdocs build
	@echo "✅ Documentation built in site/"

docs-serve: ## Serve documentation locally (development server)
	@echo "📚 Starting documentation server..."
	$(eval DEV_PORT := $(shell grep '^DOCS_DEV_PORT=' .env 2>/dev/null | cut -d'=' -f2 | tr -d ' ' || echo '8000'))
	@echo "Checking for existing servers on port $(DEV_PORT)..."
	@lsof -ti:$(DEV_PORT) | xargs -r kill -9 2>/dev/null || true
	@echo "✅ Open http://127.0.0.1:$(DEV_PORT) in your browser"
	poetry run mkdocs serve --dev-addr=127.0.0.1:$(DEV_PORT)

docs-deploy: ## Deploy documentation to GitHub Pages
	@echo "🚀 Deploying documentation..."
	$(POETRY) run mkdocs gh-deploy

docs-validate: ## Validate Mermaid diagrams in documentation
	@echo "📊 Validating Mermaid diagrams..."
	$(PYTHON) validate_mermaid.py

##@ Publishing

publish-test: ## Publish to TestPyPI
	@echo "🚀 Publishing to TestPyPI..."
	$(POETRY) config repositories.testpypi https://test.pypi.org/legacy/
	$(POETRY) publish -r testpypi

publish: build ## Publish to PyPI
	@echo "🚀 Publishing to PyPI..."
	$(POETRY) publish

##@ Sample Applications

sample-openbank: ## Run OpenBank sample
	@echo "🏦 Starting OpenBank..."
	cd $(OPENBANK) && $(POETRY) run $(PYTHON) main.py

sample-gateway: ## Run API Gateway sample
	@echo "🌐 Starting API Gateway..."
	cd $(API_GATEWAY) && $(POETRY) run $(PYTHON) main.py

sample-desktop: ## Run Desktop Controller sample
	@echo "🖥️  Starting Desktop Controller..."
	cd $(DESKTOP_CONTROLLER) && $(POETRY) run $(PYTHON) main.py

sample-lab: ## Run Lab Resource Manager sample
	@echo "🧪 Starting Lab Resource Manager..."
	cd $(LAB_RESOURCE_MANAGER) && $(POETRY) run $(PYTHON) main.py

##@ Sample Management (using pyneuroctl)

samples-list: ## List all available samples
	@echo "📋 Available sample applications:"
	@$(PYTHON) $(SRC_DIR)/cli/pyneuroctl.py list

samples-status: ## Show status of all samples
	@echo "📊 Sample application status:"
	@$(PYTHON) $(SRC_DIR)/cli/pyneuroctl.py status

samples-stop: ## Stop all running samples
	@echo "⏹️  Stopping all sample applications..."
	@$(PYTHON) $(SRC_DIR)/cli/pyneuroctl.py stop --all

mario-start: ## Start Mario's Pizzeria with full observability stack
	@./mario-docker.sh start

mario-stop: ## Stop Mario's Pizzeria and observability stack
	@./mario-docker.sh stop

mario-restart: ## Restart Mario's Pizzeria and observability stack
	@./mario-docker.sh restart

mario-status: ## Check Mario's Pizzeria and observability stack status
	@./mario-docker.sh status

mario-logs: ## View logs for Mario's Pizzeria and observability stack
	@./mario-docker.sh logs

mario-clean: ## Stop and clean Mario's Pizzeria environment (destructive)
	@./mario-docker.sh clean

mario-reset: ## Complete reset of Mario's Pizzeria environment (destructive)
	@./mario-docker.sh reset

mario-open: ## Open key Mario's Pizzeria services in browser
	@echo "🌐 Opening Mario's Pizzeria services in browser..."
	@open http://localhost:8080 &
	@open http://localhost:3001 &
	@sleep 1
	@echo "✅ Opened Mario's Pizzeria UI and Grafana dashboards"

mario-test-data: ## Generate test data for Mario's Pizzeria observability dashboards
	@echo "🍕 Generating test data for Mario's Pizzeria..."
	@$(POETRY) run python samples/mario-pizzeria/scripts/generate_test_data.py --count 10

mario-clean-orders: ## Remove all order data from Mario's Pizzeria MongoDB
	@./mario-docker.sh clean-orders

mario-create-menu: ## Create default pizza menu in Mario's Pizzeria
	@./mario-docker.sh create-menu

mario-remove-validation: ## Remove MongoDB validation schemas (use app validation only)
	@./mario-docker.sh remove-validation

openbank-start: ## Start OpenBank using CLI
	@$(PYTHON) $(SRC_DIR)/cli/pyneuroctl.py start openbank

openbank-stop: ## Stop OpenBank using CLI
	@$(PYTHON) $(SRC_DIR)/cli/pyneuroctl.py stop openbank

##@ Development Workflows

dev-setup: dev-install setup-path ## Complete development setup
	@echo "🎉 Development environment fully configured!"

dev-test: format lint test-coverage ## Full development testing cycle
	@echo "✅ All development checks passed!"

pre-commit: format-check lint test ## Pre-commit checks
	@echo "✅ Pre-commit checks completed!"

release-prep: clean build test-coverage docs lint ## Prepare for release
	@echo "🚀 Release preparation completed!"

##@ Docker Support

docker-build: ## Build Docker image
	@echo "🐳 Building Docker image..."
	docker build -t neuroglia-python .

docker-run: ## Run application in Docker
	@echo "🐳 Running in Docker..."
	docker-compose -f docker-compose.dev.yml up

docker-dev: ## Start development environment with Docker
	@echo "🐳 Starting development environment..."
	docker-compose -f docker-compose.dev.yml up -d

docker-logs: ## Show Docker container logs
	@echo "📝 Docker container logs:"
	docker-compose -f docker-compose.dev.yml logs -f

docker-stop: ## Stop Docker containers
	@echo "⏹️  Stopping Docker containers..."
	docker-compose -f docker-compose.dev.yml down

##@ Keycloak Management

keycloak-setup: ## Configure Keycloak master realm SSL (run after first startup)
	@echo "🔐 Configuring Keycloak master realm..."
	@sleep 5
	@./deployment/keycloak/configure-master-realm.sh

keycloak-reset: ## Reset Keycloak (removes volume and recreates)
	@echo "🔐 Resetting Keycloak..."
	@docker-compose -f docker-compose.mario.yml down -v
	@sleep 2
	@docker volume ls | grep mario-pizzeria_keycloak_data && docker volume rm -f mario-pizzeria_keycloak_data || echo "Volume already removed"
	@docker-compose -f docker-compose.mario.yml up -d
	@echo "⏳ Waiting for services to start..."
	@sleep 30
	@./deployment/keycloak/configure-master-realm.sh
	@echo "✅ Keycloak reset complete!"

keycloak-verify: ## Verify Keycloak master realm configuration
	@echo "🔍 Checking Keycloak configuration..."
	@docker exec mario-pizzeria-keycloak-1 /opt/keycloak/bin/kcadm.sh get realms/master 2>/dev/null | grep sslRequired || echo "❌ Keycloak not running"

keycloak-logs: ## Show Keycloak container logs
	@echo "📝 Keycloak logs:"
	@docker logs mario-pizzeria-keycloak-1 --tail 50 -f

##@ Utilities

version: ## Show current version
	@echo "📦 Neuroglia Python Framework"
	@$(POETRY) version

deps-check: ## Check for outdated dependencies
	@echo "🔍 Checking for outdated dependencies..."
	$(POETRY) show --outdated

deps-update: ## Update all dependencies
	@echo "⬆️  Updating dependencies..."
	$(POETRY) update

security-check: ## Run security checks
	@echo "🔒 Running security checks..."
	$(POETRY) run safety check

install-hooks: ## Install pre-commit hooks
	@echo "🪝 Installing pre-commit hooks..."
	$(POETRY) run pre-commit install

##@ Quick Commands

all: dev-install pre-commit docs build ## Install, test, document, and build everything
	@echo "🎉 Complete build cycle finished!"

demo: sample-mario-bg ## Start Mario's Pizzeria demo in background
	@echo "🍕 Demo started! Visit http://localhost:8000"
	@echo "📖 API docs at http://localhost:8000/docs"

stop-demo: ## Stop demo application
	@if [ -f $(MARIO_PIZZERIA)/pizza.pid ]; then \
		kill $$(cat $(MARIO_PIZZERIA)/pizza.pid) && rm $(MARIO_PIZZERIA)/pizza.pid; \
		echo "🍕 Demo stopped!"; \
	else \
		echo "❌ No demo running"; \
	fi
