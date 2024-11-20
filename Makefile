MAKEFLAGS += --warn-undefined-variables
SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := help

all: install start export-requirements

dev: install start-dev

# gunicorn does not accept root-path (api/v1, etc...), but is better at process management
# poetry run gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:80
# note: using root path below means we need a proxy server out front to strip the prefix else, teh docs don't work.
# https://fastapi.tiangolo.com/advanced/behind-a-proxy/
start:
	poetry run gunicorn app.main:app --workers 4 --timeout 120 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8080 --log-level info --access-logfile combined_access_error.log --error-logfile combined_access_error.log --capture-output

start-dev:
	poetry run gunicorn app.main:app --workers 4 --timeout 120 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8081 --log-level info --access-logfile combined_access_error.log --error-logfile combined_access_error.log --capture-output

test: unit-tests integration-tests lint spell

integration-tests:
	poetry run pytest tests/integration/step_defs/*.py

lint:
	poetry run tox -e flake8
	poetry run tox -e lint-fix

spell:
	poetry run tox -e codespell

unit-tests:
	poetry run pytest tests/unit/*.py

export-requirements:
	poetry export -f requirements.txt --output requirements.txt

install:
	poetry install

help:
	@echo "##################################################################################################"
	@echo "make all -- installs requirements, deploys and starts the site locally"
	@echo "make install -- install dependencies"
	@echo "make start -- start the API locally"
	@echo "make test -- runs tests, linter in fix mode, and spell checker"
	@echo "make lint -- runs linter in fix mode"
	@echo "make spell -- runs spell checker"
	@echo "make help -- show this help"
	@echo "make start -- start the API locally at localhost:8080/docs (takes about 10 seconds to start)"
	@echo "make start-dev -- start the API locally at localhost:8081/docs (takes about 10 seconds to start)"
	@echo "##################################################################################################"
