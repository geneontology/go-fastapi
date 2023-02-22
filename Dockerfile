###############################################
# Base Image
###############################################
FROM ubuntu:20.04 as builder

# https://stackoverflow.com/questions/53835198/integrating-python-poetry-with-docker
ENV PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100 \
  POETRY_VERSION=1.3.2 \
  DEBIAN_FRONTEND=noninteractive

# PYTHONFAULTHANDLER - https://docs.python.org/3/using/cmdline.html#envvar-PYTHONFAULTHANDLER
# PYTHONUNBUFFERED - send output straight to the terminal without hiding in the buffer
# PYTHONHASHSEED - a random value is used to seed the hashes of str and bytes objects, to prevent attackers from tar-pitting your application by sending you keys designed to collide
# PIP_NO_CACHE_DIR - cache the pip whl and tar files to speed up builder
# PIP_DISABLE_PIP_VERSION_CHECK - avoid warning that pip is out of date


# Install Poetry
RUN apt-get update && apt-get install -y curl git python3-pip python3 python3.9-venv nano make
RUN python3 -m pip install "poetry==$POETRY_VERSION"
# RUN poetry self add "poetry-dynamic-versioning[plugin]"
WORKDIR /code
COPY Makefile pyproject.toml poetry.lock README.md .
COPY ./.git /.git
COPY app app/
COPY static static/
EXPOSE 8000 8080
RUN poetry install

# CMD runs by default when no other commands are passed to a docker run directive from the command line.
CMD ["make start"]



