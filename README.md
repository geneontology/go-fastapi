## Prerequisites:

 * [install poetry](https://python-poetry.org/docs/)

### Example Deployment Locally:

```bash
git clone https://github.com/sierra-moxon/go-fastapi
pip install poetry
make all
```

### Alternate development environment - Using Docker

1) install docker
2) build the docker image
```bash
docker build -t go_fastapi .
```
3) run the docker image
```bash
docker run -t -d --name go_fastapi go_fastapi
```
4) invade the running container
```bash
docker exec -it go_fastapi /bin/bash
```
5) clone the repo
```bash
git clone https://github.com/alliance-genome/agr_curation_schema
cd agr_curation_schema
git checkout my_branch_to_run_tests
```
6) install the project
```bash
poetry install
```
7) run the tests
```bash
make test
```