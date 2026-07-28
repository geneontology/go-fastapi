---
name: upstream-api-check
description: Check whether an announced upstream API change (primarily Alliance/AGR) affects go-fastapi. Use when the user reports an upstream release announcement, forwards a release-notes email, or asks whether an upcoming Alliance/AGR change breaks us.
argument-hint: [upstream-name]
---

# Check an announced upstream API change against go-fastapi

The user has learned that an upstream provider is changing its API — typically from
an Alliance of Genome Resources (AGR) release announcement — and wants to know
whether it affects go-fastapi *before* it reaches production.

Do not answer from the release notes alone. AGR has changed response shapes without
mentioning it in the notes (see the `#159` / `#168` history below). The deliverable
is an empirical verdict: our real parsing code run against the upstream's staged
next release.

Unless the user names a different upstream in `$1`, assume AGR.

## Background: why AGR is checkable now

AGR restructured `GET /api/gene/{id}` in May 2026 with no warning, silently breaking
`gene_to_uniprot_from_alliance` (issue #159, fixed in PR #168). Following GO feedback,
AGR now publishes **advance** release notes ahead of a release and stages the next
release publicly, so this class of change can be caught before it lands.

## Where AGR announcements come from

- **Mailing list — `alliance-api-changes@lists.stanford.edu`.** AGR's announcement
  list, described by AGR as being "to notify external developers of upcoming changes
  to Alliance of Genome Resources public APIs". This is where the advance notes are
  emailed, and it is usually what prompts this check.
  - Subscribe / list info: https://mailman.stanford.edu/mailman/listinfo/alliance-api-changes
  - **Archives are publicly readable** (no login), one plain-text file per month —
    the easiest source to read and diff:
    https://mailman.stanford.edu/pipermail/alliance-api-changes/
    e.g. `https://mailman.stanford.edu/pipermail/alliance-api-changes/2026-July.txt`
- **Release notes page (human-facing)** — https://www.alliancegenome.org/release-notes
  Same content as the emailed notes, kept current across releases.

When quoting from the archive, cite the list and the release, not the individual
sender — these are public archives containing third-party addresses.

Note that the docstring in `app/utils/mygene_utils.py` was written during #168 and
describes the *old* situation. If it still claims AGR provides no versioning or
deprecation notice, that is stale — correct it.

## Step 1: Establish which releases are in play

```
curl -sS https://www.alliancegenome.org/api/releaseInfo; echo
curl -sS https://stage.alliancegenome.org/api/releaseInfo; echo
```

`www` is production; `stage` runs the **next** release. If `stage` reports a higher
`releaseVersion` than `www`, that staged version is what you diff against. If the two
match, there is no staged release to test and you can only assess from the notes —
say so explicitly rather than implying you verified against a real endpoint.

## Step 2: Read the advance release notes

Fastest source is the mailing list archive — plain text, no scraping. List the
available months, then read the relevant one:

```
curl -sS https://mailman.stanford.edu/pipermail/alliance-api-changes/ | grep -oE '20[0-9]{2}-[A-Za-z]+\.txt(\.gz)?'
curl -sS https://mailman.stanford.edu/pipermail/alliance-api-changes/2026-July.txt
```

Substitute the month you need; older months are gzipped (`.txt.gz`, pipe through
`zcat`). If the announcement predates what you find here, fall back to the release
notes page. That page (https://www.alliancegenome.org/release-notes) is a
client-rendered SPA and fetching the URL directly returns an empty ~1.7KB shell, so
read its content from the WordPress API that backs it:

```
curl -sS 'https://public-api.wordpress.com/wp/v2/sites/alliancegenome.wordpress.com/pages?slug=release-notes' \
  | python3 -c "import sys,json,html,re; d=json.load(sys.stdin)[0]['content']['rendered']; t=re.sub(r'<[^>]+>','',d); print(html.unescape(t))" \
  | head -200
```

Read the entry for the staged version. Note every endpoint, field, and download URL
it names as changing.

The two sources can differ in detail — the 9.1.0 email gave a `stage.alliancegenome.org`
example URL where the web page gave the `www` equivalent — so prefer the web page for
post-release URLs and treat emailed URLs as pre-release illustrations.

## Step 3: Re-inventory our actual upstream dependency

Do not assume it is still a single call — check:

```
grep -rn "alliancegenome" app/
```

For each call site, note the exact URL and which JSON fields the code reads.

## Step 4: Diff the live response shape, production vs staged

This catches the silent reshapes the notes omit. Adjust `GENES`/the URL if the
inventory in step 3 shows we call something else:

```
python3 - <<'PY'
import json, urllib.request
def paths(o, prefix=""):
    out=set()
    if isinstance(o, dict):
        for k,v in o.items():
            p=f"{prefix}.{k}" if prefix else k
            out.add(p); out |= paths(v, p)
    elif isinstance(o, list):
        for v in o: out |= paths(v, prefix+"[]")
    return out
for gene in ("HGNC%3A12139", "HGNC%3A11998"):
    sets={h: paths(json.load(urllib.request.urlopen(
        f"https://{h}.alliancegenome.org/api/gene/{gene}", timeout=60))) for h in ("www","stage")}
    print(f"===== {gene.replace('%3A',':')}")
    print("  REMOVED:", sorted(sets["www"]-sets["stage"]))
    print("  ADDED  :", sorted(sets["stage"]-sets["www"])[:15])
PY
```

Removed key paths are the danger. Cross-check every removal against the fields our
code reads. Purely additive changes are safe.

`HGNC:12139` (TRAV39) is the load-bearing fixture: it is a GCRP-only gene whose
UniProtKB ID lives in `gene.gcrpCrossReference` rather than `gene.crossReferences[]`,
which is exactly what broke in #159. Always include it.

## Step 5: Run our real parser against the staged release

The strongest evidence. The committed `.venv` may be stale; `uv` works:

```
PYTHONPATH=$(pwd) uv run --quiet --no-project --python 3.11 \
  --with requests --with fastapi --with ontobio --with biothings_client \
  python - <<'PY'
import requests
from app.utils import mygene_utils
real = requests.get
mygene_utils.requests.get = lambda url, *a, **k: real(
    url.replace("https://www.alliancegenome.org", "https://stage.alliancegenome.org"), *a, **k)
for g in ("HGNC:12139", "HGNC:11998", "HGNC:6893", "HGNC:1097"):
    try:
        r = mygene_utils.gene_to_uniprot_from_alliance(g)
        print(f"{g:<12} OK n={len(r)} first={r[0] if r else None}")
    except Exception as e:
        print(f"{g:<12} FAIL {type(e).__name__}: {e}")
PY
```

Every gene must resolve. A `DataNotFoundException` here means the staged release
breaks us.

## Step 6: Check for endpoint removals

AGR publishes an OpenAPI spec — note there is **no** `/api/` prefix on the path, and
`/api/swagger.json` 404s:

```
curl -sS 'https://www.alliancegenome.org/openapi?format=json' \
  | python3 -c "import sys,json; print('\n'.join(sorted(json.load(sys.stdin)['paths'])))"
```

The spec lists paths only, with no response schemas, so it catches endpoint removals
but not field renames. Beware `/q/openapi`: it returns HTTP 200 but the body is the
SPA shell, so check content-type and body rather than status when probing this host.

## Step 7: Confirm our current state is green

```
make unit-tests
```

or just the affected file:

```
PYTHONPATH=$(pwd) uv run --quiet --no-project --python 3.11 \
  --with pytest --with requests --with fastapi --with ontobio --with biothings_client \
  python -m pytest tests/unit/test_mygene_utils.py -q
```

These hit live services by design (the project does not mock), so a failure here is
either real drift or an upstream outage — distinguish the two before reporting.

## Step 8: Report

Lead with the verdict: does the announced change affect go-fastapi, yes or no.

Then give:
- Which staged version you tested against, and the date.
- What the notes said was changing, and which of those we touch (usually none).
- The shape diff result — specifically any removed key paths.
- The parser run result.
- Anything you could **not** verify, stated plainly.

Be explicit about verified versus inferred. "The URL still works today but AGR says
stable URLs are moving" is not the same claim as "this will break."

## Also worth checking beyond go-fastapi

AGR download-file changes have bitten other GO repos. `gopreprocess` consumes the
Alliance orthology JSON and is tracked in geneontology/gopreprocess#78. If the
announcement touches download files, formats, or `fms.alliancegenome.org` URLs, say
so and point at that issue rather than re-deriving it.

## Other upstreams

If `$1` names a different upstream, the same shape applies, but note that neither
GOlr nor mygene.info publishes comparable advance notices or a staging environment —
drift there surfaces through the live QC suite instead (the pattern in #152, #153,
#159, #167). For those, skip to step 7 and compare current responses against test
expectations.
