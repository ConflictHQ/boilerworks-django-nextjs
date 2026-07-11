COMPOSE = docker compose -f docker/docker-compose.yaml
CONTAINER = boilerworks-local

.PHONY: help up down build restart logs logs-worker logs-beat shell manage migrate migrations seed reindex test lint schema collectstatic superuser ps navegador-ingest brain check-brain

help:
	@echo "Available commands:"
	@echo "  up            Start the stack in detached mode"
	@echo "  down          Stop the stack"
	@echo "  build         Build and start the stack"
	@echo "  restart       Restart the boilerworks-local container"
	@echo "  logs          Tail logs for boilerworks-local"
	@echo "  logs-worker   Tail logs for celery-worker"
	@echo "  logs-beat     Tail logs for celery-beat"
	@echo "  shell         Open a bash shell in boilerworks-local"
	@echo "  manage        Run a manage.py command: make manage cmd=<command>"
	@echo "  migrate       Run database migrations"
	@echo "  migrations    Create new migrations"
	@echo "  seed          Load dev seed fixtures (add flush=1 to truncate first)"
	@echo "  reindex       Rebuild OpenSearch indices from the database"
	@echo "  test          Run tests"
	@echo "  lint          Run flake8 + isort checks"
	@echo "  schema        Export GraphQL SDL to static/gql/schema.graphql"
	@echo "  collectstatic Collect static files"
	@echo "  superuser     Create a Django superuser"
	@echo "  ps            Show running containers"
	@echo "  navegador-ingest  Build the code KG (.navegador/graph.db) and export app/code-kg.json"
	@echo "  brain         Compile the brain node envelope app/brain.json (committed)"
	@echo "  check-brain   Validate app/brain.json against schemas/ (jsonschema) + freshness"

up:
	$(COMPOSE) up -d

down:
	$(COMPOSE) down

build:
	$(COMPOSE) up -d --build

restart:
	docker restart $(CONTAINER)

logs:
	$(COMPOSE) logs -f $(CONTAINER)

logs-worker:
	$(COMPOSE) logs -f celery-worker

logs-beat:
	$(COMPOSE) logs -f celery-beat

shell:
	docker exec -it $(CONTAINER) bash

manage:
	docker exec -it $(CONTAINER) python manage.py $(cmd)

migrate:
	docker exec $(CONTAINER) python manage.py migrate

migrations:
	docker exec $(CONTAINER) python manage.py makemigrations

seed:
	docker exec $(CONTAINER) python manage.py seed $(if $(flush),--flush,)

reindex:
	docker exec $(CONTAINER) python manage.py opensearch_index --rebuild

test:
	docker exec $(CONTAINER) python manage.py test

lint:
	docker exec $(CONTAINER) python -m flake8 --max-line-length=140
	docker exec $(CONTAINER) python -m isort --check-only .

schema:
	docker exec $(CONTAINER) python manage.py shell -c "from config.schema import schema; open('static/gql/schema.graphql','w').write(schema.as_str()); print('Schema exported')"

collectstatic:
	docker exec $(CONTAINER) python manage.py collectstatic --noinput

superuser:
	docker exec -it $(CONTAINER) python manage.py createsuperuser

ps:
	$(COMPOSE) ps

# --- Navegador + brain node (see bootstrap.md "Process & brain") -------------

navegador-ingest:  ## Ingest code into the Navegador graph, enrich for Django, export conflict-kg/v1
	navegador ingest .
	navegador enrich --framework django
	navegador export --format conflict-kg app/code-kg.json

brain:  ## Compile the brain node envelope (deterministic, committed)
	python3 scripts/gen_brain_node.py

check-brain:  ## Validate app/brain.json against schemas/ + freshness (needs: pip install jsonschema)
	python3 scripts/validate_brain.py
