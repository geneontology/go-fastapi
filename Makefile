
start:
	poetry run gunicorn go_fastapi.app:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:80

test: unit-tests

unit-tests:
	poetry run pytest tests/*.py

install:
	poetry install
	poetry shell
