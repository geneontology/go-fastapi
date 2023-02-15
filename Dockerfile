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
COPY pyproject.toml poetry.lock README.md .
COPY ./.git /.git
COPY app app/
COPY static static/
EXPOSE 8080 8000
RUN poetry build

CMD ["/bin/bash"]

#######################################
# FROM builder as runner
#
# RUN useradd --create-home gofastapiuser
# WORKDIR /home/gofastapiuser
# USER gofastapiuser
# ENV PATH="${PATH}:/home/gofastapiuser/.local/bin"
# COPY --from=builder /code/dist/*.whl /tmp
# RUN pip3 install --user /tmp/*.whl

# CMD ["make start"]

# to build these images:
# from the go-fastapi directory checkout
# docker build --no-cache -f Dockerfile --tag geneontology/go-fastapi:latest .