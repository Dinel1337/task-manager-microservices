.PHONY: help install run docker-build docker-up docker-down docker-logs clean test

help:
	@echo "Available commands:"
	@echo "  make install       - Install dependencies"
	@echo "  make run           - Run the service locally"
	@echo "  make docker-build  - Build Docker image"
	@echo "  make docker-up     - Start services with docker-compose"
	@echo "  make docker-down   - Stop services"
	@echo "  make docker-logs   - View logs"
	@echo "  make clean         - Clean cache and temp files"
	@echo "  make test          - Run tests"

install:
	pip install -r requirements.txt

run:
	python -m analytics_service.main

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +

test:
	pytest tests/ -v
