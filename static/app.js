const $ = (id) => document.getElementById(id);

// paging state for the Load more button below
let page = 1;
let shown = 0;
let activeTag = "";

async function api(url, options) {
  const r = await fetch(url, options);
  if (!r.ok) throw new Error((await r.json().catch(() => ({}))).error || r.statusText);
  return r.status === 204 ? null : r.json();
}

function formatDate(ts) {
  // updated_at is stored as unix seconds
  return new Date(ts * 1000).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

async function loadNotes(reset = true) {
  // the list only ever showed the first 20 notes — page through the API
  // instead so older notes are reachable without touching the URL
  if (reset) { page = 1; shown = 0; $("notes").replaceChildren(); }
  const params = new URLSearchParams();
  if ($("q").value.trim()) params.set("q", $("q").value.trim());
  if (activeTag) params.set("tag", activeTag);
  params.set("sort", $("sort").value);
  params.set("page", page);
  try {
    const data = await api("/notes?" + params);
    render(data.notes, !reset);
    shown += data.notes.length;
    $("count").textContent = data.total ? `Showing ${shown} of ${data.total} notes` : "";
    $("load-more").hidden = shown >= data.total;
    $("status").textContent = "";
  } catch (e) {
    $("status").textContent = e.message;
  }
}

async function loadTags() {
  try {
    const data = await api("/tags");
    renderTags(data.tags);
  } catch (e) {
    $("status").textContent = e.message;
  }
}

function renderTags(tags) {
  const list = $("tag-list");
  list.replaceChildren();
  if (!tags.length) {
    const span = document.createElement("span");
    span.className = "tag-none";
    span.textContent = "No tags yet.";
    list.append(span);
    return;
  }
  for (const t of tags) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "tag" + (t.name === activeTag ? " active" : "");
    btn.textContent = t.name + " ";
    const count = document.createElement("span");
    count.className = "count";
    count.textContent = t.count;
    btn.append(count);
    btn.onclick = () => {
      activeTag = t.name === activeTag ? "" : t.name;
      $("tag").value = activeTag;
      $("clear-filter").hidden = !activeTag;
      loadTags();
      loadNotes();
    };
    list.append(btn);
  }
}

function render(notes, append) {
  const list = $("notes");
  if (!append) list.replaceChildren();
  if (!notes.length && !append) {
    const li = document.createElement("li");
    li.className = "empty";
    li.textContent = "No notes yet. Add one above, or try a different search.";
    list.append(li);
    return;
  }
  for (const n of notes) {
    list.append(noteCard(n));
  }
}

function tagChip(name) {
  const span = document.createElement("button");
  span.type = "button";
  span.className = "tag";
  span.textContent = name;
  span.onclick = () => {
    activeTag = name;
    $("tag").value = name;
    $("clear-filter").hidden = false;
    loadTags();
    loadNotes();
  };
  return span;
}

function noteCard(n) {
  // build with textContent so note text is never parsed as HTML
  const li = document.createElement("li");
  li.className = "note-card";
  li.dataset.id = n.id;

  const title = document.createElement("h3");
  title.textContent = n.title;

  const date = document.createElement("span");
  date.className = "date";
  date.textContent = "Updated " + formatDate(n.updated_at);

  const body = document.createElement("p");
  body.className = "body clamped";
  body.textContent = n.body;

  li.append(title, date, body);

  // long bodies get a Show more toggle instead of filling the card
  if (n.body.length > 280) {
    const more = document.createElement("button");
    more.type = "button";
    more.className = "more-btn";
    more.textContent = "Show more";
    more.onclick = () => {
      const expanded = body.classList.toggle("clamped");
      more.textContent = expanded ? "Show more" : "Show less";
    };
    li.append(more);
  }

  const tags = document.createElement("div");
  tags.className = "tags";
  for (const t of n.tags) tags.append(tagChip(t));
  li.append(tags);

  const footer = document.createElement("footer");
  const edit = document.createElement("button");
  edit.type = "button";
  edit.className = "btn btn-ghost btn-sm";
  edit.textContent = "Edit";
  edit.onclick = () => startEdit(li, n);
  const del = document.createElement("button");
  del.type = "button";
  del.className = "btn btn-danger btn-sm";
  del.textContent = "Delete";
  del.onclick = () => deleteNote(n.id);
  footer.append(edit, del);
  li.append(footer);

  return li;
}

function startEdit(li, n) {
  // swap the card for an inline form prefilled with the note
  const form = document.createElement("form");
  form.className = "edit-form";

  const titleInput = document.createElement("input");
  titleInput.value = n.title;
  titleInput.required = true;
  titleInput.maxLength = 200;
  titleInput.setAttribute("aria-label", "Title");

  const bodyInput = document.createElement("textarea");
  bodyInput.value = n.body;
  bodyInput.maxLength = 10000;
  bodyInput.setAttribute("aria-label", "Body");

  const tagsInput = document.createElement("input");
  tagsInput.value = n.tags.join(", ");
  tagsInput.setAttribute("aria-label", "Tags, comma separated");
  tagsInput.placeholder = "Tags, comma separated";

  const actions = document.createElement("div");
  actions.className = "actions";
  const save = document.createElement("button");
  save.type = "submit";
  save.className = "btn btn-primary btn-sm";
  save.textContent = "Save";
  const cancel = document.createElement("button");
  cancel.type = "button";
  cancel.className = "btn btn-ghost btn-sm";
  cancel.textContent = "Cancel";
  cancel.onclick = () => loadNotes();
  actions.append(save, cancel);

  form.append(titleInput, bodyInput, tagsInput, actions);
  form.onsubmit = async (e) => {
    e.preventDefault();
    const tags = tagsInput.value.split(",").map((t) => t.trim()).filter(Boolean);
    try {
      await api("/notes/" + n.id, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: titleInput.value, body: bodyInput.value, tags }),
      });
      loadTags();
      loadNotes();
    } catch (err) {
      $("status").textContent = err.message;
    }
  };

  li.replaceChildren(form);
  titleInput.focus();
}

async function deleteNote(id) {
  if (!window.confirm("Delete this note?")) return;
  try {
    await api("/notes/" + id, { method: "DELETE" });
    loadTags();
    loadNotes();
  } catch (e) {
    $("status").textContent = e.message;
  }
}

$("filters").onsubmit = (e) => { e.preventDefault(); loadNotes(); };

$("sort").onchange = () => loadNotes();

$("clear-filter").onclick = () => {
  activeTag = "";
  $("tag").value = "";
  $("clear-filter").hidden = true;
  loadTags();
  loadNotes();
};

$("load-more").onclick = () => { page += 1; loadNotes(false); };

$("add").onsubmit = async (e) => {
  e.preventDefault();
  const tags = $("tags").value.split(",").map((t) => t.trim()).filter(Boolean);
  try {
    await api("/notes", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title: $("title").value, body: $("body").value, tags }),
    });
    e.target.reset();
    loadTags();
    loadNotes();
  } catch (err) {
    $("status").textContent = err.message;
  }
};

loadTags();
loadNotes();
