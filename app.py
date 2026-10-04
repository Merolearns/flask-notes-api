"""Flask routes for the notes API."""

from flask import Flask, jsonify, request

from db import DB_PATH, init_db
from notes import (
    NotFoundError,
    create_note,
    delete_note,
    get_note,
    list_notes,
    list_tags,
    update_note,
)

app = Flask(__name__)

TITLE_MAX = 200
BODY_MAX = 10000
TAG_MAX = 40
PER_PAGE_MAX = 100


@app.errorhandler(NotFoundError)
def handle_not_found(e):
    return jsonify({"error": str(e)}), 404


@app.errorhandler(400)
def handle_bad_request(e):
    # generic fallback, most validation returns its own message below
    return jsonify({"error": "bad request"}), 400


@app.route("/notes", methods=["POST"])
def post_note():
    data = request.get_json(silent=True) or {}
    err = _validate_note(data, partial=False)
    if err:
        return jsonify({"error": err}), 400
    note = create_note(data["title"].strip(), data.get("body", ""), data.get("tags", []))
    return jsonify(note), 201


@app.route("/notes", methods=["GET"])
def get_notes():
    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 20))
    except ValueError:
        return jsonify({"error": "page and per_page must be integers"}), 400
    if page < 1 or per_page < 1 or per_page > PER_PAGE_MAX:
        return jsonify({"error": f"page >= 1 and 1 <= per_page <= {PER_PAGE_MAX}"}), 400

    result = list_notes(
        q=request.args.get("q"),
        tag=request.args.get("tag"),
        page=page,
        per_page=per_page,
    )
    return jsonify(result)


@app.route("/notes/<int:note_id>", methods=["GET"])
def get_one_note(note_id):
    return jsonify(get_note(note_id))


@app.route("/notes/<int:note_id>", methods=["PUT"])
def put_note(note_id):
    data = request.get_json(silent=True) or {}
    err = _validate_note(data, partial=True)
    if err:
        return jsonify({"error": err}), 400
    note = update_note(
        note_id,
        title=data["title"].strip() if "title" in data else None,
        body=data.get("body"),
        tags=data.get("tags"),
    )
    return jsonify(note)


@app.route("/notes/<int:note_id>", methods=["DELETE"])
def delete_one_note(note_id):
    delete_note(note_id)
    return "", 204


@app.route("/tags", methods=["GET"])
def get_tags():
    return jsonify({"tags": list_tags()})


def _validate_note(data, partial):
    """Returns an error string or None."""
    if not partial or "title" in data:
        title = data.get("title")
        if not title or not str(title).strip():
            return "title is required"
        if len(title) > TITLE_MAX:
            return f"title must be at most {TITLE_MAX} characters"
    if "body" in data and data["body"] is not None:
        if len(str(data["body"])) > BODY_MAX:
            return f"body must be at most {BODY_MAX} characters"
    if "tags" in data:
        tags = data["tags"]
        if not isinstance(tags, list):
            return "tags must be a list of strings"
        if any(not isinstance(t, str) or len(t) > TAG_MAX for t in tags):
            return f"each tag must be a string of at most {TAG_MAX} characters"
    return None


if __name__ == "__main__":
    init_db(DB_PATH)
    app.run(debug=True)
