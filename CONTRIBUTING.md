# Contributing to DriftSense

Thanks for taking the time to contribute! This is a personal project with a professional bar: small PRs, clear tests, friendly tone. By participating, you agree to our [Code of Conduct](./CODE_OF_CONDUCT.md).

---

## TL;DR checklist

* Open an issue first for non‑trivial changes.
* Use Docker for dev if possible (fast, reproducible).
* Run **`make test`** locally before opening a PR.
* Keep PRs focused; add/adjust docs as needed.
* Prefer Conventional Commits in messages (see below).

---

## Getting started

### 1) Fork & clone

```bash
git clone https://github.com/furk4neg3/DriftSense.git
cd DriftSense
```

### 2) Workflow

You can find the workflow on readme. I recommend using Docker workflow.

---


## Dev flow

### Branches

Use short, descriptive names:

* `feat/<thing>` new feature
* `fix/<bug>` bug fix
* `docs/<topic>` docs only
* `chore/<task>` CI/build/tooling
* `test/<area>` tests

### Commit messages (Conventional Commits)

```
<type>(optional-scope): short summary

body (optional)
```

**Types:** `feat`, `fix`, `docs`, `test`, `chore`, `refactor`, `perf`, `build`, `ci`

### Code style

* Keep functions small and typed where practical.
* Prefer straightforward naming over cleverness.
* If configured, run formatters/linters before committing:

```bash
make format  # optional target if available
# or manually
python -m black .
python -m ruff check . --fix || true
```

### Tests

* Add/adjust tests for your changes.
* Run locally:

```bash
make demo
# or
pytest -q
```

### Pull requests

* Keep PRs under \~400 lines of diff when possible.
* Fill a short description with **what/why**, screenshots/logs if relevant.
* Link the related issue.

---

## Proposing significant changes

Open an issue labeled **proposal** with a short design note:

* Problem, rough approach, alternatives
* Impact on config/backward compatibility

---

## Security

Please avoid filing public issues for sensitive bugs. Email **[nizamfurkanegecan@gmail.com](mailto:nizamfurkanegecan@gmail.com)** and we’ll coordinate a fix.

---

## License & attribution

By contributing, you agree your contributions are licensed under the project’s license (MIT). You confirm you have the right to contribute the content.

---

Thanks again for helping make DriftSense better! 🚀
