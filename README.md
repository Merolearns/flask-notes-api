# flask-notes-api

A small JSON REST API for notes with tags, built with Flask and SQLite. This is a personal learning project — I wanted to get comfortable writing SQL by hand (no ORM) and wiring up a clean little REST interface.

## What it does

Notes have a title, body, a list of tags, and created/updated timestamps. The API supports:

- `POST /notes` — create a note
- `GET /notes` — list notes, with `?q=` search, `?tag=` filter, and `?page=` / `?per_page=` pagination
- `GET /notes/<id>` — get one note
- `PUT /notes/<id>` — partial update
- `DELETE /notes/<id>` — delete (204)
- `GET /tags` — all tags with usage counts

Errors come back as JSON, e.g. `{"error": "title is required"}` with a 400, or 404s for missing notes. Tags are normalized to lowercase. Storage is SQLite through stdlib `sqlite3` — the data layer is deliberately hand-written SQL.

## Run it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python seed.py          # creates notes.db with 5 sample notes
python app.py
```

The API listens on http://127.0.0.1:5000.

## Try it

```bash
# list notes (paginated)
curl http://127.0.0.1:5000/notes

# search + filter
curl "http://127.0.0.1:5000/notes?q=sql&tag=study"

# create
curl -X POST http://127.0.0.1:5000/notes \
  -H 'Content-Type: application/json' \
  -d '{"title": "Read later", "body": "DDIA chapter 5", "tags": ["study", "books"]}'

# update (partial is fine)
curl -X PUT http://127.0.0.1:5000/notes/1 \
  -H 'Content-Type: application/json' \
  -d '{"tags": ["personal", "todo"]}'

# delete
curl -X DELETE http://127.0.0.1:5000/notes/1

# tag overview
curl http://127.0.0.1:5000/tags
```

## Tests

```bash
pytest
```

The suite covers the full CRUD cycle, search, tag filtering, pagination, 404s, and validation errors, all against throwaway temp databases.

## What I'd add next

- A due-date field and `?due=` filter — the obvious missing feature for a notes app
- Sorting options beyond updated-at (the listing is hardcoded right now)
- Basic auth or an API key, since anyone can currently write to the database
- A tiny frontend — probably just server-rendered templates rather than a full SPA
