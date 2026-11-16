"""Superset config for the local `analytics` compose profile only.

Production Superset needs its own config: a Postgres metadata database, a
real cache, Talisman on with `frame-ancestors` set to the app's domains, and a
service account whose role only grants guest tokens and embedding.
"""
import os

SECRET_KEY = os.environ['SUPERSET_SECRET_KEY']

FEATURE_FLAGS = {
    # Embedded dashboards and guest tokens (POST /api/v1/security/guest_token/).
    'EMBEDDED_SUPERSET': True,
}

# Guest-token users get this role's permissions. Dashboard and dataset access
# comes from the guest token's resources, so the built-in Gamma role is enough.
GUEST_ROLE_NAME = 'Gamma'
GUEST_TOKEN_JWT_EXP_SECONDS = 300

# Let http://localhost:3000 frame Superset. Talisman sets X-Frame-Options and
# a CSP without frame-ancestors, which blocks the embed; turn it back on with
# frame-ancestors in any deployed Superset.
TALISMAN_ENABLED = False
