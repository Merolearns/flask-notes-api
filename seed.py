"""Seed the database with a handful of sample notes."""

from db import DB_PATH, init_db
from notes import create_note

SAMPLES = [
    {
        "title": "Grocery list",
        "body": "Eggs, sourdough, coffee beans, olive oil. Check the pantry for rice first.",
        "tags": ["personal", "todo"],
    },
    {
        "title": "Books to read",
        "body": "1. Designing Data-Intensive Applications\n2. A Philosophy of Software Design\n3. The Pragmatic Programmer (re-read)",
        "tags": ["reading", "personal"],
    },
    {
        "title": "SQL window functions",
        "body": "ROW_NUMBER vs RANK vs DENSE_RANK — finally clicked. Write a post with the running-total example.",
        "tags": ["study", "sql"],
    },
    {
        "title": "Weekend project ideas",
        "body": "- Finish the notes API (this one)\n- Try out htmx on a small page\n- Clean up the dotfiles",
        "tags": ["projects", "todo"],
    },
    {
        "title": "Interview prep notes",
        "body": "Two pointers, sliding window, hash maps. Practice explaining time complexity out loud.",
        "tags": ["study", "career"],
    },
]


def main():
    init_db(DB_PATH)
    for sample in SAMPLES:
        note = create_note(sample["title"], sample["body"], sample["tags"])
        print(f"seeded note {note['id']}: {note['title']}")


if __name__ == "__main__":
    main()
