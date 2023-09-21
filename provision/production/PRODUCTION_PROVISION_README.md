# go-fastapi Deployment

This guide describes the deployment of the `go-fastapi` stack to AWS using Terraform, ansible, and the "go-deploy" Python library. 

## Prerequisites: 
**NOTE**: we have a docker-based environment with all these tools installed. 

#### software:

- go-fastapi checkout 
- Terraform: v1.1.4
- Ansible: 2.10.7
- aws cli
- go-deploy; multple install methods: poetry `poetry install go-deploy==0.4.2` (requires python >=3.8), can also be installed incidentally from go-fastapi repo with `poetry install`

#### configuration files:

  - vars.yaml
  - docker-vars.yaml
  - s3-vars.yaml
  - ssl-vars.yaml
  - qos-vars.yaml
  - stage.yaml
  - start_services.yaml

#### artifacts that will created/deployed to a staging directory on AWS later on:

  - s3 credentials files (used to push Apache logs and pull ssl credentials from the associated s3 bucket)
  - qos.conf and robots.txt (used for Apache mitigation)
  - docker-production-compose.yaml
  - various configuration files

#### DNS: 

DNS records are used for `go-fastapi`; they are typically the "production" record and the dev/testing record. Yhe go-deploy tool allows for creating DNS records (type A) that would be populated by the public ip addresses of the aws instance. If you don't use this option, you would need to point this record to the elastic IP of the VM. For testing purposes, you can use: `aes-test-go-fastapi.geneontology.org` or any other record that you create in Route 53.

**NOTE**: If using cloudflare, you would need to point the cloudflare dns record to the elastic IP.

#### SSH Keys:

For testing purposes you can you your own ssh keys. But for production please ask for the go ssh keys.
/tmp/go-ssh.pub
/tmp/go-ssh

## Configuring and deploying EC2 _instances_: 

This is all completed in a dockerized development environment (all commands take place inside the docker container).

1. Spin up the provided dockerized development environment:

```bash
docker run --name go-dev -it geneontology/go-devops-base:tools-jammy-0.4.1  /bin/bash
git clone https://github.com/geneontology/go-fastapi.git
cd go-fastapi/provision
```

2. Prepare AWS credentials:

The credentials are used by Terraform to provision the AWS instance and by the provisioned instance to access the certificate store and the s3 buckets used to store Apache logs.  Copy and modify the aws credential file to the default location `/tmp/go-aws-credentials` 

**NOTE**: you will need to supply an `aws_access_key_id` and `aws_secret_access_key`. These will be marked with `REPLACE_ME` in the `go-aws-credentials.sample` file.

```bash
cp production/go-aws-credentials.sample /tmp/go-aws-credentials
emacs /tmp/go-aws-credentials  # update the `aws_access_key_id` and `aws_secret_access_key`
```

3. Prepare and initialize the S3 Terraform backend:

"Initializing" a Terraform backend means that you are getting ready to save a bundle of EC2 and networking states to S3, so that you and other developers in the future can discover and manipulate these states in the future, bringing servers and services up and down in a coordinated way. These terraform backends are an arbitrary bundle and can be grouped as needed. In general, the production systems should all use a coordinated set, but you may create new ones for experimentation, etc. If you are trying to work with an already set state, jump to `4`; if you are experimenting, continue here with `3`.

```bash

# The S3 backend is used to store the terraform state.
cp ./production/backend.tf.sample ./aws/backend.tf

# replace the REPLACE_ME_GOAPI_S3_STATE_STORE with the appropriate backend
emacs ./aws/backend.tf

# Use the AWS cli to make sure you have access to the terraform s3 backend bucket
export AWS_SHARED_CREDENTIALS_FILE=/tmp/go-aws-credentials

# S3 bucket
aws s3 ls s3://REPLACE_ME_GOAPI_S3_STATE_STORE

# initialize (if it doesn't work, we fail):
go-deploy -init --working-directory aws -verbose

# Use these commands to figure out the name of an existing workspace if any. The name should have a pattern `production-YYYY-MM-DD`
go-deploy --working-directory aws -list-workspaces -verbose 
```

4. Provision instance on AWS:

If a workspace exists above, then you can skip the provisioning of the AWS instance.  
Else, create a workspace using the following namespace pattern `production-YYYY-MM-DD`.  e.g.: `production-2023-01-30`

```bash
# copy `production/config-instance.yaml.sample` to another location and modify using emacs.

cp ./production/config-instance.yaml.sample config-instance.yaml
emacs config-instance.yaml  # verify the location of the ssh keys for your AWS instance in your copy of `config-instance.yaml` under `ssh_keys`.
                            # verify the location of the public ssh key in `aws/main.tf`

```

5. test the deployment
```bash
go-deploy --workspace REPLACE_ME_WITH_TERRAFORM_BACKEND --working-directory aws -verbose -dry-run --conf config-instance.yaml
```

7. deploy if all looks good.
```bash
go-deploy --workspace REPLACE_ME_WITH_TERRAFORM_BACKEND --working-directory aws -verbose --conf config-instance.yaml
# display the terraform state. The aws resources that were created.
go-deploy --workspace REPLACE_ME_WITH_TERRAFORM_BACKEND --working-directory aws -verbose -show
# display the public ip address of the aws instance
go-deploy --workspace REPLACE_ME_WITH_TERRAFORM_BACKEND --working-directory aws -verbose -output
```

Useful Details for troubleshooting:
This will produce an IP address in the resulting inventory.json file.
The previous command creates a terraform tfvars. These variables override the variables in `aws/main.tf`

**NOTE**: write down the IP address of the AWS instance that is created.

This can be found in `REPLACE_ME_WITH_TERRAFORM_BACKEND.cfg`  (e.g. production-YYYY-MM-DD.cfg, sm-test-go-fastapi-alias.cfg)
If you need to check what you have just done, here are some helpful Terraform commands:

```bash
cat REPLACE_ME_WITH_TERRAFORM_BACKEND.tfvars.json # e.g, production-YYYY-MM-DD.tfvars.json, sm-test-go-fastapi-alias.tfvars.json
```

The previous command creates an ansible inventory file.
```bash
cat REPLACE_ME_WITH_TERRAFORM_BACKEND-inventory.cfg  # e.g, production-YYYY-MM-DD-inventory, sm-test-go-fastapi-alias-inventory
```

Useful terraform commands to check what you have just done

```bash
terraform -chdir=aws workspace show   # current terraform workspace
terraform -chdir=aws show             # current state deployed ...
terraform -chdir=aws output           # shows public ip of aws instance 
```

## Configuring and deploying software (go-fastapi) _stack_:
These commands continue to be run in the dockerized development environment.

* Make DNS names for go-fastapi point to the public IP address. If using cloudflare, put the ip in cloudflare DNS record. Otherwise put the ip in the AWS Route 53 DNS record. 
* Location of SSH keys may need to be replaced after copying config-stack.yaml.sample
* s3 credentials are placed in a file using the format described above
* s3 uri if SSL is enabled. Location of SSL certs/key
* QoS mitigation if QoS is enabled
* Use the same workspace name as in the previous step

```bash
cp ./production/config-stack.yaml.sample ./config-stack.yaml
emacs ./config-stack.yaml    # MAKE SURE TO CHANGE THE GO-FASTAPI TAG (strip the v), also replace all the REPLACE_MEs
export ANSIBLE_HOST_KEY_CHECKING=False
````

**NOTE**: change the command below to point to the terraform workspace you use above. 
go-deploy --workspace REPLACE_ME_WITH_TERRAFORM_BACKEND --working-directory aws -verbose --conf config-stack.yaml

```bash
go-deploy --workspace REPLACE_ME_WITH_TERRAFORM_BACKEND --working-directory aws -verbose --conf config-stack.yaml
```


## Testing deployment:

1. Access go-fastapi from the command line by ssh'ing into the newly provisioned EC2 instance (this too is run via the dockerized dev environment):
ssh -i /tmp/go-ssh ubuntu@IP_ADDRESS

2. Access go-fastapi from a browser:

We use health checks in the `docker-compose` file.  
Use go-fastapi DNS name. http://{go-fastapi_host}/docs

3. Debugging:

* Use -dry-run and copy and paste the command and execute it manually
* ssh to the machine; the username is ubuntu. Try using DNS names to make sure they are fine.

```bash
docker-compose -f stage_dir/docker-compose.yaml ps
docker-compose -f stage_dir/docker-compose.yaml down # whenever you make any changes 
docker-compose -f stage_dir/docker-compose.yaml up -d
docker-compose -f stage_dir/docker-compose.yaml logs -f 
```

4. Testing LogRotate:

```bash
docker exec -u 0 -it apache_fastapi bash # enter the container
cat /opt/credentials/s3cfg

echo $S3_BUCKET
aws s3 ls s3://$S3_BUCKET
logrotate -v -f /etc/logrotate.d/apache2 # Use -f option to force log rotation.
cat /tmp/logrotate-to-s3.log # make sure uploading to s3 was fine
```

5. Testing Health Check:

```sh
docker inspect --format "{{json .State.Health }}" go-fastapi
```


### Destroy Instance and Delete Workspace:

```bash
# Destroy Using Tool.
# Make sure you point to the correct workspace before destroying the stack by using the -show command or the -output command
go-deploy --workspace REPLACE_ME_WITH_TERRAFORM_BACKEND --working-directory aws -verbose -destroy
```

```bash
# Destroy Manually
# Make sure you point to the correct workspace before destroying the stack.

terraform -chdir=aws workspace list
terraform -chdir=aws workspace show # shows the name of the current workspace
terraform -chdir=aws show           # shows the state you are about to destroy
terraform -chdir=aws destroy        # You would need to type Yes to approve.

# Now delete the workspace.

terraform -chdir=aws workspace select default # change to default workspace
terraform -chdir=aws workspace delete <NAME_OF_WORKSPACE_THAT_IS_NOT_DEFAULT>  # delete workspace.
```

### Helpful commands for the docker container used as a development environment (go-dev):

1. start the docker container `go-dev` in interactive mode.

```bash
docker run --rm --name go-dev -it geneontology/go-devops-base:tools-jammy-0.4.2  /bin/bash
```

In the command above we used the `--rm` option which means the container will be deleted when you exit.
If that is not the intent and you want to delete it later at your own convenience. Use the following `docker run` command.

```bash
docker run --name go-dev -it geneontology/go-devops-base:tools-jammy-0.4.2  /bin/bash
```

2. To exit or stop the container:

```bash
docker stop go-dev                   # stop container with the intent of restarting it. This is equivalent to `exit` inside the container.
docker start -ia go-dev              # restart and attach to the container.
docker rm -f go-dev                  # remove it for good.
```

3. Use `docker cp` to copy these credentials to /tmp:

```bash
docker cp /tmp/go-aws-credentials go-dev:/tmp/
docker cp /tmp/go-ssh go-dev:/tmp
docker cp /tmp/go-ssh.pub go-dev:/tmp
```

within the docker image:

```bash
chown root /tmp/go-*
chgrp root /tmp/go-*
chmod 400 /tmp/go-ssh
```

