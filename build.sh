#!/usr/bin/env bash
# Render runs this on every deploy (Build Command: bash build.sh).
# Migrations run here because Free instances have no shell for one-off commands.
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate --no-input
python manage.py seed_exercises
python manage.py import_free_exercise_db
