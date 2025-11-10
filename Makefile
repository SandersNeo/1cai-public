# Makefile for Enterprise 1C AI Development Stack
# Quick commands for common tasks

.PHONY: help install test docker-up docker-down migrate clean train-ml eval-ml train-ml-demo eval-ml-demo scrape-its render-uml render-uml-svg adr-new test-bsl export-context generate-docs bsl-ls-up bsl-ls-down bsl-ls-logs

CONFIG ?= ERPCPM
EPOCHS ?=
LIMIT ?= 20
BASE_MODEL ?=
ITS_START_URL ?= https://its.1c.ru/db/cabinetdoc
ITS_OUTPUT ?= output/its-scraper
ITS_FORMATS ?= json markdown
ITS_CONCURRENCY ?=
ITS_SLEEP ?=
ITS_PROXY ?=
ITS_USER_AGENT_FILE ?=

help:
	@echo "Enterprise 1C AI Development Stack - Commands:"
	@echo ""
	@echo "Setup:"
	@echo "  make install          - Install Python dependencies"
	@echo "  make install-dev      - Install dev dependencies + main"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-up        - Start all Docker services"
	@echo "  make docker-down      - Stop all Docker services"
	@echo "  make docker-logs      - View Docker logs"
	@echo "  make docker-clean     - Remove all Docker volumes (⚠️  deletes data!)"
	@echo "  make bsl-ls-up        - Start the bsl-language-server (docker-compose.dev.yml)"
	@echo "  make bsl-ls-down      - Stop the bsl-language-server"
	@echo "  make bsl-ls-logs      - Tail logs from bsl-language-server"
	@echo "  make bsl-ls-check     - Run health/parse check against bsl-language-server"
	@echo ""
	@echo "Migration:"
	@echo "  make migrate          - Run all migrations (JSON→PG→Neo4j→Qdrant)"
	@echo "  make migrate-pg       - Migrate JSON to PostgreSQL"
	@echo "  make migrate-neo4j    - Migrate PostgreSQL to Neo4j"
	@echo "  make migrate-qdrant   - Migrate to Qdrant (vectorization)"
	@echo ""
	@echo "Testing:"
	@echo "  make test             - Run all tests"
	@echo "  make test-unit        - Run unit tests only"
	@echo "  make test-integration - Run integration tests"
	@echo "  make coverage         - Run tests with coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  make format           - Format code (black + isort)"
	@echo "  make lint             - Run linters (flake8 + mypy)"
	@echo "  make quality          - Run all quality checks"
	@echo ""
	@echo "API:"
	@echo "  make api              - Start Graph API server"
	@echo "  make mcp              - Start MCP server"
	@echo "  make servers          - Start both API servers"
	@echo ""
	@echo "EDT Plugin:"
	@echo "  make plugin-build     - Build EDT plugin"
	@echo "  make plugin-install   - Build and install to EDT"
	@echo ""
	@echo "AI Models:"
	@echo "  make ollama-pull      - Download Qwen3-Coder model"
	@echo "  make ollama-list      - List installed models"
	@echo ""
	@echo "ML:"
	@echo "  make train-ml         - Train neural pipeline (CONFIG=$(CONFIG), EPOCHS=$(if $(EPOCHS),$(EPOCHS),default))"
	@echo "  make eval-ml          - Evaluate dataset (CONFIG=$(CONFIG), LIMIT=$(LIMIT))"
	@echo ""
	@echo "ML Demos:"
	@echo "  make train-ml-demo    - Run demo training preset (DEMO)"
	@echo "  make eval-ml-demo     - Evaluate demo preset (DEMO)"
	@echo ""
	@echo "Utilities:"
	@echo "  make status           - Show project status"
	@echo "  make clean            - Clean temporary files"
	@echo "  make scrape-its       - Run ITS scraper (ITS_START_URL, ITS_OUTPUT, ITS_FORMATS, ITS_CONCURRENCY, ITS_SLEEP, ITS_PROXY, ITS_USER_AGENT_FILE)"
	@echo "  make render-uml       - Render all PlantUML diagrams to PNG"
	@echo "  make render-uml-svg   - Render PlantUML diagrams to PNG + SVG"
	@echo "  make adr-new SLUG=... - Create a new Architecture Decision Record"
	@echo "  make test-bsl         - Run BSL/YAxUnit test suites (see tests/bsl/testplan.json)"
	@echo "  make export-context   - Export platform context via platform-context-exporter (see ADR-0005)"
	@echo "  make generate-docs    - Generate documentation via ones_doc_gen (see ADR-0005)"

# Installation
install:
	pip install -r requirements.txt
	pip install -r requirements-stage1.txt

install-dev:
	pip install -r requirements.txt
	pip install -r requirements-stage1.txt
	pip install -r requirements-dev.txt

# Docker
docker-up:
	docker-compose -f docker-compose.yml -f docker-compose.stage1.yml up -d
	@echo "Waiting for services to start..."
	@sleep 10
	docker-compose ps

docker-down:
	docker-compose -f docker-compose.yml -f docker-compose.stage1.yml down

docker-logs:
	docker-compose -f docker-compose.yml -f docker-compose.stage1.yml logs -f

docker-clean:
	docker-compose -f docker-compose.yml -f docker-compose.stage1.yml down -v
	@echo "⚠️  All data deleted!"

# bsl-language-server helpers
bsl-ls-up:
	docker-compose -f docker-compose.dev.yml up -d bsl-language-server

bsl-ls-down:
	docker-compose -f docker-compose.dev.yml stop bsl-language-server

bsl-ls-logs:
	docker-compose -f docker-compose.dev.yml logs -f bsl-language-server

bsl-ls-check:
	python scripts/parsers/check_bsl_language_server.py

# Migration
migrate: migrate-pg migrate-neo4j migrate-qdrant

migrate-pg:
	python migrate_json_to_postgres.py

migrate-neo4j:
	python migrate_postgres_to_neo4j.py

migrate-qdrant:
	python migrate_to_qdrant.py

# Testing
test:
	pytest

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v -m integration

coverage:
	pytest --cov=src --cov-report=html --cov-report=term
	@echo "Coverage report: htmlcov/index.html"

# Code Quality
format:
	black src/ tests/
	isort src/ tests/

lint:
	flake8 src/ tests/ --max-line-length=120
	mypy src/ --ignore-missing-imports

quality: format lint test

# API Servers
api:
	python -m uvicorn src.api.graph_api:app --host 0.0.0.0 --port 8080 --reload

mcp:
	python -m uvicorn src.ai.mcp_server:app --host 0.0.0.0 --port 6001 --reload

servers:
	@echo "Starting API servers in background..."
	python -m uvicorn src.api.graph_api:app --host 0.0.0.0 --port 8080 &
	python -m uvicorn src.ai.mcp_server:app --host 0.0.0.0 --port 6001 &

# EDT Plugin
plugin-build:
	cd edt-plugin && mvn clean package

plugin-install: plugin-build
	@echo "Install manually: Help → Install New Software → Local → edt-plugin/target/repository"

# AI Models
ollama-pull:
	docker-compose exec ollama ollama pull qwen2.5-coder:7b

ollama-pull-large:
	docker-compose exec ollama ollama pull qwen2.5-coder:32b

ollama-list:
	docker-compose exec ollama ollama list

# Utilities
status:
	@echo "=== Docker Services ==="
	@docker-compose ps
	@echo ""
	@echo "=== PostgreSQL ==="
	@docker-compose exec postgres pg_isready -U admin || echo "Not running"
	@echo ""
	@echo "=== Neo4j ==="
	@curl -s http://localhost:7474 > /dev/null && echo "✓ Running" || echo "✗ Not running"
	@echo ""
	@echo "=== Qdrant ==="
	@curl -s http://localhost:6333/readyz > /dev/null && echo "✓ Running" || echo "✗ Not running"

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete
	rm -rf htmlcov/ coverage.xml .coverage
	@echo "✓ Cleaned temporary files"

scrape-its:
	python -m integrations.its_scraper scrape $(ITS_START_URL) --output $(ITS_OUTPUT) $(foreach fmt,$(ITS_FORMATS), --format $(fmt)) $(if $(ITS_CONCURRENCY), --concurrency $(ITS_CONCURRENCY),) $(if $(ITS_SLEEP), --sleep $(ITS_SLEEP),) $(if $(ITS_PROXY), --proxy $(ITS_PROXY),) $(if $(ITS_USER_AGENT_FILE), --user-agent-file $(ITS_USER_AGENT_FILE),)

render-uml:
	python scripts/docs/render_uml.py --fail-on-missing

render-uml-svg:
	python scripts/docs/render_uml.py --format png --format svg --fail-on-missing

adr-new:
ifndef SLUG
	$(error "Usage: make adr-new SLUG=my-decision")
endif
	python scripts/docs/create_adr.py $(SLUG)

test-bsl:
	python scripts/tests/run_bsl_tests.py

export-context:
	python scripts/context/export_platform_context.py

generate-docs:
	python scripts/context/generate_docs.py

train-ml:
	@python scripts/ml/config_utils.py --info $(CONFIG)
	python scripts/run_neural_training.py $(if $(EPOCHS),--epochs $(EPOCHS),)

eval-ml:
	python scripts/eval/eval_model.py --config-name $(CONFIG) --limit $(LIMIT)

train-ml-demo:
	$(MAKE) train-ml CONFIG=DEMO EPOCHS=1

eval-ml-demo:
	$(MAKE) eval-ml CONFIG=DEMO LIMIT=10
