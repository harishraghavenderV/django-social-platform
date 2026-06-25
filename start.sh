#!/bin/bash
set -e

echo "Running migrations..."
python manage.py migrate --noinput

echo "Starting Daphne ASGI server..."
daphne -b 0.0.0.0 -p ${PORT:-8000} social_platform.asgi:application
