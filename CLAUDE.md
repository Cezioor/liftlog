# LiftLog – gym tracker with AI-built training plans

Portfolio project of Cezary Muszalski (github.com/Cezioor). A Django web app used mainly on a phone at the gym.
It replaces "what did I lift last time?" guesswork with a log that shows the previous session next to every exercise,
and it can build a personalised plan from a short interview (goals, equipment, injuries, preferences).

The owner is learning: explain decisions briefly, prefer clear, conventional Django over clever code,
and keep each change small enough to review.

## Product, in priority order

### Stage 1 – Tracker (MVP)
1. **Accounts**: sign-up, login, logout, password reset (Django auth). Every object belongs to a user; a user never sees another user's data.
2. **Exercise library**: seeded with ~60 common exercises (name, primary muscle group, equipment, `is_bodyweight`). Users can add their own.
3. **Plans**: a plan has days (e.g. Push / Pull / Legs); each day has ordered exercises with target sets, a rep range (e.g. 8–12) and rest time.
4. **Logging a workout** (the core screen, must be fast one-handed on a phone):
   - start a workout from a plan day or empty;
   - for each exercise show **last time's sets (weight × reps) for that exercise** right next to the inputs;
   - add a set in one tap, pre-filled with last time's weight; edit or delete sets;
   - a simple rest timer after logging a set;
   - finish the workout with an optional note.
5. **Progression hint**: if the user hit the top of the rep range on all sets last time, suggest +2.5 kg (upper body) / +5 kg (lower body); otherwise suggest the same weight. Show it as a hint, never force it.
6. **History and progress**: list of past workouts; per-exercise page with a chart of best estimated 1RM per session (Epley: `w × (1 + reps/30)`) and of total volume.
7. **PWA**: manifest + service worker so it can be installed on the home screen; mobile-first layout.

### Stage 2 – AI plan builder
- A guided interview (form steps, then a short chat for follow-up questions) collecting: goal, experience, days per week, session length, equipment available, injuries/pain points, exercises liked and disliked.
- The Claude API returns a plan as **structured JSON validated against a schema** before it is saved as a normal Plan the user can edit. Exercises are mapped to the library; unknown ones are created as user exercises.
- **Safety rules in the system prompt**: no medical diagnosis; avoid loading reported painful areas; for acute pain, recent injury or post-surgery, recommend consulting a physiotherapist or doctor; prefer conservative volume for beginners. Show a short disclaimer on the page.
- Cost control: API key only in an environment variable; per-user limit (e.g. 3 generated plans per day); log token usage.

### Stage 3 – Schedule (later)
Tasks and recurring reminders (e.g. "gym Mon/Wed/Fri", deadlines), with the planned workouts shown on the same calendar.

## Technical decisions

- **Django 5.2+**, Python 3.12+, PostgreSQL in production, SQLite locally.
- **Server-rendered templates + HTMX** for interactivity (adding sets without page reloads). No SPA framework.
- Styling: one small hand-written CSS file with CSS variables, dark mode, large tap targets. No CSS framework.
- Charts: Chart.js from a CDN with a pinned version.
- Settings from environment variables (`DJANGO_SECRET_KEY`, `DATABASE_URL`, `ANTHROPIC_API_KEY`, `DEBUG`).
- Tests with **pytest + pytest-django**; GitHub Actions runs tests and `ruff` on every push.
- Deploy target: decided at the end of Stage 1 (a free/low-cost host with Postgres).

## Data model (Stage 1)

```
Exercise(name, muscle_group, equipment, is_bodyweight, owner: User | null)   # null = built-in
Plan(owner, name, is_active, created_at)
PlanDay(plan, name, order)
PlanExercise(day, exercise, order, target_sets, rep_min, rep_max, rest_seconds)
Workout(owner, plan_day | null, started_at, finished_at | null, note)
WorkoutSet(workout, exercise, order, weight_kg, reps, is_warmup)
```
"Last time" for an exercise = the sets of that exercise from the user's most recent finished workout that contains it.

## Conventions

- Apps: `accounts`, `exercises`, `plans`, `workouts` (Stage 2 adds `planner`).
- Every view that touches user data filters by `request.user`; write a test for this for each model.
- Business logic (progression hint, 1RM, "last time" query) lives in plain functions in `services.py`, tested without views.
- Times stored in UTC, shown in Europe/Warsaw.
- Commit messages in English, imperative mood.
