# Boilerworks

Django + Next.js platform boilerplate. Session auth, GraphQL, Celery, OpenSearch, role-based permissions, audit trails, rule engine, and state machine — all wired up and ready to extend.

See [`bootstrap.md`](bootstrap.md) for conventions, patterns, and how to add new features.

---

## Stack

| Layer | Tech |
|---|---|
| Backend | Django, graphene-django, DRF, Celery, Postgres, Redis, OpenSearch |
| Frontend | Next.js (static), Apollo Client, TypeScript |
| Infra | Docker Compose — all services containerised |

---

## Getting started

**Requirements:** Docker Desktop only. Python, pipenv, and Node run inside containers.

```shell
# First time
./bootstrap.sh

# Daily
./run.sh          # start the stack
./run.sh stop     # stop
./run.sh logs     # tail Django logs
./run.sh health   # per-service health check
```

---

## Local URLs

| Service | URL |
|---|---|
| App | http://localhost:8000/app/ |
| Admin | http://localhost:8000/app/admin/ |
| GraphQL | http://localhost:8000/app/gql/config/ |
| Health | http://localhost:8000/health/ |
| Mailpit | http://localhost:8025 |
| Django metrics | http://localhost:8000/metrics |

---

## Common commands

```shell
./run.sh migrate               # run migrations
./run.sh makemigrations <app>  # create new migration
./run.sh schema                # export GraphQL schema
./run.sh perms                 # regenerate config/roles_gen.py
./run.sh shell                 # Django Python shell
./run.sh manage <cmd>          # any manage.py command
```

Or via Make (inside the Django container):

```shell
make test       # run tests
make seed       # load dev fixtures
make lint       # flake8 + isort
make reindex    # rebuild OpenSearch indices
```

---

## Code quality

This project enforces **PEP 8** via flake8 and isort pre-commit hooks (max line length: 140).

```shell
# Fix import order
pipenv run isort .

# Check everything
make lint
# or: pipenv run pre-commit run --all-files
```

Run `make lint` before pushing. The CI pipeline will reject non-compliant code.

---

## Permissions

Permissions are group-based — never assign them directly to users.

1. Define permissions in `config/permissions.py`
2. Regenerate the enum: `./run.sh perms`
3. Assign to groups via Django admin
4. Check in code: `P.FOO_VIEW.check(info.context.user)`

See [bootstrap.md](bootstrap.md) for the full pattern.

---

## Frontend

```shell
# Compile GraphQL types (backend must be running)
npm run compile
```

The frontend is compiled to a static app (no SSR). Auth is handled by Django session via the `auth1` app.
