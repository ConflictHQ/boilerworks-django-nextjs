#!/usr/bin/env python3
"""Emit this template's brain-node envelope at app/brain.json.

This repo is a federable brain node under the boilerworks metarepo: the
metarepo's `make aggregate-brain` (scripts/aggregate-brains.py) reads each
submodule's committed app/brain.json at the pinned SHA, namespaces ids as
`<repo>/<id>`, and anchors them to a synthetic repo node. This script emits
the minimal but real graph for THIS template: the template itself, its stack
pieces, and its feature engines, with edges template->pieces.

Contract (schemas/brain-envelope.schema.json + brain-node/brain-edge):
    { meta: {version, generator, counts}, nodes: [...], edges: [...] }

Determinism (mirrors the metarepo's gen-brain.py): meta is fixed and derived
(no timestamps), nodes sorted by id, edges deduped and sorted by
(source, target, rel), file written with indent=1.

Run from anywhere:  python3 scripts/gen_brain_node.py
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "app" / "brain.json"

BRAIN_VERSION = "1"
GENERATOR = "gen-brain-node"

TEMPLATE_ID = "template:django-nextjs"

STACK_PIECES = [
    ("django", "Django 6", "Backend web framework — ORM, admin, auth, migrations."),
    ("strawberry", "Strawberry GraphQL", "Code-first GraphQL layer (strawberry-graphql-django); schema assembled in config/schema.py, served at /gql/config/."),
    ("nextjs", "Next.js 16", "Frontend App Router + TypeScript + Apollo Client 4 + Tailwind/shadcn."),
    ("celery", "Celery", "Async task queue — worker + beat containers, Redis broker."),
    ("postgres", "PostgreSQL", "Primary relational database."),
    ("redis", "Redis", "Cache and Celery broker."),
    ("opensearch", "OpenSearch", "Full-text search indices rebuilt from the database (make reindex)."),
    ("minio", "MinIO", "S3-compatible object storage for uploads."),
]

FEATURE_ENGINES = [
    ("forms", "Form engine", "JSON-schema form definitions with visual builder (FormBuilder), dynamic renderer (DynamicForm), per-type config panels, conditional logic engine, and GraphQL submit pipeline."),
    ("workflows", "Workflow engine", "State-machine workflows with visual builder (xyflow), conditions/actions, and GraphQL API."),
    ("auth1", "Auth engine (auth1)", "Auth0 OIDC server-side flow -> backend-issued JWT in httpOnly cookie; session exchange at /app/auth1/session."),
    ("uploads", "Upload engine", "File uploads to MinIO/S3 with drag-and-drop frontend widget."),
]


def build() -> dict:
    nodes = [
        {
            "id": TEMPLATE_ID,
            "kind": "Artifact",
            "title": "boilerworks-django-nextjs",
            "text": "Full-stack template: Django 6 + Strawberry GraphQL backend, Next.js 16 frontend, Celery workers, Postgres/Redis/OpenSearch/MinIO services. A boilerworks metarepo submodule and federable brain node.",
            "source": "scripts/gen_brain_node.py",
            "durability": "durable-logic",
            "labels": ["template", "boilerworks"],
        }
    ]
    edges = []

    for slug, title, text in STACK_PIECES:
        node_id = f"stack:{slug}"
        nodes.append(
            {
                "id": node_id,
                "kind": "Dependency",
                "title": title,
                "text": text,
                "source": "scripts/gen_brain_node.py",
                "durability": "durable-logic",
                "labels": ["stack"],
            }
        )
        edges.append({"source": TEMPLATE_ID, "target": node_id, "rel": "uses", "class": "structural"})

    for slug, title, text in FEATURE_ENGINES:
        node_id = f"engine:{slug}"
        nodes.append(
            {
                "id": node_id,
                "kind": "Concept",
                "title": title,
                "text": text,
                "source": "scripts/gen_brain_node.py",
                "durability": "durable-logic",
                "labels": ["engine", "feature"],
            }
        )
        edges.append({"source": TEMPLATE_ID, "target": node_id, "rel": "provides", "class": "structural"})

    nodes.sort(key=lambda n: n["id"])
    seen = set()
    deduped = []
    for e in sorted(edges, key=lambda e: (e["source"], e["target"], e.get("rel", ""))):
        key = (e["source"], e["target"], e.get("rel", ""))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(e)

    return {
        "meta": {
            "version": BRAIN_VERSION,
            "generator": GENERATOR,
            "counts": {"nodes": len(nodes), "edges": len(deduped)},
        },
        "nodes": nodes,
        "edges": deduped,
    }


def main() -> None:
    graph = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        json.dump(graph, f, indent=1)
        f.write("\n")
    print(f"wrote {OUT.relative_to(ROOT)}: {graph['meta']['counts']['nodes']} nodes, {graph['meta']['counts']['edges']} edges")


if __name__ == "__main__":
    main()
