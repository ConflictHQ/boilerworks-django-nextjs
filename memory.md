# Boilerworks Memory

This file is the **AI context seed** for the Boilerworks Django platform. It captures decisions, constraints, and non-obvious facts that are not derivable from reading the code.

For conventions and patterns, see [`bootstrap.md`](bootstrap.md).

---

## Platform purpose

Multi-tenant SaaS platform. Django backend + Next.js frontend. Organisations are the top-level tenancy unit (`organization` app). Users belong to one or more organisations via `OrganizationMember`.

---

## Key architectural decisions

| Decision | Why |
|---|---|
| GraphQL (Strawberry) as primary API | `strawberry-graphql` + `strawberry-graphql-django` (migrated from graphene in #14); schema assembled in `config/schema.py`, served at `/gql/config/`; REST (DRF) exists for specific endpoints (file upload, webhooks) |
| Auth0 OIDC handled by the backend | The `auth1` app drives the Auth0 login flow server-side (authlib); the backend issues its own token, and `Auth0SessionMiddleware` accepts it via `Authorization: Bearer`/`Session` headers. The frontend never talks to Auth0 directly |
| `Tracking` on all business models | Audit trail is a hard requirement; `simple_history` provides row-level history |
| Soft deletes via `deleted_at/by` | Compliance requirement; never hard-delete business objects |
| `guid` (UUID) as external identifier | Integer PKs are never exposed in APIs; use `guid` or relay global ID |
| django-role-permissions for RBAC | Group-based; permissions are never assigned directly to users |
| Celery + Redis for async | Rule engine and scheduled state machine transitions run through Celery beat |
| OpenSearch for full-text search | Signals drive incremental indexing; `make reindex` for full rebuilds |
| `config/roles_gen.py` is generated | Do not edit by hand; regenerate with `make perms` after changing `config/permissions.py` |

---

## Things that bite newcomers

- **Never call `.delete()` on business objects** — set `deleted_at` + `deleted_by` instead.
- **Never expose integer PKs in APIs** — always use `guid` or relay node ID.
- **Auth check is mandatory in every resolver and mutation** — the GraphQL middleware does not enforce this automatically.
- **`roles_gen.py` is generated** — editing it manually will be overwritten by `make perms`.
- **Migrations are checked in pre-commit** — you must create a migration before committing model changes.
- **`DEFAULT_AUTO_FIELD = BigAutoField`** — use `BigAutoField` (not `AutoField`) in manual migrations.
- **isort + flake8 run on pre-commit** — `pipenv run isort .` before committing to avoid failures.
- **Max line length is 140** (not 79 or 88) — configured in `.flake8`.

---

## Infrastructure topology

```
┌─────────────────────────────────────────────────────┐
│  Docker Compose (docker/)                           │
│                                                     │
│  django ──► postgres                                │
│     │                                               │
│     └──► redis ──► celery-worker                   │
│                └──► celery-beat                     │
│                                                     │
│  opensearch  mailpit  ui (Next.js)                  │
│  postgres-exporter  redis-exporter                  │
└─────────────────────────────────────────────────────┘
```

All services run in Docker. Python, pipenv, and Node are not required on the host — only Docker Desktop.

---

## Permissions model

```
User → (many) Groups → (many) Permissions
```

Permissions are defined in `config/permissions.py` as `ModelPermissions` subclasses, then compiled into the `P` enum in `config/roles_gen.py`. Check via `P.FOO_VIEW.check(user)`. Assign via Django admin (Groups UI).

---

## Frontend notes

- Next.js 16 App Router with SSR/RSC (no static export). Server Components query GraphQL via `getClient()`; client components use hooks.
- Apollo Client 4 with `@apollo/client-integration-nextjs` (separate server and client Apollo clients); unauthenticated responses redirect to login.
- 7 supported languages via i18n.
- Auth: login redirects to the backend's `/app/auth1/login` (Auth0 OIDC happens server-side); the callback returns a backend-issued token stored in `localStorage` (`jwt`) and an `httpOnly` cookie (`backend_jwt`) for SSR reads. `lib/auth/auth0.ts` is intentionally a null stub — the `@auth0/nextjs-auth0` package is not used at runtime.

---

## Test fixtures

`make seed` loads numbered fixtures from `testdata/`. The `BaseTest` superuser is `testuser` (password set in fixture). Use `make seed --flush` to reset.

---

## Common gotchas with the rule engine

- Rules are evaluated via Celery tasks, not synchronously.
- `RuleProviderMixin` wires model signals to trigger rule evaluation.
- Conditions use `durable.lang` (the `m` symbol must be imported explicitly).
- Actions live in `core_rule_engine/rules/common.py`.
