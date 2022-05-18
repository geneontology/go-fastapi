MAKEFLAGS += --warn-undefined-variables
SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := help

all: install start

start:
	poetry run gunicorn go_fastapi.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:80

test: unit-tests

unit-tests:
	poetry run pytest tests/*.py

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
