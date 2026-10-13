#!/bin/sh
set -e

python manage.py wait_for_db
python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py seed_demo

exec gunicorn backend.config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers "${GUNICORN_WORKERS:-2}" \
    --access-logfile - \
    --error-logfile -
