# GetGSA Makefile

.PHONY: help install run test clean setup

help: ## Show this help message
	@echo "GetGSA - GSA Onboarding Assistant"
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	cd backend && uv pip install -r requirements.txt

install-dev: ## Install development dependencies
	cd backend && uv pip install -r requirements.txt
	cd backend && uv pip install pytest pytest-asyncio black flake8

setup: ## Initial setup (copy env file)
	cd backend && cp .env.example .env
	@echo "Please edit backend/.env with your OpenAI API key"

run: ## Run the backend server
	cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test: ## Run all tests
	cd backend && uv run pytest tests/ -v
	cd tests && uv run pytest integration_tests.py -v

test-unit: ## Run unit tests only
	cd backend && uv run pytest tests/ -v

test-integration: ## Run integration tests only
	cd tests && uv run pytest integration_tests.py -v

lint: ## Run linting
	cd backend && uv run flake8 app/ --max-line-length=100
	cd backend && uv run black app/ --check

format: ## Format code
	cd backend && uv run black app/ --line-length=100

clean: ## Clean up generated files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf backend/.pytest_cache
	rm -rf tests/.pytest_cache

dev-setup: install-dev setup ## Complete development setup
	@echo "Development environment ready!"
	@echo "1. Edit backend/.env with your OpenAI API key"
	@echo "2. Run 'make run' to start the server"
	@echo "3. Open frontend/index.html in your browser"

docker-build: ## Build Docker image
	docker build -t getgsa .

docker-run: ## Run in Docker
	docker run -p 8000:8000 --env-file backend/.env getgsa
