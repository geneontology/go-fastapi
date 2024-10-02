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

# BREAK FOR NEW DOC #

## Configuring and deploying EC2 _instances_:

This is all completed in a dockerized development environment (all commands take place inside the docker container).

1. Prepare _your_ AWS credentials:

Your (personal developer) AWS credentials are used by Terraform to provision the AWS instance and by the provisioned instance to access the certificate store and the S3 buckets used to store Apache logs. These are your personal AWS credentials and should have been appropriately created to give you these permissions.

**NOTE**: specifically, you will need to supply an `aws_access_key_id` and `aws_secret_access_key`. These will be marked with `REPLACE_ME` in the `go-aws-credentials.sample` file farther down.

2. SSH Keys

The keys we'll be using can be found in the shared SpderOak store. If you don't know what this is, ask @kltm.

For testing purposes you can you your own ssh keys. But for production please ask for the go ssh keys.

The names will be:

```
go-ssh.pub
go-ssh
```

3. Spin up the provided dockerized development environment:

```bash
docker rm go-dev
docker run --name go-dev -it geneontology/go-devops-base:tools-jammy-0.4.4  /bin/bash
git clone https://github.com/geneontology/go-fastapi.git
cd go-fastapi/provision
```

4. Copy in SSH keys

Copy the ssh keys from your docker host into the running docker image, in `/tmp`:

```
docker cp go-ssh go-dev:/tmp
docker cp go-ssh.pub go-dev:/tmp
```
You should now have the following in your image:
```
/tmp/go-ssh
/tmp/go-ssh.pub
```
Make sure they have the right perms to be used:
```
chmod 600 /tmp/go-ssh*
```

5. Establish the AWS credential files

Within the running image, copy and modify the AWS credential file to the default location `/tmp/go-aws-credentials`.

```bash
cp production/go-aws-credentials.sample /tmp/go-aws-credentials
```
Add your personal dev keys into the file; update the `aws_access_key_id` and `aws_secret_access_key`:
```
emacs /tmp/go-aws-credentials
```

6. Initialize the S3 Terraform backend:

"Initializing" a Terraform backend connects your local Terraform instantiation to a workspace; we are using S3 as the shared workspace medium (Terraform has others as well). This workspace will contain information on EC2 instances, network info, etc.; you (and other developers in the future) can discover and manipulate these states, bringing servers and services up and down in a shared and coordinated way. These Terraform backends are an arbitrary bundle and can be grouped as needed. In general, the production systems should all use the same pre-coordinated workspace, but you may create new ones for experimentation, etc.

Typically, the name of the workspace is `go-workspace-` + the name of the service; i.e. `go-workspace-api` for the use case here.

```bash

cp ./production/backend.tf.sample ./aws/backend.tf

# Replace the REPLACE_ME_GOAPI_S3_STATE_STORE with the appropriate workspace (state store ~= workspace); so `go-workspace-api`.
emacs ./aws/backend.tf

# Use the AWS CLI to make sure you have access to the terraform s3 backend bucket
export AWS_SHARED_CREDENTIALS_FILE=/tmp/go-aws-credentials

# Check connection to S3 bucket.
aws s3 ls s3://go-workspace-api

# Initialize (if it doesn't work, we fail):
go-deploy -init --working-directory aws -verbose

# Use these commands to figure out the name of an existing workspace if any. The name should have a pattern `go-api-production-YYYY-MM-DD`
go-deploy --working-directory aws -list-workspaces -verbose
```

7. Provision new instance on AWS, for potential production use:

Create a (new) production workspace using the following namespace pattern `go-api-production-YYYY-MM-DD`; e.g.: `go-api-production-2023-01-30`:

```bash
cp ./production/config-instance.yaml.sample config-instance.yaml
emacs config-instance.yaml  # verify the location of the SSH keys for your AWS instance: /tmp/go-ssh
emacs aws/main.tf # technically optional; verify the location of the public ssh key in `aws/main.tf`
```

As well, give a human-readable string for the instance/tags/name (EC2 instance name tag), make it the same at the namespace pattern above; i.e. `go-api-production-2024-01-22`:
also update others as follows:

Name: REPLACE_ME should be "go-api-production-YYYY-MM-DD".
dns_record_name: should be "go-api-production-YYYY-MM-DD.geneontology.org"
dns_zone_id: should be "Z04640331A23NHVPCC784" (for geneontology.org).


```
emacs config-instance.yaml
```

8. Test the deployment

`REPLACE_ME_WITH_S3_WORKSPACE_NAME` would be something like `go-api-production-<TODAYS_DATE>`; i.e. `go-api-production-2024-01-22`

```bash
go-deploy --workspace REPLACE_ME_WITH_S3_WORKSPACE_NAME --working-directory aws -verbose -dry-run --conf config-instance.yaml
```

9. Deploy

Deploy command:
```bash
go-deploy --workspace REPLACE_ME_WITH_S3_WORKSPACE_NAME --working-directory aws -verbose --conf config-instance.yaml
```

10. Checking what we have done

Just to check, ask it to display what it just did (display the Terraform state):
```
go-deploy --workspace REPLACE_ME_WITH_S3_WORKSPACE_NAME --working-directory aws -verbose -show
```

Finally, just show the IP address of the AWS instance:
```
go-deploy --workspace REPLACE_ME_WITH_S3_WORKSPACE_NAME --working-directory aws -verbose -output
```

**NOTE**: write down the IP address of the AWS instance that is created. This can also be found in `REPLACE_ME_WITH_S3_WORKSPACE_NAME.cfg` (e.g. go-api-production-YYYY-MM-DD.cfg).

Useful details for troubleshooting:
These commands will produce an IP address in the resulting `inventory.json` file.
The previous command creates Terraform "tfvars". These variables override the variables in `aws/main.tf`

If you need to check what you have just done, here are some helpful Terraform commands:

```bash
cat REPLACE_ME_WITH_S3_WORKSPACE_NAME.tfvars.json # e.g, go-api-production-YYYY-MM-DD.tfvars.json
```

The previous command creates an ansible inventory file.
```bash
cat REPLACE_ME_WITH_S3_WORKSPACE_NAME-inventory.cfg  # e.g, go-api-production-YYYY-MM-DD-inventory
```

Useful Terraform commands to check what you have just done

```bash
terraform -chdir=aws workspace show   # current terraform workspace
terraform -chdir=aws show             # current state deployed ...
terraform -chdir=aws output           # shows public ip of aws instance
```

## Configuring and deploying software (go-fastapi) _stack_:

These commands continue to be run in the dockerized development environment.

* Make sure there is a CNAME pointing to the public IP address from above. At this stage, for testing, put the IP in an AWS Route 53 CNAME record. (E.g. api-test.geneontology.org.).  Login into aws, list DNS entries for geneontology.org and ensure an 'A name' entry for go-api-production-YYY-MM-DD.geneontology.org associated with the IP address has been defined.

**POSSIBLE CUT START**
* Location of SSH keys may need to be replaced after copying config-stack.yaml.sample
* S3 credentials are placed in a file using the format described above
* S3 uri if SSL is enabled. Location of SSL certs/key
* QoS mitigation if QoS is enabled
* Use the same workspace name as in the previous step
**POSSIBLE CUT END**

Let's ready the the instance, starting by editing the config:
```bash
cp ./production/config-stack.yaml.sample ./config-stack.yaml
emacs ./config-stack.yaml
```
Change these in emacs:
* `S3_BUCKET`: "go-workspace-api" (as above)
* `S3_SSL_CERTS_LOCATION`: "s3://go-service-lockbox/geneontology.org.tar.gz"; this is generally of the form: go-service-lockbox/_TLD_.tar.gz";
* `fastapi_host`: "api-test.geneontology.org"; (must be a FQDN)
* `fastapi_tag`: E.g. "0.2.0"; this should be the Dockerhub _tagged_ version of the API (which is how we deploy within the image), which is conincidentally the GitHub version of the API _sans the final "v"_. <- important point!


Point staging to a different location by default
```bash
emacs provision/vars.yaml
```

Change in emacs:
*  `fastapi_host`: api.geneontology.org
*  `fastapi_host_alias`: '{{ go-api-production-YYY-MM-DD.geneontology.org}}'  example  '{{ go-api-production-2024-09-20.geneontology.org }}'

Finally, get ansible ready:
```
export ANSIBLE_HOST_KEY_CHECKING=False
````

Run the deployment of the stack within the instance:

```bash
go-deploy --workspace REPLACE_ME_WITH_S3_WORKSPACE_NAME --working-directory aws -verbose --conf config-stack.yaml
```

## Testing deployment (within the dev image):

1. Access go-fastapi instance from the CLI by ssh'ing into the newly provisioned EC2 instance:
```
ssh -i /tmp/go-ssh ubuntu@IP_ADDRESS
```

3. Access go-fastapi from a browser:

+We use health checks in the `docker-compose` file.+ (where to put this?)

Use the go-fastapi CNAME name. https://{fastapi_host}/docs

3. Debugging (in the AWS instance):

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


## Destroy Instance and other destructive things:

```bash
# Destroy Using Tool.
# Make sure you point to the correct workspace before destroying the stack by using the -show command or the -output command
go-deploy --workspace REPLACE_ME_WITH_S3_WORKSPACE_NAME --working-directory aws -verbose -destroy
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
docker run --rm --name go-dev -it geneontology/go-devops-base:tools-jammy-0.4.4  /bin/bash
```

In the command above we used the `--rm` option which means the container will be deleted when you exit.
If that is not the intent and you want to delete it later at your own convenience. Use the following `docker run` command.

```bash
docker run --name go-dev -it geneontology/go-devops-base:tools-jammy-0.4.4  /bin/bash
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
