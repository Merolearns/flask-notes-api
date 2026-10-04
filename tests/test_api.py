"""API tests — run with `pytest` from the project root."""

import os
import tempfile

import pytest

from db import init_db
from app import app


@pytest.fixture()
def client():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    # point the data layer at the temp db by monkeypatching get_db's default
    import db as db_module
    import notes as notes_module

    orig_get_db = db_module.get_db
    db_module.get_db = lambda p=path: orig_get_db(p)
    notes_module.get_db = db_module.get_db
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c
    db_module.get_db = orig_get_db
    notes_module.get_db = orig_get_db
    os.unlink(path)


def create(client, title="Test note", body="hello", tags=None):
    payload = {"title": title, "body": body}
    if tags is not None:
        payload["tags"] = tags
    return client.post("/notes", json=payload)


def test_create_and_get_note(client):
    r = create(client, "Shopping", "milk and eggs", ["personal"])
    assert r.status_code == 201
    note = r.get_json()
    assert note["title"] == "Shopping"
    assert note["tags"] == ["personal"]
    assert "created_at" in note and "updated_at" in note

    r = client.get(f"/notes/{note['id']}")
    assert r.status_code == 200
    assert r.get_json()["body"] == "milk and eggs"


def test_update_note(client):
    note = create(client, "Old title").get_json()
    r = client.put(f"/notes/{note['id']}", json={"title": "New title", "tags": ["work"]})
    assert r.status_code == 200
    updated = r.get_json()
    assert updated["title"] == "New title"
    assert updated["tags"] == ["work"]

    # partial update leaves other fields alone
    r = client.put(f"/notes/{note['id']}", json={"body": "just the body"})
    assert r.get_json()["title"] == "New title"
    assert r.get_json()["body"] == "just the body"


def test_delete_note(client):
    note = create(client).get_json()
    r = client.delete(f"/notes/{note['id']}")
    assert r.status_code == 204
    assert client.get(f"/notes/{note['id']}").status_code == 404


def test_get_missing_note_404(client):
    r = client.get("/notes/99999")
    assert r.status_code == 404
    assert "error" in r.get_json()


def test_delete_missing_note_404(client):
    assert client.delete("/notes/99999").status_code == 404


def test_validation_errors(client):
    # missing title
    assert create(client, title="").status_code == 400
    r = client.post("/notes", json={"body": "no title"})
    assert r.status_code == 400
    assert r.get_json()["error"] == "title is required"

    # tags must be a list
    r = client.post("/notes", json={"title": "x", "tags": "notalist"})
    assert r.status_code == 400

    # title too long
    r = client.post("/notes", json={"title": "a" * 201})
    assert r.status_code == 400


def test_search(client):
    create(client, "Python tricks", "generators are neat", ["study"])
    create(client, "Grocery list", "milk", ["personal"])
    r = client.get("/notes?q=python")
    data = r.get_json()
    assert data["total"] == 1
    assert data["notes"][0]["title"] == "Python tricks"


def test_tag_filter(client):
    create(client, "A", tags=["work"])
    create(client, "B", tags=["personal"])
    r = client.get("/notes?tag=work")
    data = r.get_json()
    assert data["total"] == 1
    assert data["notes"][0]["title"] == "A"


def test_pagination(client):
    for i in range(5):
        create(client, f"Note {i}")
    r = client.get("/notes?per_page=2&page=2")
    data = r.get_json()
    assert data["total"] == 5
    assert data["page"] == 2
    assert len(data["notes"]) == 2

    # garbage page params -> 400
    assert client.get("/notes?page=abc").status_code == 400
    assert client.get("/notes?per_page=500").status_code == 400


def test_tags_endpoint(client):
    create(client, "A", tags=["work", "urgent"])
    create(client, "B", tags=["work"])
    r = client.get("/tags")
    tags = {t["name"]: t["count"] for t in r.get_json()["tags"]}
    assert tags == {"work": 2, "urgent": 1}
