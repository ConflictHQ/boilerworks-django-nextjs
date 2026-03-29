# Boilerworks

Production-ready Django + Next.js boilerplate for building enterprise applications. Forms engine, workflow engine, visual builders, session auth, GraphQL, Celery, role-based permissions, audit trails, and more — all wired up and ready to extend.

See [`bootstrap.md`](bootstrap.md) for conventions, patterns, and how to add new features.

---

## Stack

| Layer | Tech |
|---|---|
| Backend | Django 5, Strawberry GraphQL, DRF, Celery, Postgres, Redis, OpenSearch |
| Frontend | Next.js 16 (App Router), Apollo Client, TypeScript, Tailwind CSS, shadcn/ui |
| Infra | Docker Compose — all services containerised |

---

## Features

### Forms Engine
- **JSON Schema-based** form definitions with 21+ field types
- Visual form builder in **Django admin** (drag-and-drop, per-type config, JSON toggle)
- Visual form builder in **Next.js** (React, live preview, @dnd-kit)
- Dynamic renderer (`DynamicForm`) that generates forms from schema at runtime
- Field types: text, textarea, number, date, time, email, URL, select, multi-select, radio, file upload, signature, rating, scale, PIN, percentage split, section headers, page breaks, images
- Conditional logic engine (show/hide/require/calculate based on field values)
- Versioned definitions with publish/archive lifecycle
- Form submissions with validation, scoring, and prefill

### Workflow Engine
- **DB-configurable state machines** (states, transitions, conditions, actions)
- Visual workflow builder in **Django admin** (state/transition editor with validation)
- Visual workflow builder in **Next.js** (ReactFlow canvas with drag-and-drop)
- State config: attached forms, assigned roles, colors, initial/final flags
- Transition conditions: role checks, field comparisons, auth checks
- Transition actions: notifications, emails, webhooks, field updates
- Async action execution via **Celery** (Temporal.io integration planned)
- GenericForeignKey — attach workflows to any Django model
- Immutable audit trail (TransitionLog)

### Auth & Permissions
- Django session auth via `auth1` app (Auth0 SSO flow)
- Frontend auth gate with entry-point redirects (frontend login → frontend, admin login → admin)
- Group-based permissions (never assigned directly to users)
- Field-level permission filtering on GraphQL types
- Permission guard components (server + client)

### GraphQL API
- **Strawberry GraphQL** with strawberry-graphql-django
- Async dataloaders with `sync_to_async`
- Relay-style connections with `total_count`
- Mutation audit logging via schema extension
- Rate limiting on GraphQL endpoints

### Frontend
- Next.js 16 App Router with server + client components
- Apollo Client with SSR hydration (`@apollo/client-integration-nextjs`)
- shadcn/ui component library + Tailwind CSS
- Dashboard with chart components (Recharts — area, bar, donut)
- Data tables with server-side pagination, filtering, sorting
- 7-language i18n (next-intl)
- Dark mode, breadcrumbs, sidebar navigation
- Sentry error tracking, global error boundary

### Infrastructure
- Docker Compose with all services (Django, Postgres, Redis, Next.js, Celery, Flower, OpenSearch, MinIO, Mailpit)
- Feature toggle system (`config/features.py`) with Docker Compose profiles
- Health check endpoint (`/health/`)
- Prometheus metrics endpoint (`/metrics`)
- OpenTelemetry tracing (configurable exporter)
- S3-compatible file storage via MinIO

---

## Getting Started

**Requirements:** Docker Desktop only. Python, pipenv, and Node run inside containers.

```shell
# Clone and start
git clone https://github.com/ConflictHQ/boilerworks-django-nextjs.git
cd boilerworks-django-nextjs

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
| Frontend | http://localhost:3000 |
| Django Admin | http://localhost:8000/app/admin/ |
| GraphQL Playground | http://localhost:8000/app/gql/config/ |
| Health Check | http://localhost:8000/health/ |
| Flower (Celery) | http://localhost:5555 |
| Mailpit | http://localhost:8025 |
| MinIO Console | http://localhost:9001 |
| Metrics | http://localhost:8000/app/metrics/ |

---

## Common Commands

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

## Code Quality

Backend enforces **PEP 8** via flake8 and isort (max line length: 140).
Frontend uses **Prettier** with `prettier-plugin-tailwindcss`.

```shell
# Backend
make lint

# Frontend
npm run format:check
npm run format
```

---

## Permissions

Permissions are group-based — never assign them directly to users.

1. Define permissions in `config/permissions.py`
2. Regenerate the enum: `./run.sh perms`
3. Assign to groups via Django admin
4. Check in code: `P.FOO_VIEW.check(info.context.user)`

See [bootstrap.md](bootstrap.md) for the full pattern.

---

## History

Boilerworks has been built and battle-tested in production at [Conflict](https://conflict.com) for 5 years. Git history was scrubbed for open-source publication.

---

## Contributing

We'd love for people to use Boilerworks, extend it, and make it better. File issues, open PRs, or start a discussion. See [CONTRIBUTING.md](CONTRIBUTING.md) if it exists, or just jump in.

---

## License

MIT

---

Boilerworks is a [Conflict](https://weareconflict.com) brand. CONFLICT is a registered trademark of Conflict LLC.
