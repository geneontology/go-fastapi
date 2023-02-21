MAKEFLAGS += --warn-undefined-variables
SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := help

all: install start export-requirements

# gunicorn does not accept root-path (api/v1, etc...), but is better at process management
# poetry run gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:80
# note: using root path below means we need a proxy server out front to strip the prefix else, teh docs don't work.
# https://fastapi.tiangolo.com/advanced/behind-a-proxy/
start:
	poetry run gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8080

run:
	start

test: unit-tests integration-tests

integration-tests:
	poetry run pytest tests/integration/step_defs/*.py

unit-tests:
	poetry run pytest tests/unit/*.py

export-requirements:
	poetry export -f requirements.txt --output requirements.txt

install:
	poetry install

help:
	@echo ""
	@echo "make all -- installs requirements, deploys and starts the site locally"
	@echo "make install -- install dependencies"
	@echo "make start -- start the API locally"
	@echo "make test -- runs tests"
	@echo "make help -- show this help"
	@echo ""
