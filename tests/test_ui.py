"""Web UI tests: the page renders and the API calls it relies on work."""

from test_api import client, create  # noqa: F401  (client is a fixture)


def test_index_renders(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "Notes" in r.get_data(as_text=True)


def test_index_has_form_fields(client):
    html = client.get("/").get_data(as_text=True)
    for field in ('id="q"', 'id="tag"', 'id="title"', 'id="body"', 'id="tags"'):
        assert field in html


def test_index_links_stylesheet_and_script(client):
    html = client.get("/").get_data(as_text=True)
    assert 'href="/static/style.css"' in html
    assert 'src="/static/app.js"' in html
    assert client.get("/static/style.css").status_code == 200
    assert client.get("/static/app.js").status_code == 200


def test_app_js_calls_notes_api_and_pages(client):
    js = client.get("/static/app.js").get_data(as_text=True)
    assert "fetch(" in js and '"/notes' in js
    # the JS pages through /notes instead of only ever showing page 1
    assert 'params.set("page", page)' in js and "loadNotes(false)" in js
    # tag list and inline edit both talk to the API
    assert '"/tags"' in js and 'method: "PUT"' in js


def test_index_has_load_more_button(client):
    html = client.get("/").get_data(as_text=True)
    assert 'id="load-more"' in html
    assert 'id="count"' in html


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


def test_edit_flow_updates_note(client):
    # the edit form the UI shows saves through PUT /notes/<id>
    note = create(client, "Draft title", "draft body", ["todo"]).get_json()
    r = client.put(
        f"/notes/{note['id']}",
        json={"title": "Edited title", "body": "edited body", "tags": ["done"]},
    )
    assert r.status_code == 200
    updated = client.get(f"/notes/{note['id']}").get_json()
    assert updated["title"] == "Edited title"
    assert updated["body"] == "edited body"
    assert updated["tags"] == ["done"]
