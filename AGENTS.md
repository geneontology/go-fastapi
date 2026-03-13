# CLAUDE.md

## Project overview

go-fastapi is the Gene Ontology's primary API service. It is a Python FastAPI application deployed behind an Apache reverse proxy on AWS EC2 instances using Terraform and Ansible.

The service runs at `api.geneontology.org` (production, via Cloudflare).

## Repo management

This repo uses `poetry` for managing dependencies. Never use commands like `pip` to add or manage dependencies.

## Repository structure

- `app/` — Application code (routers, utils, config).
- `tests/` — Pytest test suite.
- `provision/` — All deployment infrastructure:
  - `aws/main.tf` — Terraform config, uses module from `geneontology/devops-aws-go-instance` (ref V3.1).
  - `stage.yaml`, `start_services.yaml` — Ansible playbooks.
  - `vars.yaml`, `ssl-vars.yaml`, `qos-vars.yaml`, `s3-vars.yaml`, `docker-vars.yaml` — Ansible variables.
  - `templates/` — Jinja2 templates for docker-compose, Apache vhosts, QoS config.
  - `production/` — Production config samples. See [canonical deployment docs](https://github.com/geneontology/devops-documentation/blob/main/README.api.md) for production procedures; general devops setup (credentials, environment) is at [README.setup.md](https://github.com/geneontology/devops-documentation/blob/main/README.setup.md).
- `.github/workflows/docker-build.yaml` — CI/CD: builds and pushes Docker image to DockerHub on version tags.

## Best practice

* write pytest tests
* always write pytest functional style rather than unittest OO style
* use modern pytest idioms, including `@pytest.mark.parametrize` to test for combinations of inputs
* NEVER write mock tests unless requested. I need to rely on tests to know if something breaks
* For tests that have external dependencies, you can do `@pytest.mark.integration`
* Do not "fix" issues by changing or weakening test conditions. Try harder, or ask questions if a test fails.
* Avoid try/except blocks, these can mask bugs
* Fail fast is a good principle
* Follow the DRY principle
* Avoid repeating chunks of code, but also avoid premature over-abstraction
* Declarative principles are favored
* Always use type hints, always document methods and classes

## Releasing

A GitHub release is required before deploying new code to production. The release tag triggers CI to build and push a Docker image to DockerHub.

1. Decide on the new version number following semver (e.g. `v0.4.0`). The previous release is shown at https://github.com/geneontology/go-fastapi/releases.
2. Create the release from `main`:
   ```
   gh release create vX.Y.Z --target main --generate-notes --repo geneontology/go-fastapi
   ```
3. This triggers `.github/workflows/docker-build.yaml`, which builds and pushes `geneontology/go-fastapi:X.Y.Z` to DockerHub.
4. Verify the image is available: `docker pull geneontology/go-fastapi:X.Y.Z`
5. Use `X.Y.Z` as the `fastapi_tag` (note: no leading "v") when deploying.

## Deployment

Canonical deployment documentation lives at:
https://github.com/geneontology/devops-documentation/blob/main/README.api.md

Key points:
- `go-deploy` is the high-level deployment tool for day-to-day operations. Use it for provisioning, deploying stacks, inspecting state, and destroying instances.
- Raw `terraform` commands are for lower-level debugging only.
- Workspace naming convention: `go-api-production-YYYY-MM-DD`.
- Docker image versioning: the `fastapi_tag` in config-stack.yaml matches the GitHub release version without the leading "v" (e.g. release `v0.2.0` → tag `0.2.0`). See releases at https://github.com/geneontology/go-fastapi/releases.
- Config sample files in `provision/production/` use unique `REPLACE_ME_*` placeholders (e.g. `REPLACE_ME_INSTANCE_NAME`, `REPLACE_ME_DNS_RECORD`, `REPLACE_ME_SSL_CERTS_LOCATION`). Each placeholder is self-documenting. Always scan for remaining placeholders before deploying: `grep -rn 'REPLACE_ME_' config-stack.yaml config-instance.yaml aws/backend.tf`

## Related repositories

- [devops-documentation](https://github.com/geneontology/devops-documentation) — Canonical deployment docs (README.api.md). Checked out at `../devops-documentation`.
- [devops-aws-go-instance](https://github.com/geneontology/devops-aws-go-instance) — Terraform module for AWS EC2 provisioning (consumed via `main.tf`).
- [devops-apache-proxy](https://github.com/geneontology/devops-apache-proxy) — Apache reverse proxy Docker image (consumed at deploy time).
- [devops-deployment-scripts](https://github.com/geneontology/devops-deployment-scripts) — Builds the `geneontology/go-devops-base` Docker image used as the devops environment.

## Build and test

Local development uses Poetry:
```
poetry install
```

Run tests via Make:
- `make test` — runs unit tests, integration tests, lint, and spell check
- `make unit-tests` — `poetry run pytest -v tests/unit/*.py`
- `make integration-tests` — `poetry run pytest tests/integration/step_defs/*.py`
- `make lint` — `poetry run tox -e lint-fix`

CI builds and pushes a Docker image to DockerHub on version tags via `.github/workflows/docker-build.yaml`.

## Important conventions

- The default instance user is `ubuntu`.
- Docker container name for devops work: `go-fastapi`.
- Credentials and SSH keys go in `/tmp/` inside the devops container (see README.setup.md).
- Never commit credentials, SSH keys, or `backend.tf` files (covered by `.gitignore`).
- **When generating deployment commands, always read the actual sample files** (e.g. `production/backend.tf.sample`, `production/config-instance.yaml.sample`, `production/config-stack.yaml.sample`) to determine exact placeholder names and file structure. Do not rely on documentation alone — the docs may use different placeholder names than the files. The sample files are the source of truth.
- The `config-stack.yaml` (from `config-stack.yaml.sample`) bundles overrides for SSL, S3, and other vars — when it is used, editing `vars.yaml` and `ssl-vars.yaml` separately is not needed for values already present in the stack config.
- **When generating command lists for the user**, clearly distinguish between commands that can be copy-pasted verbatim and those that require user-specific values. Specifically:
  - The path to the AWS credentials file on the host machine is user-specific — always ask or confirm.
  - The path to SSH keys on the host machine is user-specific — always ask or confirm.
  - The `docker cp` commands for copying credentials into the container require the user's host paths.
  - The environment exports (`AWS_SHARED_CREDENTIALS_FILE`, `AWS_REGION`, `ANSIBLE_HOST_KEY_CHECKING`) must appear before any commands that depend on them — do not assume they carry over from a previous step description.
  - All other commands (sed substitutions, go-deploy, grep checks) can be copy-pasted verbatim once the date and track are known.
