"""Create the local sample dashboard through Superset's REST API.

Runs in the background from start.sh. Idempotent: it looks every object up by
name before creating it. The result is a dashboard with the slug
`boilerworks-sample` over the Boilerworks `auth_user` table; embed it from the
backend with:

    make superset-embed dashboard=boilerworks-sample
"""
import json
import os
import sys
import time

import requests

BASE = 'http://localhost:8088'
DB_NAME = 'Boilerworks (local)'
DB_URI = os.environ.get('BOILERWORKS_DB_URI', '')
TABLE = 'auth_user'
SLUG = 'boilerworks-sample'


def log(message):
    print(f'[sample-dashboard] {message}', flush=True)


def wait_for(check, what, attempts=90, delay=10):
    for _ in range(attempts):
        try:
            if check():
                return
        except requests.RequestException:
            pass
        time.sleep(delay)
    log(f'gave up waiting for {what}')
    sys.exit(1)


def session():
    s = requests.Session()
    token = s.post(f'{BASE}/api/v1/security/login', json={
        'username': 'admin', 'password': 'admin', 'provider': 'db', 'refresh': False,
    }, timeout=30).json()['access_token']
    s.headers['Authorization'] = f'Bearer {token}'
    s.headers['X-CSRFToken'] = s.get(f'{BASE}/api/v1/security/csrf_token/', timeout=30).json()['result']
    s.headers['Referer'] = BASE
    return s


def find(s, resource, column, value):
    q = json.dumps({'filters': [{'col': column, 'opr': 'eq', 'value': value}]})
    rows = s.get(f'{BASE}/api/v1/{resource}/', params={'q': q}, timeout=30).json().get('result', [])
    return rows[0]['id'] if rows else None


def create(s, resource, payload):
    response = s.post(f'{BASE}/api/v1/{resource}/', json=payload, timeout=60)
    if response.status_code >= 400:
        raise RuntimeError(f'{resource}: {response.status_code} {response.text[:300]}')
    return response.json()['id']


def main():
    if not DB_URI:
        log('BOILERWORKS_DB_URI is not set; skipping the sample dashboard')
        return

    wait_for(lambda: requests.get(f'{BASE}/health', timeout=5).ok, 'Superset')
    s = session()

    db_id = find(s, 'database', 'database_name', DB_NAME) or create(s, 'database', {
        'database_name': DB_NAME, 'sqlalchemy_uri': DB_URI, 'expose_in_sqllab': True,
    })

    # The backend creates auth_user on its first migrate, which can finish
    # after Superset is up, so retry the dataset until the table exists.
    dataset = {}

    def dataset_ready():
        dataset['id'] = find(s, 'dataset', 'table_name', TABLE) or create(s, 'dataset', {
            'database': db_id, 'schema': 'public', 'table_name': TABLE,
        })
        return True

    for _ in range(60):
        try:
            dataset_ready()
            break
        except RuntimeError as error:
            log(f'waiting for {TABLE}: {error}')
            time.sleep(10)
    else:
        sys.exit(1)

    dashboard_id = find(s, 'dashboard', 'slug', SLUG) or create(s, 'dashboard', {
        'dashboard_title': 'Boilerworks sample', 'slug': SLUG, 'published': True,
    })

    datasource = f"{dataset['id']}__table"
    charts = [
        ('Users', {'viz_type': 'big_number_total', 'metric': 'count', 'subheader': 'accounts'}),
        ('Users by status', {
            'viz_type': 'table', 'query_mode': 'aggregate', 'groupby': ['is_active'],
            'metrics': ['count'], 'row_limit': 100,
        }),
    ]
    for name, params in charts:
        if find(s, 'chart', 'slice_name', name):
            continue
        create(s, 'chart', {
            'slice_name': name,
            'viz_type': params['viz_type'],
            'datasource_id': dataset['id'],
            'datasource_type': 'table',
            'params': json.dumps({**params, 'datasource': datasource}),
            'dashboards': [dashboard_id],
        })

    log(f'ready: dashboard "{SLUG}" (id {dashboard_id})')


if __name__ == '__main__':
    main()
