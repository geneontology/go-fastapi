---
name: smoke-test
description: Smoke test a deployed go-fastapi instance
argument-hint: [instance-url]
disable-model-invocation: true
---

# Smoke test a deployed go-fastapi instance

You are testing a deployed go-fastapi instance to verify it is responding correctly.

## Step 1: Determine the instance URL

If an argument `$1` was provided, use it as the base URL. Otherwise, ask the user for the instance URL (e.g. `https://go-api-production-2026-03-12.geneontology.org`).

Strip any trailing slash from the URL.

## Step 2: Run endpoint checks

Use `curl` to test each endpoint. For each one, check:
- HTTP status code is 200
- Response body contains expected content (where noted)

Run ALL of these checks and collect the results before reporting:

### 1. OpenAPI docs (liveness check)
```
curl -s -o /dev/null -w '%{http_code}' {URL}/docs
```
Expected: 200

### 2. Prefixes (no parameters, core app test)
```
curl -s -o /dev/null -w '%{http_code}' '{URL}/api/identifier/prefixes'
```
Expected: 200

Also check the response contains prefix data:
```
curl -s '{URL}/api/identifier/prefixes' | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d))"
```
Expected: a positive number (the count of prefixes)

### 3. Ontology lookup (well-known root term)
```
curl -s -o /dev/null -w '%{http_code}' '{URL}/api/go/GO:0008150'
```
Expected: 200

Also verify the response contains the expected label:
```
curl -s '{URL}/api/go/GO:0008150' | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('label','MISSING'))"
```
Expected: "biological_process"

### 4. Search autocomplete
```
curl -s -o /dev/null -w '%{http_code}' '{URL}/api/search/entity/autocomplete/biological'
```
Expected: 200

### 5. CURIE expansion
```
curl -s -o /dev/null -w '%{http_code}' '{URL}/api/identifier/prefixes/expand/GO:0008150'
```
Expected: 200

## Step 3: Report results

Present results as a table:

| Endpoint | Status | Result |
|----------|--------|--------|
| /docs | {code} | PASS/FAIL |
| /api/identifier/prefixes | {code} | PASS/FAIL |
| /api/go/GO:0008150 | {code} | PASS/FAIL |
| /api/search/entity/autocomplete/biological | {code} | PASS/FAIL |
| /api/identifier/prefixes/expand/GO:0008150 | {code} | PASS/FAIL |

End with a summary: X/5 passed.

If any endpoint fails, suggest debugging steps:
- Check if the instance is reachable: `curl -s -o /dev/null -w '%{http_code}' {URL}`
- Check container health via SSH: `ssh -i /tmp/go-ssh ubuntu@{hostname}` then `docker inspect --format "{{json .State.Health }}" fastapi`
- Check container logs: `docker-compose -f /home/ubuntu/stage_dir/docker-compose.yaml logs -f`
