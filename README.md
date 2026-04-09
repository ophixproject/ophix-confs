# ophix-conf

Configuration snippets domain plugin for **Ophix Project Servers**.

Stores named configuration snippets in a variety of formats (YAML, JSON,
XML, INI, TOML, .env, raw) and distributes them verbatim to authorised
clients with token + IP authentication.

---

## Installation

```bash
pip install ophix-server-base ophix-conf
```

---

## What this plugin provides

- `ConfigFormat` model — supported formats with validator and CodeMirror metadata
- `Configuration` model — named config snippet with format, content, enabled flag
- `ClientConfiguration` join model — per-client permissions
- Format validation on ingestion (syntax checked before storing)
- `GET/POST/PUT/DELETE /api/configs/<n>/` API endpoints
- Raw content returned with correct `Content-Type` header
- CodeMirror syntax highlighting editor in Django admin (vendored assets)
- Django admin with inline `ClientConfiguration` management
- Built-in documentation

---

## Adding CodeMirror assets

CodeMirror JavaScript and CSS files must be downloaded separately and
placed in:

```
src/ophix_conf/static/ophix_conf/codemirror/
```

See `src/ophix_conf/static/ophix_conf/codemirror/README.md` for the
complete list of required files and download URLs.

---

## Adding a new format

1. Download the CodeMirror mode file and place it in `static/ophix_conf/codemirror/mode/`
2. Add a validator class in `ophix_conf/validators/formats.py`
3. Export it from `ophix_conf/validators/__init__.py`
4. Add a data migration for the new `ConfigFormat` row
5. Release a new version — operators run `pip install --upgrade ophix-conf && ophix-manage migrate`

---

## Configuration (`.env`)

No conf-specific settings are required beyond the standard
`ophix-server-base` settings. `ENABLE_ARTIFACT_DELETE` controls
whether clients can delete configurations they own.
