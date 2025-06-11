.PHONY: help install dev-install lint format test test-cov clean docker-up docker-down start-system

help:
	@echo "BoarderframeOS Development Commands"
	@echo "=================================="
	@echo "make install      - Install production dependencies"
	@echo "make dev-install  - Install development dependencies"
	@echo "make lint        - Run linting checks"
	@echo "make format      - Auto-format code"
	@echo "make test        - Run tests"
	@echo "make test-cov    - Run tests with coverage"
	@echo "make clean       - Clean cache files"
	@echo "make docker-up   - Start Docker services"
	@echo "make docker-down - Stop Docker services"
	@echo "make start-system - Start complete BoarderframeOS"

install:
	pip install -r requirements.txt

dev-install: install
	pip install pre-commit pytest pytest-asyncio pytest-cov black isort mypy flake8 bandit
	pre-commit install

lint:
	black --check .
	isort --check-only .
	flake8 . --max-line-length=88 --extend-ignore=E203,W503
	mypy . --ignore-missing-imports
	bandit -r . -ll --skip B101,B601

format:
	black .
	isort .

test:
	pytest

test-cov:
	pytest --cov=. --cov-report=html --cov-report=term

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info

docker-up:
	docker-compose up -d postgresql redis

docker-down:
	docker-compose down

start-system: docker-up
	python startup.py
