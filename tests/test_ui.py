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


def test_page_api_lists_created_note(client):
    create(client, "From the UI", "body text", ["ui"])
    notes = client.get("/notes").get_json()["notes"]
    assert [n["title"] for n in notes] == ["From the UI"]
