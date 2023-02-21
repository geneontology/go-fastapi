## Prerequisites:

 * [install poetry](https://python-poetry.org/docs/)

### Example Deployment Locally:

1) clone the repo
`git clone https://github.com/geneontology/go-fastapi`
2) install requirements into a virtual environment 
`poetry install`
3) start the API server
`make start`
4) run the tests 
`make test`

### Alternate development environment - Using Docker

1) build the docker image
```bash
docker build -t go_fastapi .
```
2) run the docker image interactively
```bash
docker run -i -t --name go-fastapi -p 8000:8000 -p 8080:8080 go-fastapi bash
```

3) running the container with parameters above will override the default CMD in the Dockerfile
`make start` in the docker container will start the API server and by exposing 8080, the API on the
container can be accessed locally via: http://127.0.0.1:8080/docs
