# LiftLog – gym tracker with AI-built training plans

Portfolio project of Cezary Muszalski (github.com/Cezioor). A Django web app used mainly on a phone at the gym.
It replaces "what did I lift last time?" guesswork with a log that shows the previous session next to every exercise,
and it can build a personalised plan from a short interview (goals, equipment, injuries, preferences).

The owner is learning: explain decisions briefly, prefer clear, conventional Django over clever code,
and keep each change small enough to review.

## Status (checked in the code on 2026-11-07)

| Stage | Status |
|---|---|
| **1 – Tracker (MVP)** | in progress (items 6–7 left) |
| 1.1 Accounts (allauth, email verification, rate limits) | done |
| 1.2 Exercise library | done |
| 1.3 Plans (incl. "⇄ Change variant") | done |
| 1.4 Logging a workout (rest/hold timers, sides, set rating, first-time calibration) | done |
| 1.5 Progression hint (`progression_step_kg`, RIR) | done |
| 1.6 History and progress | in progress: last 5 workouts on the home screen, workout summary page, exercise page with last sets and records (best e1RM, heaviest set, most reps, longest hold). Missing: a full workout history list and the Chart.js charts (best e1RM and volume per session) – no chart code exists yet |
| 1.7 PWA | to do: no manifest, no service worker |
| **1.5 – Bigger exercise library** (free-exercise-db, detail page, muscle map, Smith machine, search, movement families and variants) | done |
| **1.6 – Exercise types** (+ set rating RIR, calibration, old plank sets converted) | done |
| Feedback ("Zgłoś", admin, `feedback_report`) | done (commit 1f73565); `FEEDBACK_EMAIL` and `ADMIN_EMAILS` still to be set on Render |
| PL/EN language switcher (whole UI, footer switch, Settings, language on the account; English by default) | done (2026-11-07) |
| **1.7 – Activities and body weight** | to do |
| **1.8 – Consistency and rewards** | to do |
| **1.9 – Training insights** | to do |
| **2 – AI plan builder and coach** | to do |
| **3 – Schedule** | to do |
| Before opening to other people (GDPR, own domain, keep-alive) | to do |

## Next up (in this order)

1. **Feedback system** ("Zgłoś": bug / suggestion / opinion, email to `FEEDBACK_EMAIL`, admin panel, `feedback_report`):
   built and deployed; left: set `FEEDBACK_EMAIL` and `ADMIN_EMAILS` on Render and test it on the phone.
2. ~~**PL/EN language switcher**~~: done (see "Languages (PL/EN)" below).
3. **Polish names for more exercises**: on 2026-11-07, 291 of 913 built-ins had Polish names (aliases, for Polish
   search; names stay English). Missing: 367 of 532 beginner exercises, 211 intermediate, 44 expert. Beginners
   first, in `exercises/free_db_polish.py`; the owner reviews the proposed names before they are saved.
4. **Finding exercises by type (A, no data model change)**: "Type" (category) filter chips in the picker; goal
   tiles on the library (Strength, Warm-up, Stretching, Balance & stability, Cardio); rename "Motor control /
   balance" to "Balance & stability"; "Stretches for these muscles" on the exercise page; in "⇄ Change variant"
   show only equipment that fits (used by ≥ 2 built-ins with the same muscle group and mechanic, e.g. no
   bodyweight hammer curl), the rest behind "Show all equipment", "Other…" stays.
5. **Plan sections and missing exercises (B + C)**, before Stage 1.7: `PlanExercise.section` with three fixed
   sections (warm-up / main / cool-down); warm-up and cool-down suggestions from the muscles of the day's main
   part; on the workout screen warm-up and cool-down are a tick-off list with an optional timer (no weights, hints
   or records; defaults 1–2 × 30 s, no rest). About 15–20 built-in dynamic warm-up drills (all 123 current
   stretches are static), exercises marked "before" / "after" training, about 10–15 balance exercises (the
   category had 1). Lists wait for the owner's approval. Warm-up and stretching never count as hard sets (1.9).
6. **Stage 1.7** – activities and body weight.
7. **Checkpoint A**: a test at the gym and by a second (female) user; then `feedback_report`.
8. **Stages 1.8, 1.9 and 2.**
9. **Checkpoint B**: a week of training on a plan built by the AI.

Stage 1 items 6 (history list, charts) and 7 (PWA) are not scheduled yet: ask the owner where they fit.

## How we work

- We work in stages; tests at the gym happen only at checkpoints. After every checkpoint we read the reports with
  `python manage.py feedback_report` and group them into bugs, convenience and ideas.
- While working, run only the tests of the app being changed (`pytest <app>/ -q`); run everything once at the end
  of the task (`pytest -q --tb=short`), plus `ruff check .` and `ruff format --check .`.
- The summary at the end of a task: at most 10 points, in Polish.
- Every change to users' data goes through `data_fingerprint` (`build.sh` fails the deploy on unexpected changes;
  expected ones are listed explicitly in `--compare`). Uncertain data decisions (matches, groups, merges) wait for
  the owner's approval before they are applied.
- Commit and push only when asked; commit messages in English, imperative mood. After pushing, check GitHub Actions
  and the Render deployment status (Render reports deployments to the GitHub API: `/repos/Cezioor/liftlog/deployments`).

## Local environment (owner's Windows PC)

- Python 3.12 in `.venv`, created with uv (the system Python is 3.11). Always use `.venv\Scripts\python`
  (`.venv/Scripts/python.exe` in Git Bash).
- Avast Web Shield intercepts HTTPS, so certificate checks fail. Never turn SSL verification off; point the tools at
  Avast's certificate instead:
  - pip: `python -m pip install --cert "C:/ProgramData/Avast Software/Avast/wscert.pem" …`
  - uv: `uv … --native-tls` (uses the Windows certificate store, which trusts Avast)
  - requests / other Python HTTP clients: `REQUESTS_CA_BUNDLE` (or `SSL_CERT_FILE`) pointing at a bundle made of
    certifi's `cacert.pem` plus `wscert.pem`
  - git: this repo has `http.sslBackend=schannel` (Windows certificate store).
- No `gh` CLI; use the GitHub REST API with curl for read-only checks.
- Run the app: `.venv/Scripts/python.exe manage.py runserver 0.0.0.0:8000` with `DEBUG=1` in `.env` (DEBUG accepts any
  host). On the phone, on the same Wi-Fi (or the phone's hotspot), open `http://<the PC's LAN IP>:8000`
  (`ipconfig` → IPv4 address); allow Python through the Windows firewall if asked. Wake lock and some browser
  features need HTTPS, so test those on Render.
- Emails locally: without `BREVO_API_KEY` they are printed in the runserver console (sign-up links, password reset,
  "Zgłoś" reports).
- Local database: SQLite `db.sqlite3`; rehearse risky migrations on a copy (e.g. in the scratchpad) with
  `DATABASE_URL=sqlite:///<copy>` and run the `build.sh` steps with `data_fingerprint --save/--compare`.
- After pulling new migrations the local database needs more than `migrate`: also the other `build.sh` steps
  (`createcachetable`, `seed_exercises`, `import_free_exercise_db`, `seed_smith_variants`, `group_movements`,
  `merge_exercises`). Without `createcachetable` logging in fails with "no such table: django_cache".
- In the local `.env` set `ACCOUNT_EMAIL_VERIFICATION=optional`: otherwise `mandatory` applies, and local emails
  only go to the runserver console. (Tests ignore it: conftest forces `mandatory`.)
- gettext (for `makemessages` / `compilemessages`) is in `C:\Users\LT\AppData\Local\Programs\gettext-iconv\bin`;
  VS Code may not see it on PATH, so prepend it in Git Bash:
  `export PATH="/c/Users/LT/AppData/Local/Programs/gettext-iconv/bin:$PATH"`. Installed with
  `winget install -e --id mlocati.GetText --source winget` (the `msstore` source rejects Avast's certificate).

## Product, in priority order

### Stage 1 – Tracker (MVP)
1. **Accounts** (django-allauth): sign-up with email + password, log-in by email, **email verification** (link by email; `ACCOUNT_EMAIL_VERIFICATION` env: `mandatory` by default, `optional` lets people
   in right away with "Konto założone. Wysłaliśmy też link do potwierdzenia adresu e-mail" and a resend button in Settings;
   "Account created! We sent a link to …" page with "send it again"), password reset, rate-limited attempts. Field errors sit next to
   their fields; an already registered email says so with links to log in / reset the password. Account emails are Polish,
   HTML + plain text, written to pass spam filters (no images, scripts or tracking, links only to the app, link also as text;
   checked with SpamAssassin: score 0). A failing mail service never breaks sign-up: it is logged (without the address)
   and the user is told. Auth forms disable their button
   after the first tap (a double submit on the slow free server used to fail with "user already exists").
   Every object belongs to a user; a user never sees another user's data.
2. **Exercise library**: seeded with ~60 common exercises (name, primary muscle group, equipment, `is_bodyweight`). Users can add their own.
3. **Plans**: a plan has days (e.g. Push / Pull / Legs); each day has ordered exercises with target sets, a rep range (e.g. 8–12) and rest time.
4. **Logging a workout** (the core screen, must be fast one-handed on a phone):
   - start a workout from a plan day or empty;
   - for each exercise show **last time's sets (weight × reps) for that exercise** right next to the inputs;
   - add a set in one tap, pre-filled with last time's weight; edit or delete sets;
   - a simple rest timer after logging a set;
   - finish the workout with an optional note.
5. **Progression hint**: if the user hit the top of the rep range on all sets last time, suggest the exercise's
   `progression_step_kg` more (default: dumbbells 2 kg, lower body 5 kg, upper body 2.5 kg; editable per exercise);
   otherwise suggest the same weight. Set ratings sharpen it: a set at the top of the range with RIR ≥ 3 means add
   weight, RIR 0 at the bottom of the range means stay. Show it as a hint, never force it.
6. **History and progress**: list of past workouts; per-exercise page with a chart of best estimated 1RM per session (Epley: `w × (1 + reps/30)`) and of total volume.
7. **PWA**: manifest + service worker so it can be installed on the home screen; mobile-first layout.

### Stage 1.5 – Bigger exercise library
1. **Import free-exercise-db** (github.com/yuhonas/free-exercise-db, The Unlicense, 876 exercises) with an idempotent
   `import_free_exercise_db` command keyed on a stable `source_id`. Exercise gains primary/secondary muscles, level,
   category, mechanic, instructions and image paths; database muscle names map onto our muscle groups.
   The 65 original exercises are never deleted or duplicated (plans and workouts point at them): each is matched to its
   free-exercise-db counterpart by a reviewed mapping and enriched, keeping its ID, Polish names and progression step.
   Ambiguous matches wait for the owner's confirmation; their candidates are not imported until then.
   ~150 popular imported exercises get Polish names and synonyms.
   Images are not stored in the repo: they come from jsDelivr pinned to one free-exercise-db commit, `loading="lazy"`.
2. **Exercise detail page**: start/end photos (tap to switch, or auto-alternate), front/back muscle map in SVG (primary
   strong, secondary lighter; works for user exercises too), step-by-step instructions, equipment, level, the user's
   last sets, "Add to plan".
3. **Thumbnails** in the exercise picker and library, and a difficulty filter.
4. Tests for the import (re-runs, legacy matching, no duplicates) and the detail view; data source credited in the README
   and the page footer.
5. **Search and variants.** Search ignores case, Polish diacritics, hyphens, spaces and English plurals
   ("step up" = "step-up" = "stepup" = "step ups"). Equipment words in the query, Polish or English (smith, suwnica,
   hantle, sztanga, kettlebell, wyciąg, linka, gumy, maszyna…), filter by equipment (or match that word in a name).
   Equipment includes **Smith machine**: the 20 free-exercise-db Smith exercises use it, plus 30 built-in Smith variants
   (`exercises/smith_variants.py`, command `seed_smith_variants`) linked to their free-weight base.
   When the movement exists but not with the typed equipment, the picker shows "+ Add variant: «Step Ups» — Kettlebell"
   on top: one tap creates the user's own exercise in the base's family, copying muscles, measurement, category,
   instructions and photos, with the new equipment. A variant has its own history and records; an exercise's page lists
   the other variants. "+ Add my own exercise" is shown first and prominently when nothing matched.
6. **Movement families.** `Movement` groups the variants of one movement (replaced `variant_of`, migration
   exercises/0009). `group_movements` (run by `build.sh`) joins built-ins whose names differ only by equipment words
   ("Barbell Step Ups" + "Dumbbell Step Ups") plus the hand-made Smith links; doubtful groups (same equipment twice,
   different muscle group or category, one side vs both) wait in `exercises/movement_groups.py` for the owner's
   CONFIRMED/REJECTED decision (`group_movements --pending` lists them); MANUAL_GROUPS joins differently named exercises
   (e.g. two-arm bent-over rows, parallel-bar dips, deadlift with other bars). Merging families keeps users' own
   variants. `merge_exercises` (`exercises/merges.py`) folds a user's own copy into the matching built-in: sets, plan
   entries and swaps move to the built-in, the copy is deleted.
   **"⇄ Change variant"** on the plan editor, the workout card and the exercise page: the family's variants first, then
   equipment without a variant (Smith, dumbbell, barbell, kettlebell, weight plate, pull-up bar, cable, machine, band,
   landmine, TRX, bodyweight, "Other…" with a typed name), which creates the user's variant in one tap. During a
   workout a plan exercise asks **"Only today"** (`WorkoutSwap`, the plan stays) or **"Change in the plan too"**
   (PlanExercise.exercise changes, targets kept). Sets already logged always stay with the variant they were done with.

### Feedback from users (done)

- **"Zgłoś"** link in the top bar of every screen for logged-in users opens a dialog: kind ("Błąd", "Sugestia zmiany",
  "Opinia"), "Opisz, co się wydarzyło albo co proponujesz" (required, max 2000 characters), "Wyślij". Sent with HTMX,
  so a workout in progress is never reloaded; "Dzięki! Zgłoszenie dotarło." and the dialog closes. Without JavaScript
  it is the page /feedback/ that returns to where you were.
- Saved automatically: the page it was sent from, the user, the time and the device type (from User-Agent).
  At most 5 reports per user per hour.
- Each report is emailed to `FEEDBACK_EMAIL` (Brevo, like account emails); if the email fails the report is still saved
  and the error is logged (report id only).
- Admin (`/admin/`, login through the app's own email login): list with filters by kind, status (Nowe / W trakcie /
  Załatwione) and device, status editable from the list. Admin access: `grant_admin` (emails from `ADMIN_EMAILS`, only
  confirmed addresses; run by `build.sh` after the data check).
- **Working rule:** at every checkpoint (before planning the next piece of work) run
  `python manage.py feedback_report` against production data, read the open reports grouped by kind and propose fixes;
  mark handled ones in the admin.

### Languages (PL/EN) (done)

- The whole UI, logged in or not, in English (the default) and Polish. Choosing: the language saved on the account
  → the cookie → the browser's Accept-Language → English (`config.middleware.UserLanguageMiddleware`); a browser
  in a language we don't have gets English (decided 2026-11-07). More languages may come later: add them to
  `LANGUAGES` and create `locale/<code>/` with `makemessages -l <code>`.
- "PL · EN" in the footer of every page (also log-in and sign-up), hidden on an open workout (the reload would lose
  inputs not logged yet), and "Language" in Settings (only Polish and English). The choice is saved on the
  account (switcher, Settings, and the language someone signs up in); after logging in on a new device the app
  is in the account's language at once, and after logging out it stays in it (the cookie lasts a year).
- Not translated on purpose: account emails (Polish, passed SpamAssassin), the admin's own texts, the feedback
  email to the owner and `feedback_report` (always Polish), exercise names and free-exercise-db instructions
  (English; Polish names are aliases for search). Saved variant names always use the English equipment label.

### Stage 1.6 – Exercise types (do this first: it changes the core data model)

Not every exercise is weight × reps. Each exercise gets a `measurement` type that decides which inputs the logging screen shows:

| measurement | logged as | examples |
|---|---|---|
| `weight_reps` | kg × reps | bench press, squat |
| `reps` | reps (optional added kg) | pull-ups, push-ups, box jumps |
| `time` | seconds (optional added kg) | plank, wall sit, isometric holds, dead hang |
| `distance_time` | metres + seconds | farmer's walk, sled push, rowing sprint |

Plus `is_unilateral` (log left/right separately, e.g. single-leg RDL, stretches per side) and a `category`:
strength, isometric, stretching / mobility, plyometric, motor / coordination / balance, cardio, rehab.
Map free-exercise-db categories (strength, stretching, plyometrics, powerlifting, olympic weightlifting, strongman, cardio) onto these;
add a small set of built-in isometric, mobility and balance exercises the database lacks (e.g. Spanish squat hold, Copenhagen plank, single-leg balance).

`WorkoutSet` gets nullable `duration_seconds`, `distance_m` and `side` (left/right/null); existing sets stay `weight_reps`.
Plans store targets per type (e.g. 3 × 30–45 s). Progression hints per type: more time for holds (+5 s), more reps for `reps`, as now for weights.
For `time` exercises the logging screen shows a hold timer that counts up and saves the duration in one tap.
"Last time", records and charts work for every type (longest hold, most reps, best e1RM).
Old time-exercise sets logged as "0 × N" were converted to N seconds (migration workouts/0004; the deploy's
`data_fingerprint --compare` allows only that change).

**Set rating (RIR).** Optional on every weight × reps and reps set, always stored as RIR (reps in reserve, 0–4, halves allowed;
4 = "4+"). Settings choose how it is entered and shown: **simple** (default: Easy = 4+, Medium = 3, Hard = 1–2 stored as 1.5,
Max effort = 0), **RIR** (buttons 0, 1, 2, 3, 4+) or **RPE** (6–10 in 0.5 steps; RPE = 10 − RIR). Switching never changes stored data.
History and "Last time" show it in the chosen scale ("60 × 8 @RIR 2", "60 × 8 · Hard").
In the progression hint, a set at the top of the rep range with RIR ≥ 3 is a clear signal to add weight;
RIR 0 at the bottom of the range means stay at that weight.

**Calibration (first time with an exercise, i.e. no history for this user):**
- `time`: "hold as long as your form stays good" (test hold), then working holds of ~75% of it, within the plan's range;
- `reps`: one set to the technical max (stop when form slips), then working sets of ~70% of it;
- `weight_reps`: no test to failure. Light test sets (barbell: the empty 20 kg bar), each rated; after the first set with RIR ≤ 2,
  estimate 1RM with Epley counting the reserve (`w × (1 + (reps + RIR)/30)`) and suggest a working weight for the plan's rep range
  (top of the range with ~2 reps to spare), rounded down to `progression_step_kg`. Test sets are marked as warm-ups so they never
  count as records. A short note explains why weights are not tested to failure (technique and safety).

### Stage 1.7 – Activities and body weight

- **Activities** outside the gym plan: sauna, running, cycling, swimming, walking, stretching session, team sport, custom.
  Fields: type, start, duration, intensity (light / moderate / vigorous), optional distance, note.
- **Estimated kcal** = MET × body weight (kg) × hours, using MET values from the Compendium of Physical Activities
  (store the source per activity type). Always labelled "estimated". Sauna gets a low MET; the app explains that weight lost in a sauna is mostly water.
- **Body weight and measurements** (waist, chest, arm, thigh…) with a chart. The latest weight feeds the kcal estimate.
- Home screen timeline shows workouts and activities together.

### Stage 1.8 – Consistency and rewards

- **Weekly goal** (e.g. 3 sessions per week; the user chooses what counts: workouts, cardio, mobility, sauna).
  Streak = consecutive weeks meeting the goal. No daily streaks: rest days are part of training.
- **Calendar heatmap** of activity (GitHub-style) and a weekly summary.
- **Badges/milestones**: first workout, 10/50/100 workouts, new personal records, 4/12/26-week streaks, first full mobility week.
- **Points ledger**: every reward is a row (`user, event_type, points, created_at, source_object`), never just a counter,
  so partner rewards, redemptions or rankings can be added later without migrations of history.
- **Live PR detection**: "New record!" on the logging screen the moment a set beats a previous best.
- Never reward eating less or a calorie deficit; reward showing up and logging.

### Stage 1.9 – Training insights (data analysis)

- **Weekly sets per muscle** from primary/secondary muscles (secondary counts as half a set), shown on the body map
  against a typical 10–20 hard sets per muscle per week, with a note that needs vary per person.
- **Plateau detection**: if best e1RM (or longest hold / most reps) for an exercise has not improved over ~3 weeks of regular training,
  suggest a deload week or an exercise variation. Explain the rule in the UI.

### Stage 2 – AI plan builder and coach

Guided interview (form steps + short chat): goal, experience, days per week, session length, equipment, exercises liked/disliked,
**injuries, pain and surgeries**. The Claude API returns a plan as JSON validated against a schema, then saved as a normal editable Plan
built from the library (all categories and measurement types, not only weights).

**Rehab / post-injury mode.** Not a yes/no gate. When the user mentions a surgery, injury or pain, the assistant runs a short
consultation, then adapts the plan to what it learned. The user is treated as an adult who knows their own situation; how cautious
the plan is depends on the whole picture, not on one answer.

**1. Consultation (gather as much as is useful, conversationally, a few questions at a time):**
- what happened: type of surgery or injury, which side, date;
- where they are in recovery: still in formal rehab, finished it, returning to the gym on their own;
- professional involvement: are they seeing (or did they see) an orthopaedic surgeon / physiotherapist, how recently,
  and **what exactly they were told** – focus areas, exercises they were given, movements or ranges to avoid, load limits, next check-up;
- current state: pain at rest / during / after training (0–10), trend (better, same, worse), swelling, stiffness, range of motion, confidence;
- what they can already do comfortably, and their goal (back to sport, strength, everyday function).
The answers are saved as the user's rehab profile and shown back as a short summary the user can correct before the plan is built.

**2. How the plan adapts (a sliding scale, not fixed categories):**
- **Clear professional guidance, recent or older** (e.g. "7 months after surgery, physio 2 months ago told me to focus on X and Y")
  → the plan is built around that guidance: the physio's exercises are included as given, and the assistant adds complementary,
  low-risk work that fits it. No push to go back to the physio; a light "mention it at your next visit" only where something is new.
- **Early phase with a physio involved but only partial guidance** → the physio's exercises plus unaffected areas; for the affected
  area only very conservative additions (isometric holds, unloaded range of motion, balance), each marked "check with your physio",
  and the assistant suggests confirming them at the next appointment.
- **Early phase with no orthopaedic surgeon or physiotherapist involved** → the assistant clearly recommends that this stage is
  supervised by an orthopaedic surgeon and a physiotherapist and explains why. It trains unaffected areas and keeps the affected
  area to what the user reports doing comfortably in daily life, until they have guidance. As soon as the user shares guidance,
  the plan moves up the scale.
- The supervision recommendation fades as recovery progresses: it is prominent in the early phase, becomes an occasional reminder
  later, and disappears once the user reports being back to normal training.
- **Red flags at any point** (new or increasing swelling, numbness or tingling, instability / giving way, night pain, fever, pain that
  keeps getting worse) → pause progression for that area and recommend getting it checked soon. Repeated whenever they are reported.

**3. Safety built into every rehab plan:**
- **Start at the lower bound:** smallest range of motion, lowest load or bodyweight, shortest hold, fewest sets;
  isometrics, unloaded mobility and balance/motor control before loaded movements.
- **No max calibration for rehab areas:** for exercises that load an area covered by rehab mode, the Stage 1.6 calibration
  (test hold, set to technical max, test sets towards RIR ≤ 2) is switched off; they start at the lower bound above instead.
- **Progress only after the user confirms:** after a session, a quick check-in per affected area – pain during / next day:
  none – mild – worse than before. "Fine" unlocks a small step (range, load, hold time or volume), one variable at a time;
  "worse" steps back a level and suggests rest. Never automatic by date. Check-ins are stored so the user and their physio can review them.
- Every rehab exercise shows "stop if pain increases". The assistant never diagnoses and never presents a plan as a medical protocol;
  a short disclaimer is shown once when rehab mode starts.

**AI coach (later)**: a weekly review of the user's logged data (consistency, volume per muscle, PRs, plateaus) with suggestions.

Cost control as before: key in an environment variable, per-user daily limit, token usage logged.

### Stage 3 – Schedule

Tasks and recurring reminders (gym days, deadlines) on one calendar with planned workouts and activities.

### Before opening the app to other people (GDPR/RODO)

Body weight, measurements, injuries and surgeries are health data. Before public sign-ups: privacy policy, explicit consent for health data,
"export my data" (CSV/JSON) and "delete my account and data", and no health data in logs or AI prompts beyond what the feature needs.
To do:
- Own domain (name to be decided), authenticated in Brevo (SPF, DKIM, DMARC), sender noreply@<domain>, the domain
  connected to Render, then `ACCOUNT_EMAIL_VERIFICATION=mandatory`. Reason: emails from a Gmail address sent through
  Brevo score 5.6/10 on mail-tester and WP.pl rejects them as spam.
- A cron-job.org task that opens the app every 10 minutes, so Render's free plan doesn't put it to sleep (the first
  visit after sleeping takes about a minute).

### Later ideas

Share a plan or workout with friends by link, friends and following, Strava import (official API, Standard Tier up to 10 users),
nutrition via Apple Health (parked), partner rewards using the points ledger.

## Technical decisions

- **Django 5.2+**, Python 3.12+, PostgreSQL in production, SQLite locally.
- **Server-rendered templates + HTMX** for interactivity (adding sets without page reloads). No SPA framework.
- Styling: one small hand-written CSS file with CSS variables, dark mode, large tap targets. No CSS framework.
- Languages: standard Django i18n. Source texts are English (msgid); Polish lives in
  `locale/pl/LC_MESSAGES/django.po`, and the compiled `django.mo` is committed (Render's build has no gettext).
  `LANGUAGE_CODE = "en"`; the `.po` uses Django's Polish plural formula (4 forms; the 4th, for fractions, repeats
  "5 serii"). JS gets its texts from `data-text-*` attributes (no JavaScriptCatalog).
- Numbers: visible text uses the page language's decimal separator (`display_kg`: "62,5" in Polish); input
  values, `data-*`, URLs and JS always use a dot (`format_kg`). Text inputs with `inputmode`, and `WeightField`
  accepts a typed comma.
- Charts: Chart.js from a CDN with a pinned version.
- Settings from environment variables (`DJANGO_SECRET_KEY`, `DATABASE_URL`, `ANTHROPIC_API_KEY`, `DEBUG`).
- Email: django-anymail with **Brevo's HTTP API** (`BREVO_API_KEY`, `DEFAULT_FROM_EMAIL` = a sender verified in Brevo), because Render's
  free plan blocks SMTP ports; without the key emails go to the console (local development). Rate limits use the database cache
  (`createcachetable` in `build.sh`), shared by all gunicorn workers.
- Tests with **pytest + pytest-django**; GitHub Actions runs tests and `ruff` on every push.
- Deploy: Render free web service (`render.yaml`, `build.sh` runs migrate, createcachetable, collectstatic, seed_exercises, import_free_exercise_db, seed_smith_variants, group_movements and merge_exercises, and fails if `data_fingerprint --compare` finds unexpected changes to users, users' own exercises, workouts, sets or plans; gunicorn + WhiteNoise) with a Neon Postgres database (`DATABASE_URL`). CI runs the tests on Postgres.

## Data model (Stages 1–1.6)

```
Exercise(name, aliases, muscle_group, equipment, is_bodyweight, progression_step_kg,
         measurement: weight_reps | reps | time | distance_time, category, is_unilateral,
         movement: Movement | null,     # family of variants: same movement, other equipment
         owner: User | null)   # null = built-in; search_text = normalised name + aliases
         # + free-exercise-db data: source_id, source_name, source_category, muscles, level, …
Movement(name, owner: User | null)   # null = built-in family
UserSettings(user 1:1, effort_scale: simple | rir | rpe, ios_shortcut_enabled, ios_shortcut_name,
             keep_screen_on, rest_end_sound, language: pl | en | "" = not chosen)
Plan(owner, name, is_active, created_at)
PlanDay(plan, name, order)
PlanExercise(day, exercise, order, target_sets, rep_min, rep_max, hold_min_s, hold_max_s,
             target_distance_m, rest_seconds)
Workout(owner, plan_day | null, started_at, finished_at | null, note)
WorkoutSwap(workout, plan_exercise, exercise)   # "only today": another variant this workout
WorkoutSet(workout, exercise, order, weight_kg, reps | null, duration_seconds | null,
           distance_m | null, side: left | right | "", rir | null, is_warmup)
Feedback(user | null, kind: bug | suggestion | opinion, message, page, device, user_agent,
         status: new | in_progress | done, created_at)
```
"Last time" for an exercise = the sets of that exercise from the user's most recent finished workout that contains it.

## Conventions

- Apps: `accounts`, `exercises`, `plans`, `workouts`, `feedback` (Stage 2 adds `planner`).
- Every view that touches user data filters by `request.user`; write a test for this for each model.
- Business logic (progression hint, 1RM, "last time" query) lives in plain functions in `services.py`, tested without views.
- Times stored in UTC, shown in Europe/Warsaw.
- Every new text people see goes through gettext (`{% translate %}` / `{% blocktranslate %}`, `gettext`,
  `gettext_lazy` for module-level texts and labels, `ngettext` / `blocktranslate count` for plurals; never format a
  lazy text at import) → `makemessages -l pl --ignore=.venv --ignore=staticfiles` → translate (short, natural gym
  Polish: seria, powtórzenia, ciężar, przerwa, trening, ćwiczenie, rekord; RIR and RPE untranslated) →
  `compilemessages --ignore=.venv` → commit both `.po` and `.mo`. `config/test_translations.py` fails on empty or
  fuzzy entries, lost placeholders or a stale `.mo`. Tests run in English (conftest); tests of Polish texts ask for
  Polish (cookie or `translation.override`).
- Commit messages in English, imperative mood.
