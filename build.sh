#!/usr/bin/env bash
# Render runs this on every deploy (Build Command: bash build.sh).
# Migrations run here because Free instances have no shell for one-off commands.
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input

# Fingerprint of accounts, workouts, sets and plans before and after the database changes.
# --compare lists every changed row and fails the deploy unless it is an expected change
# (so far only: old "0 × 60" plank sets becoming "60 s", migration workouts/0004).
SNAPSHOT=$(mktemp)
trap 'rm -f "$SNAPSHOT"' EXIT
BEFORE=$(python manage.py data_fingerprint --save "$SNAPSHOT")
echo "Training data before: $BEFORE"

python manage.py migrate --no-input
# Shared cache table for allauth's rate limits (does nothing if it already exists).
python manage.py createcachetable
python manage.py seed_exercises
python manage.py import_free_exercise_db

echo "Training data after:"
python manage.py data_fingerprint --compare "$SNAPSHOT"
