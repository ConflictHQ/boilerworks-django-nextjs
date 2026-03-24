#!/usr/bin/env bash
# Use the root-level run.sh instead:
exec "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/run.sh" "$@"
