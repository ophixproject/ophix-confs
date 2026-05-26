# ophix-confs

Configuration snippets domain plugin for [ophix-server-base](https://github.com/ophixproject/ophix-server-base).

Stores named configuration snippets in a variety of formats (YAML, JSON, XML, INI,
TOML, .env, raw) and distributes them verbatim to authorised fleet clients over HTTPS
with token + IP authentication.

---

## Installation

```bash
pip install ophix-confs
```

Recommended extras:

```bash
pip install ophix-confs ophix-docs venv-cmds
```

- `ophix-docs` — inline documentation in the admin UI
- `venv-cmds` — lists available venv commands and checks for package updates
- A theme pack (e.g. `ophix-theme-example`) can be added for custom branding; the built-in Ophix theme is active on fresh installs by default

See [Guided installation](#guided-installation) below.

---

## Guided installation

The recommended deployment path uses the three-step guided installer. Substitute
`confserver` with your preferred slug throughout.

### Step 1 — configure

```bash
ophix-manage configure_install confserver
```

Interactive wizard. Prompts for install directory, hostname, TLS certificate paths,
database connection, superuser credentials, and admin theme.

### Step 2 — install

```bash
ophix-manage run_install confserver
```

Creates the directory structure, copies TLS files, generates nginx and systemd configs,
runs `migrate` and `collectstatic`, creates the superuser, and activates the theme.

### Step 3 — system integration (as root)

```bash
sudo bash confserver_sudo_install.sh
```

Sets file ownership, installs the nginx config and systemd service, and starts the server.

For full details see the [ophix-server-base README](https://github.com/ophixproject/ophix-server-base).

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
ophix-manage generate_deploy_config --append
```

---

## What this plugin provides

- `ConfigFormat` model — supported formats with validator and CodeMirror mode metadata
- `Configuration` model — named config snippet with format, content, and `enabled` flag
- `ClientConfiguration` join model — per-client permissions
  (`enabled`, `can_update`, `can_delete`, `can_share`)
- Format validation on ingestion — syntax is checked before storing
- `GET/POST/PUT/DELETE /api/configs/<n>/` API endpoints
- Raw content returned with the correct `Content-Type` header
- CodeMirror syntax highlighting in the Django admin (requires `ophix-codemirror`)
- Django admin with inline `ClientConfiguration` management and linked-artifact columns
- Access audit logging via `ophix.core.audit`
- Built-in documentation (loaded by `ophix_docs_update` if `ophix-docs` is installed)

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
ophix-manage ophix_docs_update --include-app-docs ophix.core,ophix_confs,ophix_docs,ophix_theme_tools
```

See [ophix-docs](https://github.com/ophixproject/ophix-docs) for the full list of
documentation management commands.

---

## Themes

Install a theme alongside this plugin to customise the admin interface appearance.
See [ophix-theme-tools](https://github.com/ophixproject/ophix-theme-tools) for
available themes and installation instructions.
