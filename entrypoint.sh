#!/bin/bash
set -e

echo "Waiting for database to be ready..."
while ! nc -z db 3306; do
  sleep 1
done
echo "Database is ready!"

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Apply database migrations
echo "Running database migrations..."
python manage.py migrate

# Start Gunicorn server
echo "Starting Gunicorn..."
exec gunicorn --bind 0.0.0.0:8000 Podcraze.wsgi:application