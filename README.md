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
docker build -t go-fastapi .
```
2) run the docker image

`-d` tells docker to run the image in the background (the image includes a command to start the API), so this
will run the image and start the API server but give the control of the terminal back to the local user.

`-p` tells docker to map the container port 8080 to the host port 8080.  This way the user can access the API docker
version of the running API from their local browser via: http://127.0.0.1:8080/docs

```bash
docker run -d -p 8080:8080 go-fastapi
```

### Deploying a change in the API code:
To remove images and containers:
`docker rm -vf $(docker ps -aq)` (removes all local images)
`docker rmi -f $(docker images -aq)` (removes all local containers)

Check the port mapping:
`docker port go-fastapi` (see the port mapping)

1) checkout and build the API code locally

This should result in a locally running API server on port 8081 (note the port difference from the docker version)

```bash
git clone https://github.com/geneontology/go-fastapi
cd go-fastapi
make dev
```
localhost:8081/docs will be available for testing the API locally if the commands above are successful.

2) make a change to the API code
3) test the API changes
```bash
make test
```
4) rebuild the docker image with the changed code
```bash
docker build -t go-fastapi .
```
5) test the rebuilt docker image
```bash
docker run -i -t --name go-fastapi -p 8000:8000 -p 8080:8080 go-fastapi bash
make start
make test
```