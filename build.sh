#!/usr/bin/env bash
# Render runs this on every deploy (Build Command: bash build.sh).
# Migrations run here because Free instances have no shell for one-off commands.
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input

# Fingerprint of workouts, sets and plans before and after the database changes:
# the deploy fails if migrations or imports touched existing training data.
BEFORE=$(python manage.py data_fingerprint)
echo "Training data before: $BEFORE"

python manage.py migrate --no-input
python manage.py seed_exercises
python manage.py import_free_exercise_db

AFTER=$(python manage.py data_fingerprint)
echo "Training data after:  $AFTER"
if [ "$BEFORE" != "empty" ] && [ "$BEFORE" != "$AFTER" ]; then
  echo "ERROR: existing workouts, sets or plans changed during the deploy." >&2
  exit 1
fi
