# AGENTS.md for go-fastapi

FastAPI endpoint for GO services

## Repo management

This repo uses `python` for managing dependencies. Never use commands like `pip` to add or manage dependencies.

Layout:

 * `app/` - Code goes here

Best practice:

* Use doctests liberally - these serve as both explanatory examples for humans and as unit tests
* For longer examples, write pytest tests
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
