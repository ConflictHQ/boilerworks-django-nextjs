# Boilerworks Bootstrap

This is the primary conventions document for the Boilerworks Django platform. All agent shims (`CLAUDE.md`, `AGENTS.md`, `GEMINI.md`) point here.

An agent given this document and a business requirement should be able to generate correct, idiomatic code without exploring the codebase.

---

## What's Already Built

| Layer | What's there |
|---|---|
| Auth | Session-based auth (auth1), admin login, rate limiting on auth endpoints |
| Data | Postgres, `Tracking` base model (created/updated/deleted by + at, version, soft deletes, audit history on all models) |
| API | GraphQL (Strawberry), DRF, file upload (MinIO local / S3 prod) |
| Permissions | django-role-permissions, per-model/per-field permission checks, GQL middleware |
| Async | Celery worker + beat, Redis broker, DatabaseScheduler |
| Search | OpenSearch, ProfileDocument, signals for incremental indexing, `make reindex` |
| Email | django-ses (prod), Mailpit (local) |
| Feature flags | django-constance, admin UI, fieldsets |
| Rate limiting | django-ratelimit on auth endpoints |
| Admin | Custom dark theme, BaseCoreAdmin (import/export, tracking fields), DJDT |
| Rule engine | Conditions + Actions + RuleProviderMixin, Celery-backed evaluation |
| State machine | DFA model, cron-scheduled transitions via Celery beat |
| Infra | Docker Compose: postgres, redis, opensearch, minio (S3), celery-worker, celery-beat, mailpit, ui |
| CI | GitHub Actions: lint (pre-commit) + tests (postgres + redis services) |
| Seed | `make seed`, numbered fixtures, `--flush` flag |

---

## App Structure

| App | Purpose |
|---|---|
| `auth1` | Session-based authentication, login views, rate limiting |
| `core` | User, Profile, Address, Notification, ResourceFile, OpenSearch setup, telemetry, signals |
| `core_logs` | Permission access logging (`PermissionAccessLog`) |
| `core_rule_engine` | Rule definitions, conditions, actions, model signal triggers |
| `core_ui` | UI components, file processors |
| `organization` | Organization + OrganizationMember models, member status |
| `pushnotif` | Push notifications, delivery methods, Celery tasks |
| `scheduled_task` | Background scheduled tasks |
| `testdata` | Dev fixtures, `seed` management command |

---

## Conventions

### Models

All business models inherit from one of:

**`Tracking`** (abstract) — use for any model that needs audit trails:
```python
from core.models import Tracking

class Invoice(Tracking):
    amount = models.DecimalField(...)
```
Provides: `version` (auto-increments on save), `created_at/by`, `updated_at/by`, `deleted_at/by`, `history` (simple_history).

**`BaseCoreModel(Tracking)`** (abstract) — use for named, addressable entities:
```python
from core.models import BaseCoreModel

class Product(BaseCoreModel):
    price = models.DecimalField(...)
```
Adds: `guid` (UUID, external identifier), `name`, `slug` (auto-generated, unique), `description`. Use `slug` as the natural key. Never expose integer PKs in the API — use `guid` or the relay global ID.

**Soft deletes:** set `deleted_at` and `deleted_by`, don't call `.delete()` on business objects.

---

### GraphQL (Strawberry)

Each app has: `appname/schema/types.py`, `queries.py`, `mutations.py`, `__init__.py`

Schema assembly: `config/schema.py` merges all apps. View: `core/schema/views.py`.

**Types:**
```python
import strawberry_django
from strawberry.types import Info
from core.schema.common import permission_filtered_queryset

@strawberry_django.type(Product)
class ProductType:

    @classmethod
    def get_queryset(cls, queryset, info: Info):
        return permission_filtered_queryset(queryset, info)
```

**Queries:**
```python
import strawberry
from strawberry.types import Info

@strawberry.type
class Query:

    @strawberry.field
    def products(self, info: Info, search: str = '') -> list[ProductType]:
        if not info.context.user.is_authenticated:
            raise GraphQLError('Authentication required')
        qs = Product.objects.all()
        if search:
            qs = qs.filter(name__icontains=search)
        return qs
```

**Mutations — always return `MutationResult` (ok + errors):**
```python
import strawberry
from strawberry.types import Info
from core.schema.common import MutationResult
from core.schema.mutations.base import restricted_serializer_mutate

@strawberry.type
class Mutation:

    @strawberry.mutation
    def create_product(self, info: Info, name: str, price: str) -> MutationResult:
        Product.p('model').add.check(info.context.user)
        return restricted_serializer_mutate(
            ProductSerializer, Product, info,
            data={'name': name, 'price': price},
        )
```

**Context:** Resolvers access user, dataloaders, and permissions via `info.context` (`StrawberryContext` from `core/schema/context.py`):
```python
info.context.user                    # authenticated user
info.context.organization            # user's active org
info.context.request_language        # preferred language
info.context.request_timezone        # user timezone or SYSTEM_TIME_ZONE
info.context.check_permission(...)   # cached permission check
info.context.get_loader(name, fn)    # get/create dataloader
```

**Auth check at the top of every resolver and mutation** — no exceptions.

---

### Permissions

Permissions are defined in `config/permissions.py` using `ModelPermissions`. The generated enum lives in `config/roles_gen.py` (regenerate with `make perms`).

Check permissions via:
```python
from config.roles_gen import P

P.PRODUCT_VIEW.check(info.context.user)          # raises PermissionDenied if denied
P.PRODUCT_CHANGE.check(info.context.user, False)  # returns False instead of raising
```

Define permissions in `config/permissions.py`:
```python
from config.permissions import ModelPermissions, FieldPermissions
from core.utils.permissions import AbstractPermissions

class ProductPermissions(ModelPermissions):
    model = FieldPermissions(
        view=P.PRODUCT_VIEW,
        add=P.PRODUCT_ADD,
        change=P.PRODUCT_CHANGE,
        delete=P.PRODUCT_DELETE,
    )
```

Assign permissions to groups in admin, never directly to users.

---

### Admin

All admin classes inherit from `BaseCoreAdmin`:
```python
from core.utils.admin import BaseCoreAdmin
from django.contrib import admin

@admin.register(Product)
class ProductAdmin(BaseCoreAdmin):
    list_display = ('name', 'slug', 'created_at')
    search_fields = ('name', 'slug')
```

`BaseCoreAdmin` automatically handles: `created_by/updated_by/deleted_by` as raw ID fields, audit fields as readonly, `save_model` setting created/updated by. Uses `ImportExportMixin` — all models get CSV import/export in admin.

---

### Celery Tasks

Tasks live in `appname/tasks.py`. Use `@app.task()` and import models inside the function:
```python
from config.celery import app

@app.task()
def process_invoice(invoice_id):
    from invoicing.models import Invoice
    invoice = Invoice.objects.get(id=invoice_id)
    invoice.process()
```

For retryable tasks:
```python
@app.task(bind=True, max_retries=3)
def send_notification(self, user_id):
    try:
        ...
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
```

Async actions from workflow transitions go through `appname/tasks.py`.

---

### Tests

Use `schema.execute_sync()` for GraphQL tests:
```python
from django.test import TestCase
from config.schema import schema
from core.schema.context import StrawberryContext

class ProductTest(TestCase):

    def setUp(self):
        from organization.models import Organization, OrganizationMember
        self.org = Organization.objects.create(name='TestOrg')
        self.user = User.objects.create_superuser(username='test', email='t@t.com', password='x')
        OrganizationMember.objects.create(organization=self.org, member=self.user, is_active=True)
        self.user.profile.active_organization = self.org
        self.user.profile.save()

    def _context(self):
        from unittest.mock import MagicMock
        request = MagicMock()
        request.user = self.user
        request.session = {}
        request.headers = {}
        return StrawberryContext(request)

    def test_create_product(self):
        result = schema.execute_sync(
            'mutation { createProduct(name: "Widget", price: "9.99") { ok errors { field messages } } }',
            context_value=self._context(),
        )
        self.assertIsNone(result.errors)
        self.assertTrue(result.data['createProduct']['ok'])
```

For model-only tests use `django.test.TestCase` directly. No hardcoded values, no `pass` blocks, no fallback assertions.

---

### Code Style

This project follows **PEP 8** strictly, enforced by flake8 and isort pre-commit hooks. Key rules:
- Max line length: 140 characters (configured in `.flake8`)
- Imports sorted by isort; run `pipenv run isort .` to fix
- Two blank lines between top-level definitions
- Docstrings only where logic isn't self-evident

Run `make lint` or `pipenv run pre-commit run --all-files` before committing.

---

## Adding a New App

```bash
# 1. Create the app
./run.sh manage startapp myapp

# 2. Register in config/settings.py INSTALLED_APPS (before "End of Boilerworks")

# 3. Create models inheriting from Tracking or BaseCoreModel

# 4. Create migrations
make migrations

# 5. Create admin (inherit BaseCoreAdmin)

# 6. Create schema: myapp/schema/__init__.py
#    Wire into config/schema.py

# 7. Write tests extending BaseTest
make test
```

---

## Ports (local)

| Service | URL |
|---|---|
| Django API | http://localhost:8000 |
| Next.js UI | http://localhost:3000 |
| Django Admin | http://localhost:8000/app/admin/ |
| GraphQL | http://localhost:8000/app/gql/config/ |
| Health | http://localhost:8000/health/ |
| Mailpit | http://localhost:8025 |
| OpenSearch | http://localhost:9200 |
| Postgres | localhost:5432 |
| Redis | localhost:6379 |
| Django metrics | http://localhost:8000/metrics |
| Postgres metrics | http://localhost:9187/metrics |
| Redis metrics | http://localhost:9121/metrics |
| MinIO S3 API | http://localhost:9000 |
| MinIO Console | http://localhost:9001 (minioadmin/minioadmin) |
| Flower (Celery) | http://localhost:5555 |

---

## Common Commands

```bash
make up           # Start the stack
make build        # Build and start
make down         # Stop the stack
make migrate      # Run migrations
make migrations   # Create new migrations (add app=<name> to scope)
make seed         # Load dev fixtures
make test         # Run tests
make lint         # Run flake8 + isort checks
make schema       # Export GraphQL SDL
make shell        # Shell into Django container
make logs         # Tail Django logs
make perms        # Regenerate config/roles_gen.py
make reindex      # Rebuild OpenSearch indices
make superuser    # Create Django superuser
make ps           # Show container status
```
