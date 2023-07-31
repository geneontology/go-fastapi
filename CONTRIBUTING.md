### Running Tests

To run the tests, run

```bash
make test
```

### Linting, Formatting, and Spell Check

To run the linter, formatter, and spell check, run

```bash
poetry run tox -e codespell,lint-fix,format
```
* codespell checks app/ and tests/ for spelling mistakes
* lint-fix will run lint on the app/ and tests/ directory looking for things it can automatically fix - will also
output things to fix that it can't fix on its own.
* 




### Example Deployment Locally:

1) clone the repo
`git clone https://github.com/geneontology/go-fastapi`
2) install requirements into a virtual environment 
`poetry install`
3) start the API server
`make start`
4) run the tests
`make test`




