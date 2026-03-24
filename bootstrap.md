# Boilerworks Bootstrap

This is the primary conventions document for the Boilerworks Django platform. All agent shims (`CLAUDE.md`, `AGENTS.md`, `GEMINI.md`) point here.

An agent given this document and a business requirement should be able to generate correct, idiomatic code without exploring the codebase.

---

## What's Already Built

| Layer | What's there |
|---|---|
| Auth | Session-based auth (auth1), admin login, rate limiting on auth endpoints |
| Data | Postgres, `Tracking` base model (created/updated/deleted by + at, version, soft deletes, audit history on all models) |
| API | GraphQL (graphene-django), DRF, file upload |
| Permissions | django-role-permissions, per-model/per-field permission checks, GQL middleware |
| Async | Celery worker + beat, Redis broker, DatabaseScheduler |
| Search | OpenSearch, ProfileDocument, signals for incremental indexing, `make reindex` |
| Email | django-ses (prod), Mailpit (local) |
| Feature flags | django-constance, admin UI, fieldsets |
| Rate limiting | django-ratelimit on auth endpoints |
| Admin | Custom dark theme, BaseCoreAdmin (import/export, tracking fields), DJDT |
| Rule engine | Conditions + Actions + RuleProviderMixin, Celery-backed evaluation |
| State machine | DFA model, cron-scheduled transitions via Celery beat |
| Infra | Docker Compose: postgres, redis, opensearch, celery-worker, celery-beat, mailpit, ui |
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

### GraphQL

One schema file per app: `appname/schema/__init__.py`

**Object types:**
```python
from core.schema.utils import MetaNode, DjangoObjectTypeUtils
from graphene_django import DjangoObjectType

class ProductType(DjangoObjectType, DjangoObjectTypeUtils):
    class Meta(MetaNode):
        model = Product
        # MetaNode adds: interfaces = (Node,), connection_class = CustomConnection
```

**Queries — always return connections (never raw lists):**
```python
class Query(graphene.ObjectType):
    products = DjangoConnectionField(ProductType, search=graphene.String())

    @staticmethod
    def resolve_products(root, info, search='', **kwargs):
        if not info.context.user.is_authenticated:
            raise GraphQLError('Authentication required')
        qs = Product.objects.all()
        if search:
            qs = qs.filter(name__icontains=search)
        return qs
```

`CustomConnection` (from `core.schema.utils`) adds `total_count` automatically.

**Mutations — always return `ok: Boolean` + `errors: [ErrorType]`:**
```python
from graphene_django.rest_framework.mutation import SerializerMutation
from graphene_django.types import ErrorType

class CreateProductMutation(SerializerMutation):
    ok = graphene.Boolean()
    errors = graphene.List(ErrorType)

    class Meta:
        serializer_class = ProductSerializer

    @classmethod
    def mutate_and_get_payload(cls, root, info, **input):
        if not info.context.user.is_authenticated:
            raise GraphQLError('Authentication required')
        serializer = ProductSerializer(data=input)
        if serializer.is_valid():
            serializer.save(created_by=info.context.user)
            return cls(ok=True, errors=[])
        return cls(ok=False, errors=ErrorType.from_errors(serializer.errors))
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

All GraphQL tests extend `BaseTest`:
```python
from core.tests.utils.base_test import BaseTest

class ProductTest(BaseTest):

    def test_create_product(self):
        request = self.request()  # authenticated request as self.user
        mutation = '''
          mutation ($name: String!) {
            createProduct(input: {name: $name}) {
              ok
              errors { field messages }
            }
          }
        '''
        response = self.client.execute(mutation, variables={'name': 'Widget'}, context_value=request)
        self.assertEqual(0, len(response.get('errors', ())))
        self.assertTrue(response['data']['createProduct']['ok'])
```

`BaseTest` provides:
- `self.user` — superuser (username: `testuser`)
- `self.organization` — `Organization` (slug: `test-org`)
- `self.profile` — linked to user and org
- `self.request()` — authenticated request
- `self.assertQueryResult(query, vars, response)` — asserts no errors + snapshot
- `self.assertQueryError(query, vars, response, mutation_name)` — asserts errors present

For model-only tests use `django.test.TestCase` directly.

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
make shell        # Shell into Django container
make logs         # Tail Django logs
make perms        # Regenerate config/roles_gen.py
make reindex      # Rebuild OpenSearch indices
make superuser    # Create Django superuser
make ps           # Show container status
```
