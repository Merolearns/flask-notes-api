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

## Web UI

There's a designed web UI at `/` for using the notes app without curl: a
sidebar with search and a clickable tag list (with counts), a composer card
for new notes, and the notes themselves as a card grid — each card shows the
title, last-updated date, body, and tag chips, with inline editing (click
Edit, change the note, Save) and delete with confirmation. Long bodies are
clamped to a few lines with a Show more toggle, and older notes are reachable
through a Load more button that pages through the API. Clicking a tag chip
filters the grid to that tag. It talks to the same JSON endpoints above, so
anything you do in the UI is visible through the API and vice versa.

```bash
python app.py
```

Then open http://127.0.0.1:5000/.

With the five sample notes from `seed.py`, the first thing you see is the
sidebar listing the tags — personal (2), todo (2), study (2), reading (1),
sql (1), projects (1), career (1) — and a grid of five cards, newest first
("Interview prep notes" at the top). Searching "sql" narrows it to the one
note about window functions; clicking the `study` tag shows the two study
notes.

## Try it

```bash
# list notes (paginated)
curl http://127.0.0.1:5000/notes

# sort by title, or by creation date instead of last-updated (the default)
curl "http://127.0.0.1:5000/notes?sort=title"
curl "http://127.0.0.1:5000/notes?sort=created"

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

The suite covers the full CRUD cycle, search, tag filtering, sorting, pagination, 404s, and validation errors, all against throwaway temp databases.

## What I'd add next

- A due-date field and `?due=` filter — the obvious missing feature for a notes app
- Basic auth or an API key, since anyone can currently write to the database
