#!/usr/bin/env bash
# Render runs this on every deploy (Build Command: bash build.sh).
# Migrations run here because Free instances have no shell for one-off commands.
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input

# Fingerprint of accounts, workouts, sets and plans before and after the database changes.
# --compare lists every changed row and fails the deploy unless it is an expected change
# (old "0 × 60" plank sets becoming "60 s", migration workouts/0004; sets moved by
# merge_exercises from a user's own exercise to the built-in one).
SNAPSHOT=$(mktemp)
trap 'rm -f "$SNAPSHOT"' EXIT
BEFORE=$(python manage.py data_fingerprint --save "$SNAPSHOT")
echo "Training data before: $BEFORE"

python manage.py migrate --no-input
# Shared cache table for allauth's rate limits (does nothing if it already exists).
python manage.py createcachetable
python manage.py seed_exercises
python manage.py import_free_exercise_db
# Built-in Smith machine variants; their base exercises come from the import above.
python manage.py seed_smith_variants
# Families of variants (same movement, other equipment); doubtful ones wait for approval.
python manage.py group_movements
# Users' own copies of built-in exercises -> the built-in (exercises/merges.py).
python manage.py merge_exercises

echo "Training data after:"
python manage.py data_fingerprint --compare "$SNAPSHOT"

# Admin access for the owner's account (ADMIN_EMAILS on Render). After the data check
# on purpose: it is an intended change to a user row.
python manage.py grant_admin
