# Tests

Two suites, both run by `make test`:

- `tests/unit/` — `make unit-tests` (`pytest -v tests/unit/*.py`)
- `tests/integration/` — `make integration-tests` (`pytest tests/integration/step_defs/*.py`), pytest-bdd scenarios whose data lives in `tests/integration/features/*.feature`

`tests/fixtures/` is a separate concern — static JSON index files substituted by `conftest.py` so tests don't depend on real index paths. See [`fixtures/README.md`](fixtures/README.md).

## Live-data fixtures

By policy this project does not mock external services, so most tests query live GOlr, mygene.info and the Alliance API, asserting against **hardcoded real identifiers** — gene IDs, GO terms — and against **annotation-count thresholds**.

That means a test can go red because upstream *data* changed, with no code change on our side. This recurs: #152, #153, #159, #170.

Identifiers are spread across both suites, so a fixture sweep that only covers `tests/unit/` is incomplete:

```bash
# every hardcoded gene ID, both suites
grep -rnoE "(ZFIN|MGI|FB|HGNC|RGD|SGD|WB|Xenbase):[A-Za-z0-9:_-]+" tests/
```

## Triage: a fixture starts returning 404

A 404 on a gene that still exists at its source database usually means the gene is absent from the data GOlr was built from — not that anything is broken here.

**1. Confirm the gene is really gone from GOlr**, rather than the endpoint misbehaving:

```bash
curl -sS -G "https://golr.geneontology.org/solr/select" \
  --data-urlencode 'q=*:*' --data-urlencode 'fq=id:"ZFIN:ZDB-GENE-980526-388"' \
  --data-urlencode 'wt=json' --data-urlencode 'rows=1'
```

**2. Check the GAF that GOlr is actually built from.** Since the pipeline migration ([go-technical-announcements#20](https://github.com/geneontology/go-technical-announcements/issues/20)) that is the new layout, `annotations/gaf/<MNEMONIC>-{mod,uniprot}.gaf.gz` — *not* the legacy `annotations/<db>.gaf.gz`. The legacy files were still served through the transition window and still return HTTP 200 with plausible content, so comparing against them gives a confidently wrong answer:

```bash
curl -sS https://current.geneontology.org/annotations/gaf/DANRE-mod.gaf.gz \
  | zcat | awk -F'\t' '$2=="ZDB-GENE-980526-388"' | wc -l
```

**3. Interpret using `-mod` vs `-uniprot`.** This is the useful discriminator:

| `-mod` | `-uniprot` | Meaning |
|---|---|---|
| absent | **present** | Known upstream gene-to-MOD-ID **mapping issue**, already owned by another group. Re-baseline the fixture and move on — do not escalate. |
| absent | absent | A real coverage or curation change. Worth reporting onward. |

**4. Re-baseline to a gene that is present**, preferably one that still satisfies whatever the test actually asserts. Where a scenario asserts a specific GO term, find another gene carrying that term so only the identifier changes:

```bash
curl -sS -G "https://golr.geneontology.org/solr/select" \
  --data-urlencode 'q=*:*' --data-urlencode 'fq=document_category:"annotation"' \
  --data-urlencode 'fq=annotation_class:"GO:0030500"' --data-urlencode 'fq=bioentity:ZFIN\:*' \
  --data-urlencode 'wt=json' --data-urlencode 'rows=10' \
  --data-urlencode 'fl=bioentity,bioentity_label'
```

## Re-baselining vs weakening

`AGENTS.md` says not to "fix" failures by weakening test conditions. Updating a fixture or threshold to match a *verified* upstream change is not that — but the two look identical in a diff, so the distinction has to be made explicit:

- Prefer repointing the fixture over relaxing the assertion. Changing which gene is tested keeps the assertion's strength intact.
- Only move a threshold when you have confirmed the new value against the source data, and **leave a comment at the assertion** recording the number, the reason, and the issue. See `test_fly_ribbon` in `tests/unit/test_ribbon.py` for the shape.
- Never relax a bound merely to get green. If the underlying data looks wrong rather than changed, leave it red and raise it.

## Worked example (2026-07-28)

The GO pipeline migration replaced the legacy per-database GAFs with MOD-centric ones carrying smaller gene coverage. GOlr is a faithful load of the new files — zebrafish 15,163 genes in both `DANRE-mod.gaf.gz` and the index; fly 12,392 genes and 161,834 annotations in both.

Five tests failed. Four were a single dead identifier, `ZFIN:ZDB-GENE-980526-388` (`bmp2a`) — a live, unmerged ZFIN gene, simply absent from the new `-mod` file while present in `-uniprot`, i.e. the mapping-issue row of the table above. The fifth was `FB:FBgn0051155`, whose molecular-function annotations went from 5 to 2.

Fixed in #171 by repointing to `ZFIN:ZDB-GENE-990415-72` and `ZFIN:ZDB-GENE-010302-1`, plus one commented threshold change. Full investigation: #170.

Two things that cost time and are worth avoiding:

- The first diagnosis blamed GOlr for dropping data, because it compared the index against the superseded legacy GAF. Confirm *which* artifact the serving system is built from before concluding it is lossy.
- The first fix validated only `tests/unit/`, so the integration `.feature` fixture failed in CI. Run `make test`, or at least check both suites.
