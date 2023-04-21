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

Note: tests will run with or without a functioning server locally.

### Alternate development environment - Using Docker

1) build the docker image
```bash
docker build -t geneontology/go-fastapi .
```
2) run the docker image

`-d` tells docker to run the image in the background (the image includes a command to start the API), so this
will run the image and start the API server but give the control of the terminal back to the local user.

`-p` tells docker to map the container port 8080 to the host port 8080.  This way the user can access the API docker
version of the running API from their local browser via: http://127.0.0.1:8080/docs

```bash
docker run -d -p 8080:8080 --name go-fastapi geneontology/go-fastapi
```

### Deploying a change in the API code to docker image:
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
docker build -t geneontology/go-fastapi .
```
5) test the rebuilt docker image
```bash
docker run -i -t --name geneontology/go-fastapi -p 8080:8080 geneontology/go-fastapi bash
make start
make test
```

### Deploying a change in the API code to docker image on AWS:

1) ssh into the AWS instance running the docker container, invade the image and git pull the changes
total downtime for this process is about 5 minutes! 
```bash
ssh -i [path/to/pem/key/locally] ubuntu@[aws.instance.public.ip.address]
sudo docker stop geneontology/go-fastapi
sudo docker rm geneontology/go-fastapi
sudo docker image rm geneontology/go-fastapi
cd go-fastapi
git pull 
sudo docker build -t geneontology/go-fastapi .
sudo docker run -d -p 8080:8080 geneontology/go-fastapi
```

### Restarting the API server on AWS manually:
2) stop the running api from inside the docker container
```bash
sudo pkill gunicorn
```
this will stop the running docker container and push you back into the AWS instance itself.

3) restart the image 
This automatically restarts the API server by running `make start` in the docker container.
```bash
docker run -d -p 8080:8080 geneontology/go-fastapi
```

### Pushing to Dockerhub

GitHub Actions will automatically build and push the docker image to Dockerhub when a new versioned tag is created.
To do this manually, run the following commands, replacing [tag_name] with the tag or version number:

```bash
docker login
docker build -t geneontology/go-fastapi .
docker tag geneontology/go-fastapi:latest geneontology/go-fastapi:[tag_name]
docker push geneontology/go-fastapi:[tag_name]
```

### Deploying to AWS/production

1) create a go-fastapi release using the GitHub UI and semantic versioning.
2) wait for the GitHub action to build and push the docker image to Dockerhub.
3) ssh into the AWS instance running the docker container, pull the new image and restart the container.
```bash
ssh -i [path/to/pem/key/locally] ubuntu@[aws.instance.public.ip.address]
sudo docker pull geneontology/go-fastapi:latest
sudo docker stop geneontology/go-fastapi
sudo docker rm geneontology/go-fastapi
sudo docker run -d -p 8080:8080 geneontology/go-fastapi
```
