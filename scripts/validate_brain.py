#!/usr/bin/env python3
"""Validate app/brain.json against the brain schemas (schemas/brain-*.schema.json).

Also checks the file is fresh: regenerating with scripts/gen_brain_node.py
must produce byte-identical output (the brain is committed, deterministic).

Requires: pip install jsonschema
Run from anywhere:  python3 scripts/validate_brain.py
"""

import importlib.util
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parent.parent
BRAIN = ROOT / "app" / "brain.json"
SCHEMAS = ROOT / "schemas"


def main() -> int:
    envelope_schema = json.loads((SCHEMAS / "brain-envelope.schema.json").read_text())
    registry = Registry()
    for name in ("brain-node.schema.json", "brain-edge.schema.json", "brain-envelope.schema.json"):
        schema = json.loads((SCHEMAS / name).read_text())
        registry = registry.with_resource(name, Resource.from_contents(schema))

    brain = json.loads(BRAIN.read_text())
    validator = Draft202012Validator(envelope_schema, registry=registry)
    errors = sorted(validator.iter_errors(brain), key=lambda e: list(e.absolute_path))
    for err in errors:
        path = "/".join(str(p) for p in err.absolute_path) or "<root>"
        print(f"SCHEMA: {path}: {err.message}", file=sys.stderr)

    # Freshness: committed brain must match a regeneration exactly.
    spec = importlib.util.spec_from_file_location("gen_brain_node", ROOT / "scripts" / "gen_brain_node.py")
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    if gen.build() != brain:
        print("FRESHNESS: app/brain.json is stale — run `make brain` and commit", file=sys.stderr)
        return 1

    if errors:
        return 1
    print(f"app/brain.json OK: {len(brain['nodes'])} nodes, {len(brain['edges'])} edges, schema-valid and fresh")
    return 0


if __name__ == "__main__":
    sys.exit(main())
