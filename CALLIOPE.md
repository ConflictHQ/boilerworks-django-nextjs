# Calliope — Boilerworks Django + Next.js
<!-- Agent shim for https://github.com/calliopeai/calliope-cli -->

Primary conventions doc: [`bootstrap.md`](bootstrap.md)
Context seed: [`memory.md`](memory.md)

Read both before writing any code.

---

## Project-specific notes

- Django backend with a Strawberry GraphQL API (`strawberry-graphql` + `strawberry-graphql-django`); `config/schema.py` assembles Query/Mutation from all apps. Endpoints: `/gql/config/` (main), `/gql/config/auth/` (login only).
- Types in `<app>/schema/types.py`; mutations in `<app>/schema/mutations.py`; context (`StrawberryContext`) in `core/schema/context.py`; async batch dataloaders in `core/schema/dataloaders.py`.
- Auth check is required at the top of **every** GraphQL resolver and mutation.
- `config/roles_gen.py` is generated — don't edit it; run `make perms`.
- Never expose integer PKs — use `guid` or the relay global ID.
- Soft-delete only: set `deleted_at`/`deleted_by`, never `.delete()`. Run `make lint` (flake8 + isort) before committing; max line length 140.
