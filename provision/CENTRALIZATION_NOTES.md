# Devops centralization handoff notes (go-fastapi API)

**Purpose.** Preserve the lessons, procedures, and decisions from the May 2026
non-Blazegraph (`v0.4.0`/`v0.4.1`) API rollout, so the planned centralization of devops
into the [`geneontology/operations`](https://github.com/geneontology/operations)
repo can pick them up. This is intended to be read (and ported) during that move.

**Canonical sources this complements** (don't duplicate — go there for the live
procedure): deployment runbook is
[`devops-documentation/README.api.md`](https://github.com/geneontology/devops-documentation/blob/main/README.api.md);
the API code/devops lives in this repo (`app/`, `provision/`, `CLAUDE.md`).

---

## 1. The architecture change (`v0.4.0`): Blazegraph → GOlr + index files

PR #136 (umbrella issue #137) removed the SPARQL/Blazegraph dependency. API
endpoints are now served by **GOlr** plus **six static GO-CAM index JSON files**:
`{contributor,entity,evidence,provided_by,source,taxon}_index.json`.

- Served from `https://current.geneontology.org/go-cams/index-json/`.
- Read by `app/utils/settings.py::get_index_files()`. Since PR #161 the app
  **caches them in-process** (load-once per worker) — so **restart the `fastapi`
  container to pick up regenerated files**.
- The index-file config keys must exist in **both** `app/conf/config.yaml` (dev/test)
  **and** `provision/templates/config.yaml` (the deploy template, bind-mounted over
  the baked config). The deploy template originally lacked them → issue #157 / PR #158.
- `entity_index` keys on `model.objects[].id` (+ GO-term closures), which is what
  makes the isoform fix (#135) work: isoform IDs like `UniProtKB:P08887-2` appear as
  keys, so `/api/gp/{id}/models` resolves them via the GOlr isoform facet then an
  index lookup.
- **GOlr-backed subset/ribbon resolution must key on stable GO IDs, not labels.**
  `/api/ontology/ribbon/` and `/api/ontology/subset/{id}` group slim terms by
  aspect and resolve each aspect's root term. Matching the root by
  `annotation_class_label` is fragile: GOlr relabelled the molecular_function root
  `GO:0003674` ("molecular_function" → "gene product or complex activity"), the
  lookup returned nothing, and an unguarded `KeyError` 500'd the ribbon for every
  `goslim_agr` call. Fixed in `v0.4.1` by resolving roots from a fixed
  `source → GO-ID` map (`ASPECT_ROOTS` in `app/utils/ontology_utils.py`). The
  break was a **GOlr data condition** — identical on `v0.3.x` and `v0.4.0`, so an
  API rollback did **not** mitigate it; see §6 (#165).

## 2. Generating the six index files for *this* version of the API

Until the new pipeline (`pipeline-from-goa` → skyhook, see §6) is live, the index
files are generated **manually each release cycle** from the gocam-py pipeline,
then uploaded to S3. Generator: `gocam-py/pipeline/generate_index_files.py`,
orchestrated in production by `pipeline-from-goa/scripts/gocam-processing.sh`
(steps 1–4). Manual run (from the `gocam-py/` repo root):

```bash
WORK=/tmp/gocam-index-run
mkdir -p "$WORK"/{input,01-gocam-models,02-true-gocams,02-pseudo-gocams,03-indexed-true-gocams,04-index-files,reports}
# Inputs — all from the CURRENT release:
curl -fSL https://current.geneontology.org/products/json/noctua-models-json.tgz -o "$WORK/noctua-models.tar.gz"
tar -xzf "$WORK/noctua-models.tar.gz" -C "$WORK/input"
curl -fSL https://current.geneontology.org/ontology/go.obo      -o "$WORK/go.obo"        # PIN the ontology
curl -fSL https://current.geneontology.org/metadata/groups.yaml -o "$WORK/groups.yaml"
uvr() { uv run --extra oaklib --with "networkx>=3,<4" "$@"; }   # see env note below
uvr python pipeline/convert_minerva_models_to_gocam_models.py --input-dir "$WORK/input" --output-dir "$WORK/01-gocam-models" --report-file "$WORK/reports/01.jsonl" --verbose
uvr python pipeline/filter_true_gocam_models.py --input-dir "$WORK/01-gocam-models" --output-dir "$WORK/02-true-gocams" --pseudo-gocam-output-dir "$WORK/02-pseudo-gocams" --report-file "$WORK/reports/02.jsonl" --verbose
uvr python pipeline/add_query_index_to_models.py --input-dir "$WORK/02-true-gocams" --output-dir "$WORK/03-indexed-true-gocams" --report-file "$WORK/reports/03.jsonl" --go-adapter-descriptor "pronto:$WORK/go.obo" --goc-groups-yaml "$WORK/groups.yaml" --verbose
uvr python pipeline/generate_index_files.py --input-dir "$WORK/03-indexed-true-gocams" --output-dir "$WORK/04-index-files" --report-file "$WORK/reports/04.jsonl" --verbose
```

**Critical:** `--go-adapter-descriptor pronto:<current go.obo>` pins GO to the current
release. The script default `sqlite:obo:go` is OAK's prebuilt cache and can be STALE.

**Env note:** on the maintainer's host `poetry` was broken and `uv sync --all-extras`
failed building `pygraphviz` (needs `libgraphviz-dev`). The four pipeline scripts use
plain networkx only, so `uv run --extra oaklib --with "networkx>=3,<4"` (skipping the
`cx2`/pygraphviz extra) works without system libs. (Alternative: `apt-get install
libgraphviz-dev`.)

**Sanity check (2026-05-30 run vs then-current published files):** key counts were
~3–5% higher (entity 15,566 vs 15,159; etc.), driven by ~+81 more models in the
current release — expected for fresher data. Funnel: 54,381 Minerva models → 3,361
GO-CAMs → 1,810 "true" GO-CAMs indexed (index covers true GO-CAMs only). Spot-check
`entity_index` for isoform keys (e.g. `UniProtKB:P08887-2`) after generating.

## 3. Publishing the files + cache topology

- **`current.geneontology.org` = Cloudflare → CloudFront → S3** (bucket
  `go-data-product-current`). Index files at
  `s3://go-data-product-current/go-cams/index-json/<name>.json`.
- After upload, verify the **origin** independent of caches:
  `aws s3api head-object --bucket go-data-product-current --key go-cams/index-json/entity_index.json`
  (S3 `ETag` = md5; compare to the local file).
- Both CDN layers cache (~1h origin `max-age`, but Cloudflare's edge TTL is set by a
  zone rule and observed to exceed it). To force a refresh, **purge the inner layer
  first**: CloudFront invalidation (`/go-cams/index-json/*`) **then** a Cloudflare
  purge — otherwise the outer layer just re-pulls the stale inner copy. (A `?cb=`
  cache-buster proves nothing through both layers — use `s3api head-object`.)

## 4. Deploy process + gotchas (go-fastapi instances)

Follow `devops-documentation/README.api.md` (`go-deploy` init → instance → stack).
Lessons learned this cycle:

- **`--network host` is required** for the devops container on the maintainer's host
  (the default bridge network can't resolve DNS → Terraform/AWS timeouts).
- **The agent drives the container from outside**, non-interactively:
  `docker exec <name> bash -lc '…'` per step (no `docker exec -it … bash` session —
  shell state doesn't persist between automated calls). Pass AWS env via `-e`.
- **README.api.md is stale on one point:** instances have **Docker Compose v2**
  (`docker compose`); `docker-compose` (v1) is NOT installed. To restart the API use
  `docker restart fastapi` or `docker compose -f /home/ubuntu/stage_dir/docker-compose.yaml restart fastapi`.
- **`USE_CLOUDFLARE=0`** matches both existing production boxes (checked); keep it
  unless deliberately changing the Apache real-IP handling.
- **Branch-aware provisioning:** deploy from `main`'s `provision/` (it carries the
  #158 index-file config keys). `fastapi_tag` = the GitHub release without the leading
  `v` (e.g. release `v0.4.0` → tag `0.4.0`). Image builds automatically on the `v*`
  tag via `.github/workflows/docker-build.yaml`.
- **No version endpoint (#155):** identify the running build via SSH
  `docker inspect fastapi --format '{{.Config.Image}}'`, or fingerprint over HTTP via
  the OpenAPI path-set (`/openapi.json`: 0.4.0 = 32 paths, drops `/api/groups` &
  `/api/models`; 0.3.9 = 38). (`v0.4.1` is logic-only — same path-set as `v0.4.0`.)
- **Running the test suite locally:** the committed `.venv` targets Python 3.10 and
  poetry is broken on the 3.12 host. Build a fresh env with
  `uv venv --python 3.11 && uv pip install -e . && uv pip install httpx` — the
  dev-group `httpx` that starlette's `TestClient` needs is **not** pulled by `-e .`.
  Tests hit **live** GOlr + mygene, so the 3 mygene/Alliance `HGNC:12139` failures
  (#159) are expected drift, not regressions; everything else should pass.

## 5. The cutover (`api.geneontology.org`)

`api.geneontology.org` = Cloudflare → the EC2 instance origin (separate from the
`current.geneontology.org` data CDN — don't conflate the two). "Go live" = repoint the
Cloudflare origin to the new instance (dashboard). Cloudflare also caches some API GET
responses, so after the flip, normal requests keep serving the old build until those
edge entries age out; cache-busted/uncached requests hit the new origin immediately.
Keep the previous instance running as a hot backup until the cache has aged out and
you're confident (rollback = repoint Cloudflare back).

## 6. `v0.4.0`–`v0.4.1` rollout record (May 2026)

Goal: remove Blazegraph and confirm the isoform fix (#135) holds. Both met on `0.4.0`
(deployed to workspace `go-api-production-2026-05-29`, cut over 2026-05-30). `v0.4.1`
is a same-day **ribbon hotfix** (#165) on top of `v0.4.0` — see §1.

| Issue/PR | What |
|---|---|
| #137 | Umbrella: remove Blazegraph dependencies (OPEN; last item = gocam-py pipeline automation) |
| #136 | The Blazegraph→GOlr+index PR (merged 2026-03-10) |
| #135 / #150 / #151 | Isoform fix (`/gp/{id}/models` over all isoforms); #150 on main, #151 backport (`v0.3.9-a`) |
| #157 / #158 | Deploy template missing index-file keys → fixed |
| #160 / #161 | Index files were re-fetched per request → in-process caching |
| #159 | Live-data QC test drift (GOlr `annotation_class`, mygene/Alliance HGNC:12139). The ribbon/subset portion was cleared by #167; the 3 mygene `HGNC:12139` cases remain (external data) |
| #162 | GO hierarchy `rows=10000` cap (truncates large terms; latency-vs-completeness — confirm intent) |
| #163 | `/api/users/{orcid}/gp` shape change (object→list) + untested |
| #165 / #167 | Ribbon `500` on `goslim_agr`: GOlr relabelled the MF root `GO:0003674`, breaking the `annotation_class_label` self-join → `KeyError`. Fixed by resolving aspect roots by GO ID (`ASPECT_ROOTS`) + guards |
| #166 | Bot-thought follow-up: drop the now-redundant GOlr round-trip kept only for the per-category `description` |
| release `v0.4.0` | First non-Blazegraph production build |
| release `v0.4.1` | Ribbon hotfix (#165) on top of `v0.4.0` |

## 7. Open follow-ups (NOT blockers for the Blazegraph/isoform goal)

- **#159** — re-baseline the live-data QC tests (recurring; cf. #152/#153).
- **#162** — confirm intent of the hierarchy `rows` cap with @sierra-moxon; if a bug,
  `rows=-1` + a large-term regression test.
- **#163** — decide the `/api/users/{orcid}/gp` contract (list shape, `/gp` naming) + add tests.
- **#166** — optional ribbon cleanup: drop the second GOlr query in
  `get_ontology_subsets_by_id` entirely (the `ASPECT_ROOTS` map alone resolves the
  roots) if no client needs the per-category `description` on `/api/ontology/subset/{id}`.
- **Index-file automation** — `pipeline-from-goa` (gocam-py → skyhook) is intended to
  replace the manual §2 generation; once live and pushing to S3, the manual step retires.

## 8. Related repos

- `devops-documentation` — canonical deploy runbook (`README.api.md`).
- `gocam-py` — index-file generator (`pipeline/`).
- `pipeline-from-goa` — future automated pipeline (Jenkins → skyhook).
- `devops-aws-go-instance` (TF module), `devops-apache-proxy` (proxy image).

> Detailed per-topic working notes also live in the maintainer's local Claude memory
> for this project (machine-local; not a substitute for this doc). This document is the
> portable record.
