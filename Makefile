.PHONY: help install dev test clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .pytest_cache
	rm -rf .mypy_cache

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

migrate:
	alembic upgrade head

createsuperuser:
	python main.py createsuperuser

format:
	black app/ tests/
	isort app/ tests/

lint:
	flake8 app/ tests/
	mypy app/ docker-up docker-down

help:
	@echo "Available commands:"
	@echo "  make install    - Install dependencies"
	@echo "  make dev       - Run development server"
	@echo "  make test      - Run tests"
	@echo "  make clean     - Clean cache files"
	@echo "  make docker-up - Start Docker containers"
	@echo "  make docker-down - Stop Docker containers"

install:
	pip install -r requirements.txt
	cp .env.example .env
	python main.py initdb

dev:
	python main.py

test:
	pytest tests/ -v

clean
