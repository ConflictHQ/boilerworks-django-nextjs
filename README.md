# Boilerworks

Production-ready Django + Next.js boilerplate for building enterprise applications. Forms engine, workflow engine, visual builders, session auth, GraphQL, Celery, role-based permissions, audit trails, and more — all wired up and ready to extend.

See [`bootstrap.md`](bootstrap.md) for conventions, patterns, and how to add new features.

---

## Stack

| Layer | Tech |
|---|---|
| Backend | Django 6, Strawberry GraphQL, DRF, Celery, Postgres, Redis, OpenSearch |
| Frontend | Next.js 16 (App Router), Apollo Client, TypeScript, Tailwind CSS, `@calliopelabs/ui`, shadcn/ui |
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
- [`@calliopelabs/ui`](https://www.npmjs.com/package/@calliopelabs/ui) (the Calliope AI design system) + Tailwind CSS, shadcn/ui for what the library lacks
- Dashboard with chart components (Recharts — area, bar, donut)
- Embedded Apache Superset dashboards (`/analytics`) through backend-issued guest tokens
- Data tables with server-side pagination, filtering, sorting
- 7-language i18n (next-intl)
- Appearance (ground, accent, light or dark), breadcrumbs and sidebar navigation from the library
- Storybook 10 with an a11y gate in `npm test`
- Sentry error tracking, global error boundary

### Infrastructure
- Docker Compose with all services (Django, Postgres, Redis, Next.js, Celery, Flower, OpenSearch, MinIO, Mailpit, Superset)
- Feature toggle system (`config/features.py`) with Docker Compose profiles
- Health check endpoint (`/health/`)
- Prometheus metrics endpoint (`/metrics`)
- OpenTelemetry tracing (configurable exporter)
- S3-compatible file storage via MinIO

---

## The Calliope AI happy path

This template builds on the Calliope AI design system and platform. A new app made from it starts on the shared UI library, deploys on Astrolift, shows its Storybook in the Calliope AI UX front door, and receives library upgrades automatically.

### What the template ships

- **The design system.** `frontend/` depends on [`@calliopelabs/ui`](https://www.npmjs.com/package/@calliopelabs/ui). `app/globals.css` imports its Tailwind preset (tokens, theme map, `dark:` on `data-mode`, base layer). The root layout renders `AppearanceScript` in `<head>` and mounts `AppearanceProvider` and `UIProvider`, the latter through `ui-app/providers/UiEnvironment.tsx`, which gives the library `next/link` and translates every string it renders from the `ui` namespace of `messages/<locale>.json`.
- **The product.** `ui-app/product.ts` defines the app with `defineProduct`: a neutral `boilerworks` brand and the navigation model the sidebar and breadcrumb read.
- **The shell and patterns from the library.** `AppShell`, `Sidebar`, `BrandMark`, `UserMenu`, `Breadcrumbs`, `PageHeader`, `DataTable`, `EmptyState`, `ErrorState`, `LoadingState`, `StatusBadge`, `AppearancePicker`, and the primitives `Button`, `Input`, `Checkbox`, `DropdownMenu`, `Popover`, `Skeleton`, `AlertDialog` and `Drawer`.
- **The app's own layer, `ui-app/`.** The shadcn components the library does not have (`primitives/`), the signed-in frame (`shell/AppFrame.tsx`), and the two `TableController`s for the library `DataTable` (`table/`: `paginatedController` over `usePaginatedQuery`, `useLocalTable` for rows already in hand).
- **A Storybook with gates.** `npm run storybook` in `frontend/` (Storybook 10, `@storybook/nextjs-vite`). `npm test` renders every story with the a11y addon's WCAG A and AA checks and fails on a violation, and requires a sibling story for every component in `ui-app/`.
- **Astrolift manifests.** Astrolift builds one image per app, so there are three: `astrolift.toml` for the backend (api, Celery worker and beat from `backend/Dockerfile`, Postgres, Redis), `frontend/astrolift.toml` for the web (`frontend/Dockerfile`, Next.js standalone), and `storybook/` (Dockerfile, nginx, `astrolift.toml`) for the Storybook.
- **Upgrades.** `.github/dependabot.yml` checks `frontend/` daily and puts `@calliopelabs/*` releases in their own pull request.

### Rename the product

1. `frontend/ui-app/product.ts`: set `id` (lowercase slug, also the appearance storage key) and `name`; pick an `accent` (a family accent or the product's own) and a `sidebar` colour, or spread a shipped brand (`astroliftBrand`, `zentinelleBrand`, ...). Edit `NAV` for the app's areas and rows; each row's `key` is its message key in the `nav` namespace.
2. `frontend/ui-app/shell/AppFrame.tsx`: the brand mark (a lucide icon by default; an `<img>` of the logo works).
3. Replace `boilerworks-app` in `astrolift.toml`, `frontend/astrolift.toml` and `storybook/astrolift.toml` (`name`, `slug`, `display_name`, `repo`, the managed service names).

### Deploy with Astrolift

```shell
astro app register --project-id <uuid> --source-repo <org>/<repo>
astro app register -f frontend/astrolift.toml --manifest-path frontend/astrolift.toml \
  --project-id <uuid> --source-repo <org>/<repo>
astro app register -f storybook/astrolift.toml --manifest-path storybook/astrolift.toml \
  --project-id <uuid> --source-repo <org>/<repo>
astro app secrets create DJANGO_SECRET_KEY boilerworks-app --stdin   # and the others astrolift.toml lists
```

Pushes to `main` deploy through the managed workflow. The browser calls the backend directly, so the web's `NEXT_PUBLIC_API_ROOT` is the api's public URL; it is compiled into the bundle, so set it as a build argument of the web app. The backend's cache and Celery URLs are secrets made from the Redis binding's `REDIS_URL` (see `astrolift.toml`). Build and check the images locally:

```shell
docker build -t app-web --build-arg NEXT_PUBLIC_API_ROOT=http://localhost:8000 frontend
docker build -f storybook/Dockerfile -t app-storybook .
docker run --rm -p 8080:8080 app-storybook        # http://localhost:8080, /healthz answers ok
```

### Add the Storybook to the front door

The front door, [calliopeai/calliope-ux](https://github.com/calliopeai/calliope-ux), composes each app's Storybook as a section. Once the Storybook app is deployed, add an entry to its `catalogs.json` and push:

```json
{
  "id": "boilerworks-app",
  "title": "Boilerworks",
  "group": "web",
  "kind": "storybook",
  "repo": "ConflictHQ/boilerworks-django-nextjs",
  "app": "storybook-boilerworks-app",
  "upstream": "web.conflict-storybook-boilerworks-app.svc.cluster.local:8080"
}
```

`upstream` is `<workload>.conflict-<app slug>.svc.cluster.local:8080`; the workload here is `web`.

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
| Superset (`analytics` profile) | http://localhost:8088 (admin/admin, local only) |
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

## Analytics (Superset)

Embedded analytics use [Apache Superset](https://superset.apache.org/) and its
[Embedded SDK](https://www.npmjs.com/package/@superset-ui/embedded-sdk). The
browser never holds a Superset credential:

1. The frontend lists dashboards with the `supersetDashboards` query (title,
   order, the embedded dashboard UUID and the Superset domain).
2. `SupersetDashboard` in `frontend/ui-app/analytics/` mounts the dashboard
   with `embedDashboard()`. Its `fetchGuestToken` calls the
   `supersetGuestToken` mutation, on mount and before each token expires.
3. The backend (`core/utils/api/superset_rest_client.py`) signs in to Superset
   as a service account (`/api/v1/security/login`), takes a CSRF token and
   asks `/api/v1/security/guest_token/` for a token scoped to that one
   dashboard, with the dashboard's row-level security clause, if it has one.

Access is the `view_supersetdashboard` permission (assign it to groups);
`FEATURE_SUPERSET=false` removes the query and mutations from the schema.

### Row-level security

A dashboard's `rls_clause` (admin, or `superset_embed --rls-clause`) is added
to every guest token issued for it. `{organization_guid}` becomes the user's
active organization guid, quoted, so a dataset with an `organization_guid`
column can be scoped with:

```
organization_guid = {organization_guid}
```

A user with no active organization gets `1 = 0` and sees no rows. Leave the
clause empty for dashboards that are not tenant scoped.

### Local Superset

Superset runs in the opt-in `analytics` compose profile (the official
`apache/superset` image plus the Postgres driver, `docker/superset/`):

```shell
docker compose -f docker/docker-compose.yaml --profile analytics up -d
make superset-embed dashboard=boilerworks-sample   # enable embedding, register it
```

On first start it creates a local admin (admin/admin), the service account
from `SUPERSET_USERNAME` / `SUPERSET_PASSWORD` in `backend/config/local.env`
(`bootstrap.sh` generates the password) and a sample dashboard,
`boilerworks-sample`, over the local `auth_user` table. Open
http://localhost:3000/analytics to see it embedded. For your own dashboards,
build them at http://localhost:8088 and run `make superset-embed
dashboard=<id or slug>`.

### Hosted Superset

Point the backend at a self-hosted or managed Superset (the local profile
pins 6.1.0) through `backend/config/local.env` or the
deployment's secrets:

| Variable | Purpose |
|---|---|
| `SUPERSET_URL` | Superset as the backend reaches it (API calls) |
| `SUPERSET_PUBLIC_URL` | Superset as the browser reaches it (the iframe); defaults to `SUPERSET_URL` |
| `SUPERSET_USERNAME` / `SUPERSET_PASSWORD` | Service account for guest tokens; env or secrets only |
| `SUPERSET_EMBED_ALLOWED_DOMAINS` | Comma-separated origins allowed to frame dashboards (set by `superset_embed`) |

On the Superset side: turn on the `EMBEDDED_SUPERSET` feature flag, give the
service account a role with only "can grant guest token" and dashboard
embedding, set `GUEST_ROLE_NAME` to a role that can read the embedded
dashboards, and allow the app's origin in Talisman's `frame-ancestors`. The
local `docker/superset/superset_config.py` shows the flags; it turns Talisman
off, which is for local use only.

### Migrating from Metabase

Earlier versions embedded Metabase. Migration `core.0010` is a clean break:
Metabase card and dashboard ids have no Superset equivalent, so it drops the
Metabase tables, their history and permissions, and creates
`SupersetDashboard`. Export any Metabase chart rows you need first, rebuild
the dashboards in Superset, register each with `make superset-embed`, and
remove `METABASE_*` from your environment. Rotate any `METABASE_SECRET_KEY`
that ran on an earlier version of this template: settings logged it at
startup.

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

Boilerworks has been built and battle-tested in production at [CONFLICT](https://weareconflict.com) for 5 years. Git history was scrubbed for open-source publication.

---

## Contributing

We'd love for people to use Boilerworks, extend it, and make it better. File issues, open PRs, or start a discussion. See [CONTRIBUTING.md](CONTRIBUTING.md) if it exists, or just jump in.

---

## License

MIT

---

Boilerworks is a [CONFLICT](https://weareconflict.com) brand. CONFLICT is a registered trademark of CONFLICT LLC.
