#!/usr/bin/env bash
# Render build step: runs on every deploy (Render > your service > Events shows its output).
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate --no-input        # also loads the seed data (institutions, programs)
python manage.py ensure_superuser          # creates the admin account once, from DJANGO_SUPERUSER_* variables
