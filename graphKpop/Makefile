HELP_TARGET_COLUMN_WIDTH = 40
COMPOSE_RUN = docker compose run showcase

.PHONY: help
help:
	@grep -E '^[a-zA-Z_/-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-$(HELP_TARGET_COLUMN_WIDTH)s\033[0m %s\n", $$1, $$2}'

.PHONY: init
init: ## init the stack.
	cp ./src/.env.example ./src/.env
	docker compose up -d --build

.PHONY: up
up: ## Creates the docker compose stack.
	docker compose up -d --build
	@echo Neo4j: "http://localhost:7474"
	@echo NeoDash: "http://localhost:5005/graph-kpop/neodash/"

.PHONY: up_showcase
up_showcase: ## Creates the docker compose stack.
	docker compose up -d --build showcase

.PHONY: down
down: ## Deletes the docker compose stack. Your local environment will no longer be accessible.
	docker compose down

.PHONY: ps
ps: ## Creates the docker compose stack.
	docker compose ps

.PHONY: logs
logs: ## Displays logs the graph-kpop container.
	docker compose logs -f graph-kpop

.PHONY: db_clean
db_clean: ## Removes every nodes and relationships in Neo4j
	${COMPOSE_RUN} python3 /showcase/src/bin/cleanDB.py

.PHONY: reset_data
reset_data: db_clean up_showcase ## Cleans the db, loads fixtures and load showcase data

# Other shenanigans such as linters
.PHONY: linters
linters: lint_black lint_flake8 lint_mypy lint_pylint ## Runs all linters.

.PHONY: lint_flake8
lint_flake8: ## Runs flake8.
	${COMPOSE_RUN} flake8 ./src --count || exit 0

.PHONY: lint_mypy
lint_mypy: ## Runs mypy.
	${COMPOSE_RUN} mypy --install-types --non-interactive --check-untyped-defs ./src || exit 0

.PHONY: lint_black
lint_black: ## Uses black to format your code.
	${COMPOSE_RUN} black ./src/ || exit 0

.PHONY: lint_pylint
lint_pylint: ## Runs pylint.
	${COMPOSE_RUN} pylint --output-format=text ./src || exit 0