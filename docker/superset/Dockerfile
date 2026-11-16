# Local-dev Superset: the official image plus the Postgres driver, so the
# sample dashboard can read the Boilerworks database. Production uses a
# hosted or separately deployed Superset; see README "Analytics (Superset)".
FROM apache/superset:6.1.0

USER root
RUN uv pip install --python /app/.venv/bin/python --no-cache psycopg2-binary==2.9.13
USER superset
