"""Web UI tests: the page renders and the API calls it relies on work."""

from test_api import client, create  # noqa: F401  (client is a fixture)


def test_index_renders(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "Notes" in r.get_data(as_text=True)


def test_index_has_fetch_and_form_fields(client):
    html = client.get("/").get_data(as_text=True)
    assert "fetch(" in html and '"/notes' in html
    for field in ('id="q"', 'id="tag"', 'id="title"', 'id="body"', 'id="tags"'):
        assert field in html


def test_index_has_load_more_button(client):
    html = client.get("/").get_data(as_text=True)
    assert 'id="load-more"' in html
    assert 'id="count"' in html
    # the JS pages through /notes instead of only ever showing page 1
    assert 'params.set("page", page)' in html and "loadNotes(false)" in html


def test_load_more_reaches_notes_past_page_one(client):
    for i in range(25):
        create(client, f"Note {i:02d}")
    first = client.get("/notes?page=1").get_json()
    assert first["total"] == 25 and len(first["notes"]) == 20
    second = client.get("/notes?page=2").get_json()
    assert len(second["notes"]) == 5
    # newest first, so page 2 starts at Note 04
    assert second["notes"][0]["title"] == "Note 04"


def test_page_api_lists_created_note(client):
    create(client, "From the UI", "body text", ["ui"])
    notes = client.get("/notes").get_json()["notes"]
    assert [n["title"] for n in notes] == ["From the UI"]
