###############################################
# Base Image
###############################################
FROM ubuntu:latest as builder

# https://stackoverflow.com/questions/53835198/integrating-python-poetry-with-docker
ENV PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100 \
  POETRY_VERSION=1.2.1

# Install Poetry
RUN apt-get update && apt-get install -y curl git python3-pip python3 python3.10-venv nano make
RUN python3 -m pip install "poetry==$POETRY_VERSION"
RUN poetry self add "poetry-dynamic-versioning[plugin]"
WORKDIR /code
COPY Makefile pyproject.toml poetry.lock README.md .
COPY ./.git /.git
COPY app app/
COPY static static/
EXPOSE 8000 8080
RUN poetry install

# CMD runs by default when no other commands are passed to a docker run directive from the command line.
CMD ["make start"]



