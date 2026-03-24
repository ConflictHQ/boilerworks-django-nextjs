

import logging
import os
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


variables = [
    'DJANGO_SETTINGS_MODULE',
    'DJANGO_CONFIGURATION',
    'POSTGRES_ENGINE',
    'POSTGRES_DB',
    'POSTGRES_USER',
    'POSTGRES_HOST',
    'POSTGRES_PORT',
]

logger.warning('[STARTUP] Env Variables v1 ==================================')

for name in variables:
    value = os.getenv(name)
    if value:
        logging.warning(f'[STARTUP] Variables {name} value found {value}')
    else:
        logging.warning(f'[STARTUP] Missing value for {name}')

logger.warning('[STARTUP] Env Variables ==================================')


def execute_and_log(command):
    logger.warning(f'[STARTUP] Running command {command}')
    # Run the command and capture the output
    result = subprocess.run(command, shell=True, text=True, capture_output=True)

    # Log the standard output and standard error
    if result.stdout:
        logging.warning("Command output: %s", result.stdout)
    if result.stderr:
        logging.error("Command error: %s", result.stderr)

    return result.returncode


ON_STARTUP = [
    'showmigrations',
    'migrate'
]

logger.warning('[STARTUP] Running startup... ==================================')

os.system('service cron start')

BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR)
for command in ON_STARTUP:
    execute_and_log(f'python manage.py {command}')


os.system('python manage.py runserver 0.0.0.0:8000')

logger.warning('Setup complete')
