# Contributing to Boilerworks

Thanks for your interest in contributing. This document covers everything you need to get started.

---

## Getting started

**Requirements:** Docker Desktop only — Python, pipenv, and Node run inside containers.

```shell
git clone https://github.com/ConflictHQ/boilerworks-django.git
cd boilerworks-django
./bootstrap.sh   # generates local.env, builds images
./run.sh         # start the stack
```

Read [`bootstrap.md`](bootstrap.md) before writing any code. It covers models, GraphQL, permissions, Celery, tests, and code style.

---

## Making changes

### Branching

```
main          — stable, always deployable
feature/...   — new features
fix/...       — bug fixes
chore/...     — tooling, deps, docs
```

Open a PR against `main`.

### Code style

This project enforces **PEP 8** via flake8 and isort (max line length: 140).

```shell
pipenv run isort .                          # fix import order
pipenv run pre-commit run --all-files       # run all hooks
```

Pre-commit hooks run automatically on `git commit`. CI will reject non-compliant code.

### Tests

```shell
make test
```

All new features and bug fixes need tests. Use `BaseTest` for GraphQL tests (see `bootstrap.md`).

### Migrations

If you change a model, create a migration before committing:

```shell
./run.sh makemigrations <appname>
```

The pre-commit hook will catch missing migrations.

---

## Pull requests

- Keep PRs focused — one feature or fix per PR
- Include tests
- Run `make lint` and `make test` before opening
- Fill in the PR template
- Reference any related issues with `Closes #123`

---

## Reporting issues

Use the [issue templates](.github/ISSUE_TEMPLATE/) — bug reports and feature requests have separate forms.

For security vulnerabilities, see [`SECURITY.md`](SECURITY.md) — do not open a public issue.

---

## Questions

Open a [GitHub Discussion](https://github.com/ConflictHQ/boilerworks-django/discussions) for questions, ideas, or general feedback.
