#!/bin/bash
# Migration check hook.
# Runs inside the Docker container if it's up; skips otherwise (CI handles it).
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd "$SCRIPT_DIR/.." || exit 1

CONTAINER="boilerworks-local"

if docker inspect "$CONTAINER" --format '{{.State.Running}}' 2>/dev/null | grep -q true; then
    echo "Checking Django migrations in container..."
    docker exec "$CONTAINER" python manage.py makemigrations --check
    exit $?
fi

# Container not running — skip rather than block the commit.
# Start the stack with ./run.sh to enable the full migration check.
echo "⚠ Skipping migration check: $CONTAINER is not running."
echo "  Start the stack with ./run.sh and retry if you added migrations."
exit 0
