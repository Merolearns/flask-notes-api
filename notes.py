"""Data access layer — every function talks to sqlite3 directly.

Returns plain dicts, raises NotFoundError when an id doesn't exist.
Validation lives in app.py; this module assumes the input is already clean.
"""

from db import get_db, now, row_to_dict


class NotFoundError(Exception):
    pass


def create_note(title, body="", tags=None, path=None):
    """Insert a note and its tags. Returns the note dict with id."""
    tags = tags or []
    conn = get_db(path) if path else get_db()
    ts = now()
    cur = conn.execute(
        "INSERT INTO notes (title, body, created_at, updated_at) VALUES (?, ?, ?, ?)",
        (title, body, ts, ts),
    )
    note_id = cur.lastrowid
    _set_tags(conn, note_id, tags)
    conn.commit()
    note = get_note(note_id, path, _conn=conn)
    conn.close()
    return note


def get_note(note_id, path=None, _conn=None):
    conn = _conn or (get_db(path) if path else get_db())
    row = conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
    if row is None:
        if _conn is None:
            conn.close()
        raise NotFoundError(f"note {note_id} not found")
    note = row_to_dict(row)
    note["tags"] = _tags_for_note(conn, note_id)
    if _conn is None:
        conn.close()
    return note


def list_notes(q=None, tag=None, page=1, per_page=20, path=None):
    """Paginated note list with optional search and tag filter."""
    conn = get_db(path) if path else get_db()
    clauses, params = [], []

    if tag:
        clauses.append(
            "n.id IN (SELECT note_id FROM note_tags nt JOIN tags t ON t.id = nt.tag_id WHERE t.name = ?)"
        )
        params.append(tag)

    if q:
        clauses.append("(n.title LIKE ? OR n.body LIKE ?)")
        like = f"%{q}%"
        params += [like, like]

    where = "WHERE " + " AND ".join(clauses) if clauses else ""
    total = conn.execute(f"SELECT COUNT(*) FROM notes n {where}", params).fetchone()[0]

    offset = (page - 1) * per_page
    rows = conn.execute(
        f"SELECT n.* FROM notes n {where} ORDER BY n.updated_at DESC LIMIT ? OFFSET ?",
        params + [per_page, offset],
    ).fetchall()

    notes = []
    for row in rows:
        note = row_to_dict(row)
        note["tags"] = _tags_for_note(conn, note["id"])
        notes.append(note)

    conn.close()
    return {"notes": notes, "page": page, "per_page": per_page, "total": total}


def update_note(note_id, title=None, body=None, tags=None, path=None):
    """Partial update — only the fields passed get touched."""
    conn = get_db(path) if path else get_db()
    row = conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
    if row is None:
        conn.close()
        raise NotFoundError(f"note {note_id} not found")

    fields, params = [], []
    if title is not None:
        fields.append("title = ?")
        params.append(title)
    if body is not None:
        fields.append("body = ?")
        params.append(body)
    if fields:
        fields.append("updated_at = ?")
        params.append(now())
        conn.execute(f"UPDATE notes SET {', '.join(fields)} WHERE id = ?", params + [note_id])

    if tags is not None:
        conn.execute("DELETE FROM note_tags WHERE note_id = ?", (note_id,))
        _set_tags(conn, note_id, tags)
        conn.execute("UPDATE notes SET updated_at = ? WHERE id = ?", (now(), note_id))

    conn.commit()
    note = get_note(note_id, path, _conn=conn)
    conn.close()
    return note


def delete_note(note_id, path=None):
    conn = get_db(path) if path else get_db()
    cur = conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    conn.commit()
    conn.close()
    if cur.rowcount == 0:
        raise NotFoundError(f"note {note_id} not found")


def list_tags(path=None):
    """All tag names currently in use, with counts. Ordered by count desc."""
    conn = get_db(path) if path else get_db()
    rows = conn.execute(
        """
        SELECT t.name, COUNT(nt.note_id) AS count
        FROM tags t
        JOIN note_tags nt ON nt.tag_id = t.id
        GROUP BY t.id
        ORDER BY count DESC, t.name
        """
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def _set_tags(conn, note_id, tags):
    for name in tags:
        name = name.strip().lower()
        if not name:
            continue
        conn.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (name,))
        tag_id = conn.execute("SELECT id FROM tags WHERE name = ?", (name,)).fetchone()["id"]
        conn.execute(
            "INSERT OR IGNORE INTO note_tags (note_id, tag_id) VALUES (?, ?)",
            (note_id, tag_id),
        )


def _tags_for_note(conn, note_id):
    rows = conn.execute(
        "SELECT t.name FROM tags t JOIN note_tags nt ON nt.tag_id = t.id "
        "WHERE nt.note_id = ? ORDER BY t.name",
        (note_id,),
    ).fetchall()
    return [r["name"] for r in rows]
