#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install production dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Run database migrations
python manage.py migrate

# Populate sample seed data if empty
python manage.py seed_data

# Collect static assets into staticfiles/
python manage.py collectstatic --noinput
