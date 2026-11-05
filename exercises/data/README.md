# free-exercise-db snapshot

`free_exercise_db.json` is `dist/exercises.json` from
https://github.com/yuhonas/free-exercise-db at commit
`f00c92c7dcf1216a928a52c3706c7ce8e2f71ed5` (876 exercises).

License: The Unlicense (public domain). Images are not stored here; they are
served from jsDelivr pinned to the same commit (see `exercises/free_db.py`).

To update: download the file at a newer commit, change `FREE_DB_COMMIT` in
`exercises/free_db.py` to match, run the tests, then `import_free_exercise_db`.
