#!/bin/sh
# Initialise the local Superset, create the accounts, start the sample loader
# in the background and run the server. Safe to re-run: every step is
# idempotent against the persisted superset-home volume.
set -e

superset db upgrade
superset init

# The human admin for building dashboards at http://localhost:8088 (local only).
superset fab create-admin --username admin --firstname Local --lastname Admin \
    --email admin@example.com --password admin || true

# The service account the backend uses for guest tokens (SUPERSET_USERNAME /
# SUPERSET_PASSWORD in backend/config/local.env). Admin here for simplicity;
# give a deployed one a role with only "can grant guest token" and embedding.
superset fab create-user --role Admin --username "$SUPERSET_USERNAME" \
    --firstname Embed --lastname Service --email "$SUPERSET_USERNAME@example.com" \
    --password "$SUPERSET_PASSWORD" || true

python /app/docker/boilerworks/sample_dashboard.py &

exec /usr/bin/run-server.sh
