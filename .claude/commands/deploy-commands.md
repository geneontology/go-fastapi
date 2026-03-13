---
description: Generate deployment commands for a production go-fastapi instance
argument-hint: [version] [date]
---

# Generate go-fastapi deployment commands

You are generating a complete set of copy-pasteable bash commands to deploy go-fastapi to production.

## Step 1: Gather context

Perform ALL of the following checks before generating any commands:

### User-specific paths
Ask the user for:
- Path to AWS credentials file on their host machine (e.g. `/home/user/secrets/go-aws-credentials`)
- Path to SSH keys directory on their host machine (e.g. `/home/user/secrets/ssh-keys/`)

Do NOT proceed without these.

### Existing devops container
Run: `docker ps -a --filter name=^go-fastapi$ --format '{{.Names}}'`
- If `go-fastapi` is returned: this is a **resuming session** (Path B)
- If empty: this is a **fresh setup** (Path A)

### Version
If a version was provided as argument `$1`, use it. Otherwise:
- Check the latest release: `gh release list --repo geneontology/go-fastapi --limit 1`
- Check if main is ahead: `gh api repos/geneontology/go-fastapi/compare/v{latest}...main --jq '.ahead_by'`
- If main is ahead (>0 commits), tell the user and ask whether to create a new release or use the existing version
- If main is even (0 commits), use the existing version

### Docker image
Check if the target version's Docker image exists:
`docker manifest inspect geneontology/go-fastapi:{version_without_v} 2>/dev/null`
- If it exists: skip the release step
- If it doesn't exist: a release is needed

### Date
If a date was provided as argument `$2`, use it. Otherwise use today's date in YYYY-MM-DD format.

## Step 2: Read sample files

Read these files to get the current placeholder names (these are the source of truth):
- `provision/production/backend.tf.sample`
- `provision/production/config-instance.yaml.sample`
- `provision/production/config-stack.yaml.sample`

## Step 3: Generate commands

Use the gathered context to produce the full command set. Clearly separate commands by where they run:
- **On host**: docker commands, docker cp, gh release
- **Inside devops container**: go-deploy, terraform, git, sed

### If a release is needed, start with:
```
gh release create v{VERSION} --target main --generate-notes --repo geneontology/go-fastapi
```
Then tell the user to wait for the Docker build workflow to complete and provide a command to check:
```
gh run list --repo geneontology/go-fastapi --workflow docker-build.yaml --limit 1
```

### Path A: Fresh setup (no existing container)

Generate commands for:
1. `docker run` to create the container
2. `docker cp` to copy credentials and SSH keys from host into container at `/tmp/`
3. Inside container: `chmod 600 /tmp/go-ssh*`
4. Inside container: `git clone`, `cd go-fastapi/provision`
5. Backend init: `cp backend.tf.sample`, `sed` to replace placeholder, `go-deploy -init`
6. Instance config: `cp config-instance.yaml.sample`, `sed` commands for each placeholder
7. Instance deploy: dry-run then deploy with `go-deploy`
8. Stack config: `cp config-stack.yaml.sample`, `sed` commands for each placeholder
9. Verify: `grep -rn 'REPLACE_ME_' config-stack.yaml config-instance.yaml aws/backend.tf`
10. Stack deploy: `export ANSIBLE_HOST_KEY_CHECKING=False`, `go-deploy`
11. Test: curl the instance, health check commands
12. Finalize: show IP for Cloudflare cutover, destroy old instance commands

### Path B: Resuming session (container exists)

Generate commands for:
1. `docker start` + `docker exec` to rejoin the container
2. Inside container: `cd /tmp/go-fastapi/provision`, `git pull`
3. Check if backend is already initialized: `go-deploy --working-directory aws -list-workspaces -verbose`
4. If already initialized, skip backend init steps
5. Continue from instance config (step 6) through finalize (step 12) as in Path A

## Important conventions

- Use `sed -i` for placeholder substitution, not `emacs`
- Use single-dash flags for go-deploy: `-dry-run`, `-verbose`, `-show`, `-output` (NOT `--dry-run`)
- The workspace name pattern is `go-api-production-YYYY-MM-DD`
- The `fastapi_tag` is the version WITHOUT the leading "v"
- The container names on the deployed instance are `fastapi` and `apache_fastapi`
- The working directory inside the fastapi container is `/code`
- Always include the placeholder verification grep step before deploying the stack
