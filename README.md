# ophix-confs

**One place to define a config snippet once — YAML, JSON, XML, INI, TOML, .env, or raw — instead of copy-pasting it across every host that needs it.**

If your server configs have drifted apart because each host's copy got hand-edited independently, with no single source of truth for what's actually deployed where, `ophix-confs` gives you one place to define each snippet and let clients pull their own copy on demand over HTTPS. Content is validated against its declared format before it's ever stored, so a broken YAML file or malformed INI can't make it into the fleet in the first place.

Access is granted per client, per configuration, and any grant can be revoked instantly without touching the configuration itself.

---

## Installation

See [installation.md](installation.md) for the full step-by-step guide — service user, TLS setup, the guided installer, and getting the service running under nginx and systemd.

---

## Routine upgrades

```bash
pip install --upgrade ophix-server-base ophix-confs
ophix-manage migrate
ophix-manage collectstatic --noinput
sudo systemctl restart confserver
```

If the upgrade added new `.env` settings, pull them in first:

```bash
ophix-manage generate_config --append
```

---

## What this plugin provides

- `ConfigFormat` model — supported formats with validator and CodeMirror mode metadata
- `Configuration` model — named config snippet with format, content, and `enabled` flag
- `ClientConfiguration` join model — per-client permissions
  (`enabled`, `can_update`, `can_delete`, `can_share`)
- Format validation on ingestion — syntax is checked before storing
- `GET/POST/PUT/DELETE /api/configs/<name>/` API endpoints
- Raw content returned with the correct `Content-Type` header
- CodeMirror syntax highlighting in the Django admin, switching mode automatically to match
  each Configuration's format
- Django admin with inline `ClientConfiguration` management and linked-artifact columns
- Access audit logging via `ophix.core.audit`
- Built-in documentation (loaded by `update_docs` if `ophix-docs` is installed)

---

## Configuration (`.env`)

| Variable | Default | Purpose |
| --- | --- | --- |
| `ENABLE_ARTIFACT_DELETE` | `False` | Allow clients to delete configurations they own |
| `SHOW_CONFIG_FORMATS_MODEL` | `False` | Show the Configuration Formats model in admin |

---

## Client

Fleet clients use [ophix-conf-client](https://github.com/ophixproject/ophix-conf-client)
to authenticate and fetch configuration snippets.

---

## Documentation

If `ophix-docs` is installed, documentation is loaded automatically during `run_install`.
To load or refresh docs manually after an upgrade:

```bash
ophix-manage update_docs --include-app-docs ophix.core,ophix_confs,ophix_docs
```

See [ophix-docs](https://github.com/ophixproject/ophix-docs) for the full list of
documentation management commands.
