# LiftLog

A gym tracker built with Django, used mainly on a phone at the gym. It shows what you
lifted last time next to every exercise, suggests when to add weight, and keeps a rest
timer running. Portfolio project by Cezary Muszalski ([@Cezioor](https://github.com/Cezioor)).

## Run locally

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows; on macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
copy .env.example .env            # sets DEBUG=1 for local development
python manage.py migrate
python manage.py createcachetable   # rate limits of log-in and sign-up
python manage.py seed_exercises
python manage.py import_free_exercise_db
python manage.py seed_smith_variants
python manage.py group_movements
python manage.py merge_exercises
python manage.py runserver 0.0.0.0:8000
```

Run the same steps after pulling new migrations (they are the ones `build.sh` runs on Render).

Tests and linting: `pytest` and `ruff check .`

Languages: the UI is in English (default) and Polish. Texts are English in the code; Polish is in
`locale/pl/LC_MESSAGES/django.po`, compiled to `django.mo`, and both are committed. After changing texts run
`python manage.py makemessages -l pl --ignore=.venv --ignore=staticfiles`, translate, then
`python manage.py compilemessages --ignore=.venv` (both need GNU gettext installed).

## Deployment

Render (free web service, `render.yaml` + `build.sh`) with a Neon Postgres database.
Every deploy runs migrations, `seed_exercises` and `import_free_exercise_db`; both commands
can be run any number of times.

## Data and credits

Exercise data, instructions and photos come from
[free-exercise-db](https://github.com/yuhonas/free-exercise-db) by yuhonas, released into the
public domain under [The Unlicense](https://github.com/yuhonas/free-exercise-db/blob/main/LICENSE.md).
A snapshot of `dist/exercises.json` is kept in `exercises/data/` (pinned to commit
`f00c92c7`); photos are loaded from the jsDelivr CDN at the same commit and are not stored
in this repository. Polish exercise names and the muscle map drawing are LiftLog's own.
